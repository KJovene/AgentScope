"""Adaptateur OpenAI-compatible pour ``LLMProvider`` (issue I3.4).

Couvre OpenAI et tout serveur compatible (Ollama, LM Studio) via un simple
changement de ``base_url`` — même code, aucune branche spécifique (ADR-0005).

Appel HTTP brut (``httpx``), même mécanisme de transport/retries que
l'adaptateur Anthropic (I3.3), testable sans réseau via ``httpx.MockTransport``.

Construit le prompt via ``PromptBuilder`` (I3.6) puis convertit la réponse via
``parse_mapping_response_text`` (I3.11).
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

_RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}


class OpenAIProvider:
    """Fournisseur IA OpenAI-compatible : propose un mapping, discute dessus.

    ``base_url`` swappable (ex. ``http://localhost:11434/v1`` pour Ollama,
    un serveur LM Studio, ...) sans changer une ligne de code : seule la
    configuration change (contrat ADR-0005).
    """

    name = "openai"

    def __init__(
        self,
        *,
        model: str,
        api_key: str | None,
        prompt_builder: PromptBuilder,
        base_url: str = "https://api.openai.com/v1",
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

        messages = [
            {"role": "system", "content": prompt.system},
            {"role": "user", "content": user_message},
        ]
        text = self._call_chat_completions_api(messages)
        return parse_mapping_response_text(text)

    def chat(
        self,
        conversation_id: str,
        messages: list[ChatMessage],
        context: MappingContext,
    ) -> ChatReply:
        openai_messages = [{"role": m.role, "content": m.text} for m in messages]
        text = self._call_chat_completions_api(openai_messages or [{"role": "user", "content": ""}])
        return ChatReply(text=text, revised_proposal=None)

    # ------------------------------------------------------------------

    def _call_chat_completions_api(self, messages: list[dict[str, str]]) -> str:
        body: dict[str, Any] = {
            "model": self._model,
            "max_tokens": self._max_tokens,
            "messages": messages,
        }

        headers = {"content-type": "application/json"}
        if self._api_key:
            headers["Authorization"] = f"Bearer {self._api_key}"

        last_error: Exception | None = None
        for _ in range(self._max_retries + 1):
            try:
                response = self._client.post("/chat/completions", json=body, headers=headers)
            except httpx.TransportError as exc:
                last_error = exc
                continue

            if response.status_code in _RETRYABLE_STATUS_CODES:
                last_error = LLMError(
                    f"Le fournisseur a répondu {response.status_code} : {response.text}"
                )
                continue
            if response.status_code >= 400:
                raise LLMError(f"Le fournisseur a répondu {response.status_code} : {response.text}")

            return self._extract_text(response.json())

        raise LLMError(
            f"Fournisseur OpenAI-compatible injoignable après {self._max_retries + 1} tentative(s)."
        ) from last_error

    @staticmethod
    def _extract_text(payload: object) -> str:
        choices = payload.get("choices") if isinstance(payload, dict) else None
        if not isinstance(choices, list) or not choices:
            raise LLMError("Réponse invalide : `choices` manquant ou vide.")

        first = choices[0]
        message = first.get("message") if isinstance(first, dict) else None
        content = message.get("content") if isinstance(message, dict) else None
        if not isinstance(content, str):
            raise LLMError("Réponse invalide : `choices[0].message.content` manquant.")
        return content
