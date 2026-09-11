"""Fixtures partagées."""

from __future__ import annotations

import os
from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from agentscope.infrastructure.config.settings import Settings
from agentscope.interfaces.api.app import create_app


@pytest.fixture(autouse=True)
def isolate_configuration(monkeypatch: pytest.MonkeyPatch) -> None:
    """Coupe la configuration des tests de la machine qui les exécute.

    ``Settings`` lit l'environnement réel **et** les fichiers ``.env`` du dépôt
    (voulu en production). Sans cette isolation, un test du type « clé API
    absente -> erreur de configuration » passe ou échoue selon le ``.env`` du
    développeur ou les variables injectées par ``docker compose``.

    Un test qui a besoin d'une variable la pose lui-même : ``monkeypatch``
    s'applique après cette fixture.
    """
    for name in [n for n in os.environ if n.startswith("AGENTSCOPE_")]:
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setitem(Settings.model_config, "env_file", None)


@pytest.fixture
def settings() -> Settings:
    """Configuration de test : base SQLite en mémoire, aucun appel externe."""
    return Settings(
        database_url="sqlite://",
        cors_origins=["http://testserver"],
        llm_provider="fake",
    )


@pytest.fixture
def client(settings: Settings) -> Iterator[TestClient]:
    # Le context manager déclenche le lifespan -> app.state.container.
    with TestClient(create_app(settings)) as test_client:
        yield test_client
