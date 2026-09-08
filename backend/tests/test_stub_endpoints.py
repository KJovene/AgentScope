"""
I4.1 — Definition of Done : /docs affiche tous les endpoints ; le front peut démarrer.

Ce test ne vérifie pas de logique métier (il n'y en a pas encore ici) : il
vérifie que chaque route du contrat §5.3 répond avec la forme attendue à
partir des fixtures, et que les erreurs suivent bien le format problem+json.
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


# NOTE : /imports/* n'est plus un stub — la route est branchée sur le port
# `ImportService` (le service réel reste à câbler, cf. I4.2). Elle est couverte
# par tests/integration/test_imports_routes.py (service simulé via dependency_overrides).


def test_analyze_returns_profile_and_proposal() -> None:
    resp = client.post(
        "/api/v1/analyze",
        files={"file": ("unknown.jsonl", b'{"a": 1}\n', "application/jsonl")},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert "profile" in body and "proposal" in body


def test_mapping_crud_and_preview() -> None:
    created = client.post(
        "/api/v1/mappings",
        json={"name": "tracelab-jsonl", "source_format": "jsonl", "definition": {}},
    )
    assert created.status_code == 201
    mapping_id = created.json()["mapping_id"]

    listed = client.get("/api/v1/mappings")
    assert listed.status_code == 200

    fetched = client.get(f"/api/v1/mappings/{mapping_id}")
    assert fetched.status_code == 200

    updated = client.put(f"/api/v1/mappings/{mapping_id}", json={"definition": {"entities": {}}})
    assert updated.status_code == 200
    assert updated.json()["version"] == fetched.json()["version"] + 1

    preview = client.post(f"/api/v1/mappings/{mapping_id}/preview")
    assert preview.status_code == 200
    assert "rows" in preview.json()


def test_chat_has_no_db_side_effect_and_returns_reply() -> None:
    resp = client.post(
        "/api/v1/chat",
        json={"conversation_id": "c1", "message": "Pourquoi ce mapping ?", "file_ref": "profile_1"},
    )
    assert resp.status_code == 200
    assert "text" in resp.json()


# NOTE : /metrics/*, /sessions/*, /sources et /data-quality ne sont plus des stubs.
# Ils sont branchés sur des services de lecture réels et couverts par
# tests/integration/test_metrics_routes.py, test_sessions_routes.py et
# test_sources_and_quality_routes.py (avec bases migrées / services simulés).


def test_validation_error_is_problem_json() -> None:
    resp = client.post("/api/v1/chat", json={"conversation_id": "c1"})  # champs requis manquants
    assert resp.status_code == 422
    body = resp.json()
    assert body["status"] == 422
    assert isinstance(body["errors"], list) and len(body["errors"]) > 0
