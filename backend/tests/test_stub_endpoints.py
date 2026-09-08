"""Contrat OpenAPI (issue I4.1) : toutes les routes du §5.3 sont exposées et
``/docs`` démarre.

La plupart des routes sont désormais branchées sur des services réels et
couvertes par leurs tests d'intégration dédiés :

- ``/imports/*``            → ``test_imports_routes.py`` / ``test_imports_api_real.py``
- ``/analyze`` · ``/mappings/{id}/preview`` → ``test_analyze_preview_routes.py``
- ``/chat``                 → ``test_chat_route.py``
- ``/mappings`` (CRUD)      → ``test_mappings_routes.py``
- ``/metrics/*`` · ``/sessions/*`` · ``/sources`` · ``/data-quality``
      → ``test_metrics_routes.py`` / ``test_sessions_routes.py`` /
        ``test_sources_and_quality_routes.py``
- format ``problem+json`` des erreurs → ``test_error_handling.py``
"""

from __future__ import annotations

from fastapi.testclient import TestClient

from agentscope.interfaces.api.app import app

client = TestClient(app)


def test_health() -> None:
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_openapi_lists_all_contract_routes() -> None:
    resp = client.get("/openapi.json")
    assert resp.status_code == 200
    paths = resp.json()["paths"]
    expected = {
        "/api/v1/imports",
        "/api/v1/imports/{import_id}",
        "/api/v1/imports/{import_id}/rejects",
        "/api/v1/analyze",
        "/api/v1/mappings",
        "/api/v1/mappings/{mapping_id}",
        "/api/v1/mappings/{mapping_id}/preview",
        "/api/v1/chat",
        "/api/v1/metrics/indicators",
        "/api/v1/metrics/timeseries",
        "/api/v1/metrics/tool-usage",
        "/api/v1/sessions",
        "/api/v1/sessions/{session_id}",
        "/api/v1/sources",
        "/api/v1/data-quality",
    }
    assert expected.issubset(paths.keys())
