from __future__ import annotations

from datetime import datetime
from fastapi.testclient import TestClient
import pytest

from agentscope.application.ports.data_quality import DataQualityBatchItem
from agentscope.application.ports.sources import SourceItem
from agentscope.interfaces.api.app import create_app
from agentscope.interfaces.api.dependencies import (
    get_data_quality_service,
    get_sources_service,
)


class DummySourcesService:
    def list_sources(self):
        return [
            SourceItem(
                id="src-tracelab",
                name="TraceLab",
                description="Traces JSONL benchmark",
                format="jsonl",
                session_count=120,
                created_at=datetime(2026, 9, 8, 10, 0, 0),
            )
        ]


class DummyDataQualityService:
    def get_quality_metrics(self, source_id=None):
        return [
            DataQualityBatchItem(
                import_batch_id="batch-001",
                source_name="TraceLab",
                imported_count=100,
                duplicate_count=5,
                rejected_count=2,
                missing_info_count=1,
                completeness_rate=0.97,
                imported_at=datetime(2026, 9, 8, 10, 0, 0),
            )
        ]


@pytest.fixture
def client():
    app = create_app()
    app.dependency_overrides[get_sources_service] = lambda: DummySourcesService()
    app.dependency_overrides[get_data_quality_service] = lambda: DummyDataQualityService()
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def test_list_sources(client):
    response = client.get("/api/v1/sources")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["id"] == "src-tracelab"
    assert data[0]["name"] == "TraceLab"


def test_get_data_quality(client):
    response = client.get("/api/v1/data-quality")
    assert response.status_code == 200
    data = response.json()
    assert "batches" in data
    assert len(data["batches"]) == 1
    batch = data["batches"][0]
    assert batch["import_batch_id"] == "batch-001"
    assert batch["completeness_rate"] == 0.97
