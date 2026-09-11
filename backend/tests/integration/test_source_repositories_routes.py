"""``/sources/{name}/repositories`` — déclaration idempotente des dépôts de code
d'une source (dimension SWE-chat, I1.10). Conteneur réel + SQLite migrée.
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


def _mapping_definition(source_name: str) -> dict:
    return {
        "name": "m",
        "version": 1,
        "source_format": "jsonl",
        "constants": {"source_name": source_name},
        "entities": {
            "session": {
                "iterate": {"path": ""},
                "identity": {"key_fields": ["session_id"]},
                "fields": {
                    "external_id": {
                        "from": "session_id",
                        "required": True,
                        "on_error": "reject",
                    }
                },
            }
        },
    }


@pytest.fixture
def client(tmp_path: Path):
    url = f"sqlite:///{tmp_path / 'r.db'}"
    cfg = Config()
    cfg.set_main_option("script_location", str(MIGRATIONS_DIR))
    cfg.set_main_option("sqlalchemy.url", url)
    command.upgrade(cfg, "head")
    with TestClient(create_app(Settings(database_url=url))) as c:
        # Crée la source « SWE-chat » (le POST /mappings la crée à la volée).
        r = c.post(
            "/api/v1/mappings",
            json={
                "name": "m",
                "source_format": "jsonl",
                "definition": _mapping_definition("SWE-chat"),
            },
        )
        assert r.status_code == 201, r.text
        yield c


def test_register_then_list(client: TestClient) -> None:
    body = [
        {"name": "octo/api", "url": "https://x/api", "language": "python"},
        {"name": "octo/web"},
    ]
    created = client.post("/api/v1/sources/SWE-chat/repositories", json=body)
    assert created.status_code == 201, created.text
    assert created.json() == {"registered": 2, "skipped": 0, "total": 2}

    listed = client.get("/api/v1/sources/SWE-chat/repositories")
    assert listed.status_code == 200
    assert [r["name"] for r in listed.json()] == ["octo/api", "octo/web"]
    assert listed.json()[0]["language"] == "python"


def test_register_is_idempotent(client: TestClient) -> None:
    body = [{"name": "octo/api"}]
    assert client.post("/api/v1/sources/SWE-chat/repositories", json=body).status_code == 201
    again = client.post("/api/v1/sources/SWE-chat/repositories", json=body)
    assert again.json() == {"registered": 0, "skipped": 1, "total": 1}


def test_unknown_source_is_404(client: TestClient) -> None:
    assert client.get("/api/v1/sources/Nope/repositories").status_code == 404
    assert (
        client.post("/api/v1/sources/Nope/repositories", json=[{"name": "a/b"}]).status_code == 404
    )
