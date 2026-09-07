from __future__ import annotations

from fastapi.testclient import TestClient

from agentscope.infrastructure.config.settings import Settings
from agentscope.interfaces.api.app import create_app
from agentscope.interfaces.api.container import Container
from agentscope.interfaces.api.dependencies import get_container


def test_healthcheck_ok() -> None:
    app = create_app()
    with TestClient(app) as client:
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}


def test_container_initialization_in_lifespan() -> None:
    app = create_app()
    with TestClient(app):
        assert hasattr(app.state, "container")
        assert isinstance(app.state.container, Container)


def test_override_container_dependency() -> None:
    app = create_app()

    mock_settings = Settings(db_url="sqlite:///:memory:")
    mock_container = Container(mock_settings)

    app.dependency_overrides[get_container] = lambda: mock_container

    with TestClient(app) as client:
        response = client.get("/health")
        assert response.status_code == 200

    app.dependency_overrides.clear()
