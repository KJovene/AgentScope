"""Vérifie la factory de fournisseur LLM pilotée par configuration (I3.5)."""

import pytest

from agentscope.infrastructure.config.settings import Settings
from agentscope.infrastructure.llm.anthropic_provider import AnthropicProvider
from agentscope.infrastructure.llm.factory import LLMProviderConfigError, create_llm_provider
from agentscope.infrastructure.llm.fake_provider import FakeLLMProvider
from agentscope.infrastructure.llm.openai_provider import OpenAIProvider


def _settings(**overrides: object) -> Settings:
    defaults: dict[str, object] = {"llm_provider": "fake"}
    defaults.update(overrides)
    return Settings(**defaults)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    ("llm_provider", "extra", "expected_type"),
    [
        ("fake", {}, FakeLLMProvider),
        ("anthropic", {"llm_model": "claude-x", "llm_api_key": "sk-test"}, AnthropicProvider),
        ("openai", {"llm_model": "gpt-x"}, OpenAIProvider),
        ("OpenAI", {"llm_model": "gpt-x"}, OpenAIProvider),  # insensible à la casse
    ],
)
def test_create_llm_provider_changes_with_configuration_only(
    llm_provider: str, extra: dict[str, object], expected_type: type
) -> None:
    """Changer `llm_provider` (+ config associée) suffit : zéro modif de code."""
    settings = _settings(llm_provider=llm_provider, **extra)

    provider = create_llm_provider(settings)

    assert isinstance(provider, expected_type)


def test_anthropic_requires_api_key() -> None:
    settings = _settings(llm_provider="anthropic", llm_model="claude-x")

    with pytest.raises(LLMProviderConfigError, match="llm_api_key"):
        create_llm_provider(settings)


def test_openai_does_not_require_api_key() -> None:
    """Compatible Ollama/LM Studio : la clé peut être absente."""
    settings = _settings(llm_provider="openai", llm_model="local-model")

    provider = create_llm_provider(settings)

    assert isinstance(provider, OpenAIProvider)


def test_missing_model_raises_config_error() -> None:
    settings = _settings(llm_provider="anthropic", llm_api_key="sk-test")

    with pytest.raises(LLMProviderConfigError, match="llm_model"):
        create_llm_provider(settings)


def test_unknown_provider_raises_config_error() -> None:
    settings = _settings(llm_provider="mistral")

    with pytest.raises(LLMProviderConfigError, match="mistral"):
        create_llm_provider(settings)
