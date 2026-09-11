"""I4.2 bout-en-bout : routes /imports servies par le vrai ``SqlImportService``
(conteneur réel, base SQLite migrée, sans ``dependency_overrides``).
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient

import agentscope.infrastructure.persistence as persistence_pkg
from agentscope.domain import FileFormat, Source, SourceMapping
from agentscope.infrastructure.config.settings import Settings
from agentscope.infrastructure.persistence.database import Database
from agentscope.infrastructure.persistence.unit_of_work import SqlAlchemyUnitOfWork
from agentscope.interfaces.api.app import create_app

MIGRATIONS_DIR = Path(persistence_pkg.__file__).parent / "migrations"
NOW = datetime(2026, 1, 1, 12, 0, 0, tzinfo=UTC)

MAPPING_DEF = {
    "name": "demo-jsonl",
    "version": 1,
    "source_format": "jsonl",
    "constants": {"source_name": "demo"},
    "entities": {
        "session": {
            "iterate": {"path": ""},
            "identity": {"key_fields": ["sid"]},
            "fields": {
                "external_id": {"from": "sid", "required": True, "on_error": "reject"},
            },
        },
    },
}
ROWS = [{"sid": "s1"}, {"sid": "s2"}, {"no_sid": True}]
PAYLOAD = ("\n".join(json.dumps(r) for r in ROWS)).encode("utf-8")


@pytest.fixture
def client(tmp_path: Path):
    url = f"sqlite:///{tmp_path / 'api.db'}"
    cfg = Config()
    cfg.set_main_option("script_location", str(MIGRATIONS_DIR))
    cfg.set_main_option("sqlalchemy.url", url)
    command.upgrade(cfg, "head")

    settings = Settings(database_url=url, cors_origins=["http://testserver"])
    db = Database(settings)
    with SqlAlchemyUnitOfWork(db) as uow:
        uow.reference.add_source(Source(name="demo", display_name="Demo"))
        uow.mappings.add(
            SourceMapping(
                name="demo-jsonl",
                version=1,
                source_name="demo",
                source_format=FileFormat.JSONL,
                definition=MAPPING_DEF,
                created_at=NOW,
            )
        )
        uow.commit()
    db.engine.dispose()

    with TestClient(create_app(settings)) as c:
        yield c


def test_import_history_and_rejects_end_to_end(client: TestClient) -> None:
    created = client.post(
        "/api/v1/imports",
        data={"mapping_id": "demo-jsonl"},
        files={"files": ("demo.jsonl", PAYLOAD, "application/jsonl")},
    )
    assert created.status_code == 201, created.text
    body = created.json()
    assert body["mapping_id"] == "demo-jsonl"
    assert body["imported_count"] == 2
    assert body["rejected_count"] == 1
    import_id = body["id"]

    listed = client.get("/api/v1/imports?limit=10&offset=0")
    assert listed.status_code == 200
    page = listed.json()
    assert page["total"] == 1
    assert page["items"][0]["id"] == import_id

    detail = client.get(f"/api/v1/imports/{import_id}")
    assert detail.status_code == 200
    assert detail.json()["rejected_count"] == 1

    rejects = client.get(f"/api/v1/imports/{import_id}/rejects")
    assert rejects.status_code == 200
    assert rejects.json()["total"] == 1

    missing = client.get("/api/v1/imports/deadbeef")
    assert missing.status_code == 404


def test_unknown_mapping_returns_problem_json(client: TestClient) -> None:
    resp = client.post(
        "/api/v1/imports",
        data={"mapping_id": "pas-de-mapping"},
        files={"files": ("demo.jsonl", PAYLOAD, "application/jsonl")},
    )
    assert resp.status_code == 400
    assert resp.headers["content-type"] == "application/problem+json"
