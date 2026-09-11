"""Coût estimé (docs/data/indicators.md §3.4) — bout en bout via l'API.

Une source qui ne déclare pas de coût (SWE-chat) : après `POST /model-pricing`,
`total_cost_usd` est estimé `tokens × tarif` et `cost_is_estimated` passe à true.
Un modèle sans ligne de tarif ne contribue rien (le coût absent reste absent).
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient

import agentscope.infrastructure.persistence as persistence_pkg
from agentscope.infrastructure.config.settings import Settings
from agentscope.interfaces.api.app import create_app

ROOT = Path(__file__).resolve().parents[3]
MIGRATIONS_DIR = Path(persistence_pkg.__file__).parent / "migrations"
SWE_MAPPING = ROOT / "docs" / "data" / "mappings" / "swe-chat.json"
SWE_FIXTURE = ROOT / "backend" / "tests" / "fixtures" / "swe_chat" / "sample.jsonl"


@pytest.fixture
def client(tmp_path: Path):
    url = f"sqlite:///{tmp_path / 'c.db'}"
    cfg = Config()
    cfg.set_main_option("script_location", str(MIGRATIONS_DIR))
    cfg.set_main_option("sqlalchemy.url", url)
    command.upgrade(cfg, "head")
    with TestClient(create_app(Settings(database_url=url))) as c:
        yield c


def _import_swe_chat(client: TestClient) -> None:
    definition = json.loads(SWE_MAPPING.read_text(encoding="utf-8"))
    created = client.post(
        "/api/v1/mappings",
        json={"name": "swe-chat-jsonl", "source_format": "jsonl", "definition": definition},
    )
    assert created.status_code == 201, created.text
    up = client.post(
        "/api/v1/imports",
        data={"mapping_id": "swe-chat-jsonl"},
        files={"files": ("sample.jsonl", SWE_FIXTURE.read_bytes(), "application/octet-stream")},
    )
    assert up.status_code == 201, up.text


def test_cost_absent_sans_grille(client: TestClient) -> None:
    _import_swe_chat(client)
    ind = client.get("/api/v1/metrics/indicators").json()
    assert ind["total_cost_usd"] is None
    assert ind["cost_is_estimated"] is False


def test_cost_estime_apres_seed_pricing(client: TestClient) -> None:
    client.post(
        "/api/v1/model-pricing",
        json=[
            {
                "model_name": "claude-opus-4-6",
                "input_usd_per_mtok": 15.0,
                "output_usd_per_mtok": 75.0,
                "cached_usd_per_mtok": 1.5,
            },
            # gpt-5-codex volontairement absent -> swe-b ne contribue rien
        ],
    )
    _import_swe_chat(client)

    ind = client.get("/api/v1/metrics/indicators").json()
    # swe-a (claude-opus-4-6) : completion 200 * 75 + cached 5000 * 1.5, /1e6
    expected = (200 * 75 + 5000 * 1.5) / 1_000_000
    assert ind["total_cost_usd"] == pytest.approx(expected)
    assert ind["cost_is_estimated"] is True


def test_pricing_upsert_is_idempotent(client: TestClient) -> None:
    body = [{"model_name": "m", "input_usd_per_mtok": 1.0, "output_usd_per_mtok": 2.0}]
    assert client.post("/api/v1/model-pricing", json=body).json() == {"upserted": 1}
    body[0]["output_usd_per_mtok"] = 9.0
    assert client.post("/api/v1/model-pricing", json=body).json() == {"upserted": 1}
    listed = client.get("/api/v1/model-pricing").json()
    assert listed == [
        {
            "model_name": "m",
            "input_usd_per_mtok": 1.0,
            "output_usd_per_mtok": 9.0,
            "cached_usd_per_mtok": None,
        }
    ]
