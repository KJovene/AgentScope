"""``MappingWorkbenchAdapter`` (issue I4.3) — analyse + prévisualisation réelles,
sans réseau (fournisseur LLM simulé) ni base de données.
"""

from __future__ import annotations

import json

import pytest

from agentscope.application.ports.llm_provider import (
    ChatMessage,
    ChatReply,
    MappingProposal,
)
from agentscope.application.use_cases.analyze_unknown_file import AnalysisFailedError
from agentscope.domain import DomainError
from agentscope.infrastructure.llm.fake_provider import FakeLLMProvider
from agentscope.infrastructure.profiling.field_profiler import DefaultFieldProfiler
from agentscope.infrastructure.readers.csv_reader import CsvReader
from agentscope.infrastructure.readers.jsonl_reader import JsonlReader
from agentscope.infrastructure.readers.parquet_reader import ParquetReader
from agentscope.infrastructure.services.workbench_service import MappingWorkbenchAdapter

_VALID_DEFINITION = {
    "name": "demo",
    "version": 1,
    "source_format": "jsonl",
    "constants": {"source_name": "Demo"},
    "entities": {
        "session": {
            "iterate": {"path": "", "where": []},
            "identity": {"key_fields": ["session_id"]},
            "fields": {
                "external_id": {"from": "session_id", "transform": "identity"},
                "agent_name": {"from": "agent", "transform": "identity"},
            },
        }
    },
}

SAMPLE = "\n".join(
    json.dumps(r) for r in [{"session_id": "s1", "agent": "claude"}, {"session_id": "s2"}, {}]
).encode("utf-8")


class _ValidStubProvider:
    name = "stub-valid"

    def __init__(self, chat_reply: ChatReply | None = None) -> None:
        self._chat_reply = chat_reply or ChatReply(text="Explication.", revised_proposal=None)

    def propose_mapping(self, profile, sample, target_schema):
        return MappingProposal(
            definition=_VALID_DEFINITION, explanations=[], ambiguities=[], unmapped_fields=[]
        )

    def chat(self, conversation_id, messages, context):
        return self._chat_reply


def _readers():
    return (JsonlReader(), CsvReader(), ParquetReader())


def _adapter(provider) -> MappingWorkbenchAdapter:
    return MappingWorkbenchAdapter(
        readers=_readers(), profiler=DefaultFieldProfiler(), llm_provider=provider
    )


def test_analyze_returns_profile_and_validated_proposal() -> None:
    result = _adapter(_ValidStubProvider()).analyze("unknown.jsonl", SAMPLE)

    assert result.proposal.definition == _VALID_DEFINITION
    assert result.profile.record_count == 3
    assert result.profile.by_path("session_id") is not None


def test_analyze_rejects_a_non_conforming_proposal() -> None:
    # FakeLLMProvider produit un mapping "record" plat, non conforme au schéma cible.
    with pytest.raises(AnalysisFailedError):
        _adapter(FakeLLMProvider()).analyze("unknown.jsonl", SAMPLE)


def test_analyze_unknown_extension_raises_domain_error() -> None:
    with pytest.raises(DomainError):
        _adapter(_ValidStubProvider()).analyze("unknown.txt", SAMPLE)


def test_preview_dry_runs_the_normalizer_on_a_sample() -> None:
    report = _adapter(_ValidStubProvider()).preview(
        "sample.jsonl", SAMPLE, _VALID_DEFINITION, sample_size=10
    )

    assert report.sampled_count == 3
    assert len(report.result.sessions) == 2  # s1 + s2
    assert len(report.result.rejects) == 1  # ligne sans session_id


def test_preview_rejects_an_invalid_mapping_definition() -> None:
    with pytest.raises(DomainError):
        _adapter(_ValidStubProvider()).preview("sample.jsonl", SAMPLE, {"entities": "nope"})


def test_preview_unknown_extension_raises_domain_error() -> None:
    with pytest.raises(DomainError):
        _adapter(_ValidStubProvider()).preview("sample.bin", SAMPLE, _VALID_DEFINITION)


def _proposal(ambiguities: list[str]) -> MappingProposal:
    return MappingProposal(
        definition=_VALID_DEFINITION,
        explanations=[],
        ambiguities=ambiguities,
        unmapped_fields=[],
    )


def test_chat_returns_text_and_keeps_proposal_without_revision() -> None:
    provider = _ValidStubProvider(ChatReply(text="Parce que X.", revised_proposal=None))
    original = _proposal(["`agent` ambigu"])

    result = _adapter(provider).chat(
        "conv-1", [ChatMessage(role="user", text="pourquoi ?")], original
    )

    assert result.text == "Parce que X."
    assert result.revised_proposal is None
    assert result.current_proposal is original
    assert result.ambiguities == ["`agent` ambigu"]


def test_chat_surfaces_a_revised_proposal() -> None:
    revised = _proposal([])
    provider = _ValidStubProvider(ChatReply(text="Je corrige.", revised_proposal=revised))

    result = _adapter(provider).chat(
        "conv-1", [ChatMessage(role="user", text="corrige X")], _proposal(["à revoir"])
    )

    assert result.revised_proposal is revised
    assert result.current_proposal is revised
