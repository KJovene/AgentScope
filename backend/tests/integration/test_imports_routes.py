from __future__ import annotations

from datetime import datetime
from io import BytesIO
from fastapi.testclient import TestClient
import pytest

from agentscope.application.ports.imports import ImportBatchItem, ImportRejectItem
from agentscope.application.ports.metrics import Page, Paginated
from agentscope.interfaces.api.app import create_app
from agentscope.interfaces.api.dependencies import get_import_service


class DummyImportService:

    async def process_import(self, mapping_id: str, files: list[tuple[str, bytes]]):
        return ImportBatchItem(
            id="batch-123",
            source_id="src-tracelab",
            mapping_id=mapping_id,
            status="completed",
            imported_count=10,
            duplicate_count=1,
            rejected_count=2,
            missing_info_count=0,
            imported_at=datetime(2026, 9, 8, 10, 0, 0),
        )

    def list_imports(self, page: Page):
        item = ImportBatchItem(
            id="batch-123",
            source_id="src-tracelab",
            mapping_id="tracelab-jsonl",
            status="completed",
            imported_count=10,
            duplicate_count=1,
            rejected_count=2,
            missing_info_count=0,
            imported_at=datetime(2026, 9, 8, 10, 0, 0),
        )
        return Paginated(items=(item,), total=1, limit=page.limit, offset=page.offset)

    def get_import_detail(self, import_id: str):
        if import_id != "batch-123":
            return None
        return ImportBatchItem(
            id="batch-123",
            source_id="src-tracelab",
            mapping_id="tracelab-jsonl",
            status="completed",
            imported_count=10,
            duplicate_count=1,
            rejected_count=2,
            missing_info_count=0,
            imported_at=datetime(2026, 9, 8, 10, 0, 0),
        )

    def list_rejects(self, import_id: str, page: Page):
        reject = ImportRejectItem(
            id="rej-01",
            import_batch_id=import_id,
            line_number=4,
            raw_record='{"bad": "format"}',
            reason="Champ session_id manquant",
            rejected_at=datetime(2026, 9, 8, 10, 0, 0),
        )
        return Paginated(items=(reject,), total=1, limit=page.limit, offset=page.offset)


@pytest.fixture
def client():
    app = create_app()
    app.dependency_overrides[get_import_service] = lambda: DummyImportService()
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def test_create_import_multi_file(client):
    file_content = b'{"session_id": "s1"}\n'
    files = [
        ("files", ("f1.jsonl", BytesIO(file_content), "application/json")),
        ("files", ("f2.jsonl", BytesIO(file_content), "application/json")),
    ]
    data = {"mapping_id": "tracelab-jsonl"}

    response = client.post("/api/v1/imports", files=files, data=data)
    assert response.status_code == 201
    body = response.json()
    assert body["id"] == "batch-123"
    assert body["imported_count"] == 10


def test_list_imports_paginated(client):
    response = client.get("/api/v1/imports?limit=10&offset=0")
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert body["items"][0]["id"] == "batch-123"


def test_get_import_detail(client):
    response = client.get("/api/v1/imports/batch-123")
    assert response.status_code == 200
    assert response.json()["mapping_id"] == "tracelab-jsonl"


def test_get_import_detail_not_found(client):
    response = client.get("/api/v1/imports/unknown-batch")
    assert response.status_code == 404


def test_list_import_rejects(client):
    response = client.get("/api/v1/imports/batch-123/rejects")
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert body["items"][0]["reason"] == "Champ session_id manquant"
