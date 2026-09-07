"""Fume-test : l'application démarre et /health répond."""

from fastapi.testclient import TestClient

from agentscope.interfaces.api.app import create_app


def test_health_ok() -> None:
    client = TestClient(create_app())

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
