"""Factory de fournisseur LLM pilotée par configuration (issue I3.5, ADR-0005).

Le choix du fournisseur (``fake`` / ``anthropic`` / ``openai``), le modèle,
l'URL de base et la clé API viennent uniquement de `Settings`. Changer de
modèle ou de fournisseur ne touche jamais le code applicatif — seulement la
configuration (variables d'environnement ``AGENTSCOPE_LLM_*``).
"""

from __future__ import annotations

from agentscope.application.mapping.prompt_builder import PromptBuilder
from agentscope.application.ports.llm_provider import LLMProvider
from agentscope.domain import DomainError
from agentscope.infrastructure.config.settings import Settings
from agentscope.infrastructure.llm.anthropic_provider import AnthropicProvider
from agentscope.infrastructure.llm.fake_provider import FakeLLMProvider
from agentscope.infrastructure.llm.openai_provider import OpenAIProvider
from agentscope.infrastructure.profiling.sensitive_filter import DefaultSensitiveFilter

_KNOWN_PROVIDERS = ("fake", "anthropic", "openai")


class LLMProviderConfigError(DomainError):
    """La configuration ne permet pas de construire le fournisseur demandé."""


def create_llm_provider(
    settings: Settings,
    prompt_builder: PromptBuilder | None = None,
) -> LLMProvider:
    """Construit le fournisseur désigné par ``settings.llm_provider``."""
    prompt_builder = prompt_builder or PromptBuilder(sensitive_filter=DefaultSensitiveFilter())
    provider_name = settings.llm_provider.lower()

    if provider_name == "fake":
        return FakeLLMProvider()

    if provider_name == "anthropic":
        model = _require(settings.llm_model, provider_name, "llm_model")
        api_key = _require(settings.llm_api_key, provider_name, "llm_api_key")
        if settings.llm_base_url:
            return AnthropicProvider(
                model=model,
                api_key=api_key,
                prompt_builder=prompt_builder,
                base_url=settings.llm_base_url,
            )
        return AnthropicProvider(model=model, api_key=api_key, prompt_builder=prompt_builder)

    if provider_name == "openai":
        model = _require(settings.llm_model, provider_name, "llm_model")
        if settings.llm_base_url:
            return OpenAIProvider(
                model=model,
                api_key=settings.llm_api_key,
                prompt_builder=prompt_builder,
                base_url=settings.llm_base_url,
            )
        return OpenAIProvider(
            model=model, api_key=settings.llm_api_key, prompt_builder=prompt_builder
        )

    raise LLMProviderConfigError(
        f"Fournisseur LLM inconnu : `{settings.llm_provider}` "
        f"(attendu : {' | '.join(_KNOWN_PROVIDERS)})."
    )


def _require(value: str | None, provider_name: str, field_name: str) -> str:
    if not value:
        raise LLMProviderConfigError(
            f"Fournisseur `{provider_name}` : `{field_name}` manquant dans la configuration."
        )
    return value
