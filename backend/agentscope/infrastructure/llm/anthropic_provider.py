"""Adaptateur Anthropic pour ``LLMProvider`` (issue I3.3).

Appel HTTP brut (``httpx``) à l'API Messages d'Anthropic — pas de SDK officiel
(ADR-0005) : un seul mécanisme de transport, partagé avec l'adaptateur
OpenAI-compatible (I3.4), testable sans réseau via ``httpx.MockTransport``.

Construit le prompt via ``PromptBuilder`` (I3.6, durcissement « traces =
données ») puis convertit la réponse via ``parse_mapping_response_text`` (I3.11).
"""

from __future__ import annotations

from typing import Any

import httpx

from agentscope.application.mapping.prompt_builder import PromptBuilder
from agentscope.application.ports.llm_provider import (
    ChatMessage,
    ChatReply,
    MappingContext,
    MappingProposal,
    TargetSchema,
)
from agentscope.domain import FieldProfileSet, LLMError
from agentscope.infrastructure.llm.response_parsing import (
    RESPONSE_FORMAT_INSTRUCTION,
    parse_mapping_response_text,
)

_ANTHROPIC_VERSION = "2023-06-01"
_RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}


class AnthropicProvider:
    """Fournisseur IA Anthropic (Claude) : propose un mapping, discute dessus."""

    name = "anthropic"

    def __init__(
        self,
        *,
        model: str,
        api_key: str,
        prompt_builder: PromptBuilder,
        base_url: str = "https://api.anthropic.com",
        timeout: float = 30.0,
        max_retries: int = 2,
        max_tokens: int = 4096,
        client: httpx.Client | None = None,
    ) -> None:
        self._model = model
        self._api_key = api_key
        self._prompt_builder = prompt_builder
        self._max_retries = max_retries
        self._max_tokens = max_tokens
        self._client = client or httpx.Client(base_url=base_url, timeout=timeout)

    def propose_mapping(
        self,
        profile: FieldProfileSet,
        sample: list[dict[str, Any]],
        target_schema: TargetSchema,
    ) -> MappingProposal:
        prompt = self._prompt_builder.build(target_schema, profile, sample)
        user_message = f"{prompt.user}\n\n{RESPONSE_FORMAT_INSTRUCTION}"

        text = self._call_messages_api(system=prompt.system, user=user_message)
        return parse_mapping_response_text(text)

    def chat(
        self,
        conversation_id: str,
        messages: list[ChatMessage],
        context: MappingContext,
    ) -> ChatReply:
        # Format exact de `messages`/`context` fixé par I3.8 (non codé) ; en
        # attendant, on suppose des dicts `{"role": ..., "content": ...}`.
        anthropic_messages = (
            [{"role": m["role"], "content": m["content"]} for m in messages] or None
        )
        text = self._call_messages_api(system=None, messages=anthropic_messages)
        return ChatReply(text=text, revised_proposal=None)

    # ------------------------------------------------------------------

    def _call_messages_api(
        self,
        *,
        system: str | None,
        user: str | None = None,
        messages: list[dict[str, str]] | None = None,
    ) -> str:
        body: dict[str, Any] = {
            "model": self._model,
            "max_tokens": self._max_tokens,
            "messages": messages or [{"role": "user", "content": user or ""}],
        }
        if system is not None:
            body["system"] = system

        headers = {
            "x-api-key": self._api_key,
            "anthropic-version": _ANTHROPIC_VERSION,
            "content-type": "application/json",
        }

        last_error: Exception | None = None
        for _ in range(self._max_retries + 1):
            try:
                response = self._client.post("/v1/messages", json=body, headers=headers)
            except httpx.TransportError as exc:
                last_error = exc
                continue

            if response.status_code in _RETRYABLE_STATUS_CODES:
                last_error = LLMError(
                    f"Anthropic a répondu {response.status_code} : {response.text}"
                )
                continue
            if response.status_code >= 400:
                raise LLMError(f"Anthropic a répondu {response.status_code} : {response.text}")

            return self._extract_text(response.json())

        raise LLMError(
            f"Anthropic injoignable après {self._max_retries + 1} tentative(s)."
        ) from last_error

    @staticmethod
    def _extract_text(payload: object) -> str:
        content = payload.get("content") if isinstance(payload, dict) else None
        if not isinstance(content, list) or not content:
            raise LLMError("Réponse Anthropic invalide : `content` manquant ou vide.")

        first = content[0]
        text = first.get("text") if isinstance(first, dict) else None
        if not isinstance(text, str):
            raise LLMError("Réponse Anthropic invalide : bloc `content[0].text` manquant.")
        return text
