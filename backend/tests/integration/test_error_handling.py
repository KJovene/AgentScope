from __future__ import annotations

from fastapi import HTTPException
from fastapi.testclient import TestClient
import pytest

from agentscope.domain.errors import DomainError
from agentscope.interfaces.api.app import create_app


@pytest.fixture
def client():
    app = create_app()

    @app.get("/test-domain-error")
    def _domain_error_route():
        raise DomainError("L'invariant du domaine est violé.")

    @app.get("/test-404")
    def _not_found_route():
        raise HTTPException(status_code=404, detail="Ressource introuvable.")

    with TestClient(app) as c:
        yield c


def test_validation_error_format(client):
    response = client.get("/api/v1/sessions?limit=not_an_int")
    assert response.status_code == 422
    assert response.headers["content-type"] == "application/problem+json"

    body = response.json()
    assert body["title"] == "Requête invalide"
    assert body["status"] == 422
    assert isinstance(body["errors"], list)


def test_http_404_format(client):
    response = client.get("/test-404")
    assert response.status_code == 404
    assert response.headers["content-type"] == "application/problem+json"

    body = response.json()
    assert body["status"] == 404
    assert body["detail"] == "Ressource introuvable."


def test_domain_error_format(client):
    response = client.get("/test-domain-error")
    assert response.status_code == 400
    assert response.headers["content-type"] == "application/problem+json"

    body = response.json()
    assert body["title"] == "Violation de règle métier"
    assert body["detail"] == "L'invariant du domaine est violé."
