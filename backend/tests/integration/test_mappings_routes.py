"""I4.5 — CRUD ``/mappings`` bout-en-bout : conteneur réel, base SQLite migrée,
sans ``dependency_overrides``.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient

import agentscope.infrastructure.persistence as persistence_pkg
from agentscope.infrastructure.config.settings import Settings
from agentscope.interfaces.api.app import create_app

MIGRATIONS_DIR = Path(persistence_pkg.__file__).parent / "migrations"


def _definition(source_name: str, field_name: str = "external_id") -> dict:
    return {
        "name": "demo",
        "version": 1,
        "source_format": "jsonl",
        "constants": {"source_name": source_name},
        "entities": {
            "session": {
                "iterate": {"path": "", "where": []},
                "identity": {"key_fields": ["session_id"]},
                "fields": {
                    field_name: {
                        "from": "session_id",
                        "transform": "identity",
                        "required": True,
                        "on_error": "reject",
                    }
                },
            }
        },
    }


@pytest.fixture
def client(tmp_path: Path):
    url = f"sqlite:///{tmp_path / 'm.db'}"
    cfg = Config()
    cfg.set_main_option("script_location", str(MIGRATIONS_DIR))
    cfg.set_main_option("sqlalchemy.url", url)
    command.upgrade(cfg, "head")
    with TestClient(create_app(Settings(database_url=url))) as c:
        yield c


def test_full_crud_round_trip(client: TestClient) -> None:
    # create -> v1, source "Nouvelle" créée automatiquement
    created = client.post(
        "/api/v1/mappings",
        json={"name": "demo", "source_format": "jsonl", "definition": _definition("Nouvelle")},
    )
    assert created.status_code == 201, created.text
    body = created.json()
    assert body["mapping_id"] == "demo"
    assert body["version"] == 1
    assert body["source_name"] == "Nouvelle"

    # list
    listed = client.get("/api/v1/mappings")
    assert listed.status_code == 200
    assert listed.json()["total"] == 1
    assert listed.json()["items"][0]["name"] == "demo"

    # get (dernière version)
    fetched = client.get("/api/v1/mappings/demo")
    assert fetched.status_code == 200
    assert fetched.json()["version"] == 1

    # PUT -> v2
    updated = client.put(
        "/api/v1/mappings/demo",
        json={"definition": _definition("Nouvelle", field_name="agent_name")},
    )
    assert updated.status_code == 200
    assert updated.json()["version"] == 2

    assert client.get("/api/v1/mappings/demo").json()["version"] == 2
    assert client.get("/api/v1/mappings/demo?version=1").json()["version"] == 1


def test_create_duplicate_is_400_problem_json(client: TestClient) -> None:
    payload = {"name": "dup", "source_format": "jsonl", "definition": _definition("S")}
    assert client.post("/api/v1/mappings", json=payload).status_code == 201
    resp = client.post("/api/v1/mappings", json=payload)
    assert resp.status_code == 400
    assert resp.headers["content-type"] == "application/problem+json"


def test_get_unknown_is_404(client: TestClient) -> None:
    assert client.get("/api/v1/mappings/nope").status_code == 404


def test_put_unknown_is_404(client: TestClient) -> None:
    resp = client.put("/api/v1/mappings/nope", json={"definition": _definition("S")})
    assert resp.status_code == 404


def test_create_with_bad_source_format_is_422(client: TestClient) -> None:
    resp = client.post(
        "/api/v1/mappings",
        json={"name": "x", "source_format": "xml", "definition": _definition("S")},
    )
    assert resp.status_code == 422


def test_create_without_source_name_is_400(client: TestClient) -> None:
    definition = _definition("S")
    definition["constants"] = {}
    resp = client.post(
        "/api/v1/mappings",
        json={"name": "x", "source_format": "jsonl", "definition": definition},
    )
    assert resp.status_code == 400
