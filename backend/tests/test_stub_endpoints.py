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


# NOTE : plusieurs routes ne sont plus des stubs et sont couvertes ailleurs :
#  - /imports/*            -> port ImportService            (test_imports_routes.py,
#                                                            test_imports_api_real.py)
#  - /analyze              -> MappingWorkbenchService (I4.3) (test_analyze_preview_routes.py)
#  - /mappings/{id}/preview -> idem                          (test_analyze_preview_routes.py)


def test_mapping_crud_stub() -> None:
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


# NOTE : /chat est branché sur MappingWorkbenchService (I4.4) — couvert par
# tests/integration/test_chat_route.py.
# /metrics/*, /sessions/*, /sources et /data-quality sont branchés sur des
# services de lecture réels — couverts par test_metrics_routes.py,
# test_sessions_routes.py et test_sources_and_quality_routes.py.


def test_validation_error_is_problem_json() -> None:
    # /mappings (POST) est un stub sans dépendance conteneur : convient pour
    # vérifier le format d'erreur de validation avec un simple TestClient(app).
    resp = client.post("/api/v1/mappings", json={"name": "x"})  # source_format + definition manquants
    assert resp.status_code == 422
    body = resp.json()
    assert body["status"] == 422
    assert isinstance(body["errors"], list) and len(body["errors"]) > 0
