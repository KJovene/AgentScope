"""Fixtures partagées."""

from __future__ import annotations

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from agentscope.infrastructure.config.settings import Settings
from agentscope.interfaces.api.app import create_app


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
