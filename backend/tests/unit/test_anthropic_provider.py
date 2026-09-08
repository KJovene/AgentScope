"""Adaptateur Anthropic (issue I3.3) : appel HTTP, retries, conversion de la réponse."""

from __future__ import annotations

import json

import httpx
import pytest

from agentscope.application.mapping.prompt_builder import PromptBuilder
from agentscope.application.mapping.target_schema import TARGET_SCHEMA
from agentscope.application.ports.llm_provider import ChatReply, LLMProvider, MappingProposal
from agentscope.domain import FieldProfile, FieldProfileSet, LLMError
from agentscope.infrastructure.llm.anthropic_provider import AnthropicProvider


class _NoopSensitiveFilter:
    """Ne masque rien : isole les tests du détail du `SensitiveFilter` réel (I2.14)."""

    def scrub(self, value: object) -> object:
        return value


VALID_DEFINITION = {
    "name": "demo",
    "version": 1,
    "source_format": "jsonl",
    "constants": {"source_name": "Demo"},
    "entities": {
        "session": {
            "iterate": {"path": "", "where": []},
            "identity": {"key_fields": ["sid"]},
            "fields": {
                "external_id": {
                    "from": "sid",
                    "transform": "identity",
                    "required": True,
                    "on_error": "reject",
                },
            },
        },
    },
}

VALID_MODEL_RESPONSE = {
    "definition": VALID_DEFINITION,
    "explanations": [
        {
            "target_field": "external_id",
            "source_field": "sid",
            "rationale": "Identifiant de session.",
            "confidence": 0.9,
        }
    ],
    "ambiguities": [],
    "unmapped_fields": [],
}


class _CallRecorder:
    """Handler de `httpx.MockTransport` : rejoue une séquence de réponses/exceptions."""

    def __init__(self, responses: list[httpx.Response | Exception]) -> None:
        self.requests: list[httpx.Request] = []
        self._responses = list(responses)

    def __call__(self, request: httpx.Request) -> httpx.Response:
        self.requests.append(request)
        item = self._responses.pop(0)
        if isinstance(item, Exception):
            raise item
        return item


def _profile() -> FieldProfileSet:
    return FieldProfileSet(
        record_count=1,
        fields=(
            FieldProfile(
                path="sid", inferred_type="string", null_ratio=0.0, distinct_count=1,
                sample_values=("s1",),
            ),
        ),
    )


def _anthropic_text_response(text: str, status_code: int = 200) -> httpx.Response:
    return httpx.Response(status_code, json={"content": [{"type": "text", "text": text}]})


def _make_provider(recorder: _CallRecorder, **overrides: object) -> AnthropicProvider:
    client = httpx.Client(
        transport=httpx.MockTransport(recorder), base_url="https://api.anthropic.com"
    )
    kwargs: dict[str, object] = {
        "model": "claude-test",
        "api_key": "sk-ant-test",
        "prompt_builder": PromptBuilder(sensitive_filter=_NoopSensitiveFilter()),
        "client": client,
        "max_retries": 2,
    }
    kwargs.update(overrides)
    return AnthropicProvider(**kwargs)  # type: ignore[arg-type]


def test_provider_satisfies_llm_provider_protocol() -> None:
    provider = _make_provider(_CallRecorder([]))

    assert isinstance(provider, LLMProvider)
    assert provider.name == "anthropic"


def test_propose_mapping_returns_a_validated_proposal() -> None:
    recorder = _CallRecorder([_anthropic_text_response(json.dumps(VALID_MODEL_RESPONSE))])
    provider = _make_provider(recorder)

    proposal = provider.propose_mapping(
        profile=_profile(), sample=[{"sid": "s1"}], target_schema=TARGET_SCHEMA
    )

    assert isinstance(proposal, MappingProposal)
    assert proposal.definition == VALID_DEFINITION
    assert len(recorder.requests) == 1

    request = recorder.requests[0]
    assert request.headers["x-api-key"] == "sk-ant-test"
    assert request.headers["anthropic-version"]
    body = json.loads(request.content)
    assert body["model"] == "claude-test"
    assert "system" in body


def test_propose_mapping_accepts_a_markdown_fenced_response() -> None:
    fenced = f"```json\n{json.dumps(VALID_MODEL_RESPONSE)}\n```"
    recorder = _CallRecorder([_anthropic_text_response(fenced)])
    provider = _make_provider(recorder)

    proposal = provider.propose_mapping(profile=_profile(), sample=[], target_schema=TARGET_SCHEMA)

    assert proposal.definition == VALID_DEFINITION


def test_propose_mapping_with_malformed_json_raises_llm_error() -> None:
    recorder = _CallRecorder([_anthropic_text_response("not json")])
    provider = _make_provider(recorder)

    with pytest.raises(LLMError, match="JSON illisible"):
        provider.propose_mapping(profile=_profile(), sample=[], target_schema=TARGET_SCHEMA)


def test_retries_on_429_then_succeeds() -> None:
    recorder = _CallRecorder(
        [
            httpx.Response(429, text="rate limited"),
            _anthropic_text_response(json.dumps(VALID_MODEL_RESPONSE)),
        ]
    )
    provider = _make_provider(recorder, max_retries=2)

    proposal = provider.propose_mapping(profile=_profile(), sample=[], target_schema=TARGET_SCHEMA)

    assert proposal.definition == VALID_DEFINITION
    assert len(recorder.requests) == 2


def test_exhausted_retries_on_persistent_5xx_raises_llm_error() -> None:
    recorder = _CallRecorder([httpx.Response(500, text="boom")] * 2)
    provider = _make_provider(recorder, max_retries=1)

    with pytest.raises(LLMError, match="injoignable"):
        provider.propose_mapping(profile=_profile(), sample=[], target_schema=TARGET_SCHEMA)
    assert len(recorder.requests) == 2


def test_timeout_is_retried_then_raises_llm_error() -> None:
    timeout = httpx.TimeoutException("timed out")
    recorder = _CallRecorder([timeout, timeout])
    provider = _make_provider(recorder, max_retries=1)

    with pytest.raises(LLMError, match="injoignable"):
        provider.propose_mapping(profile=_profile(), sample=[], target_schema=TARGET_SCHEMA)
    assert len(recorder.requests) == 2


def test_non_retryable_4xx_raises_immediately() -> None:
    recorder = _CallRecorder([httpx.Response(401, text="unauthorized")])
    provider = _make_provider(recorder, max_retries=2)

    with pytest.raises(LLMError, match="401"):
        provider.propose_mapping(profile=_profile(), sample=[], target_schema=TARGET_SCHEMA)
    assert len(recorder.requests) == 1  # pas de retry sur une erreur non transitoire


def test_chat_returns_the_model_text_without_a_revised_proposal() -> None:
    recorder = _CallRecorder([_anthropic_text_response("Voici pourquoi j'ai choisi ce mapping.")])
    provider = _make_provider(recorder)

    reply = provider.chat(
        conversation_id="conv-1",
        messages=[{"role": "user", "content": "Pourquoi ce mapping ?"}],
        context=None,
    )

    assert isinstance(reply, ChatReply)
    assert reply.text == "Voici pourquoi j'ai choisi ce mapping."
    assert reply.revised_proposal is None


def test_response_without_content_raises_llm_error() -> None:
    recorder = _CallRecorder([httpx.Response(200, json={})])
    provider = _make_provider(recorder)

    with pytest.raises(LLMError, match="content"):
        provider.propose_mapping(profile=_profile(), sample=[], target_schema=TARGET_SCHEMA)


def test_response_with_content_missing_text_raises_llm_error() -> None:
    recorder = _CallRecorder([httpx.Response(200, json={"content": [{"type": "text"}]})])
    provider = _make_provider(recorder)

    with pytest.raises(LLMError, match="content\\[0\\].text"):
        provider.propose_mapping(profile=_profile(), sample=[], target_schema=TARGET_SCHEMA)
