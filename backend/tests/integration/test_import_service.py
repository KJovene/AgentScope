"""``SqlImportService`` (issue I4.2) — orchestration réelle des routes /imports
contre une base SQLite migrée.
"""

from __future__ import annotations

import json
from collections.abc import Callable
from datetime import UTC, datetime

import pytest

from agentscope.application.ports.metrics import Page
from agentscope.domain import DomainError, FileFormat, ImportStatus, Source, SourceMapping
from agentscope.infrastructure.persistence.database import Database
from agentscope.infrastructure.persistence.services.import_service import SqlImportService
from agentscope.infrastructure.persistence.unit_of_work import SqlAlchemyUnitOfWork
from agentscope.infrastructure.readers.csv_reader import CsvReader
from agentscope.infrastructure.readers.jsonl_reader import JsonlReader
from agentscope.infrastructure.readers.parquet_reader import ParquetReader

NOW = datetime(2026, 1, 1, 12, 0, 0, tzinfo=UTC)
MakeUow = Callable[[], SqlAlchemyUnitOfWork]

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
                "agent_name": {"from": "agent"},
            },
        },
        "model_call": {
            "iterate": {"path": ""},
            "parent": {"entity": "session", "key_from": "sid"},
            "identity": {"key_fields": ["sid", "round"]},
            "fields": {
                "sequence": {"from": "round", "transform": "to_int"},
                "model_name": {"from": "model", "required": True, "on_error": "reject"},
            },
        },
    },
}

ROWS = [
    {"sid": "s1", "agent": "claude", "model": "m-1", "round": 0},
    {"sid": "s2", "agent": "codex", "model": "m-2", "round": 0},
    {"agent": "orphan", "model": "m-3", "round": 0},  # pas de `sid` -> rejet
]
PAYLOAD = ("\n".join(json.dumps(r) for r in ROWS)).encode("utf-8")


@pytest.fixture
def service(make_uow: MakeUow, database: Database) -> SqlImportService:
    with make_uow() as uow:
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

    return SqlImportService(
        session=database.create_session(),
        uow_factory=lambda: SqlAlchemyUnitOfWork(database),
        readers=(JsonlReader(), CsvReader(), ParquetReader()),
        clock=lambda: NOW,
    )


async def test_process_import_returns_aggregated_batch_item(service: SqlImportService) -> None:
    item = await service.process_import("demo-jsonl", [("demo.jsonl", PAYLOAD)])

    assert item.mapping_id == "demo-jsonl"
    assert item.source_id == "demo"
    assert item.status == "partial"  # 1 rejet
    assert item.imported_count == 2 + 2  # 2 sessions + 2 model_calls
    assert item.rejected_count == 1
    assert len(item.id) == 64  # sha256 hex
    assert item.imported_at == NOW


async def test_list_get_and_rejects_round_trip(service: SqlImportService) -> None:
    created = await service.process_import("demo-jsonl", [("demo.jsonl", PAYLOAD)])

    page = service.list_imports(Page(limit=50, offset=0))
    assert page.total == 1
    assert page.items[0].id == created.id
    assert page.items[0].mapping_id == "demo-jsonl"

    detail = service.get_import_detail(created.id)
    assert detail is not None
    assert detail.rejected_count == 1

    assert service.get_import_detail("inconnu") is None

    rejects = service.list_rejects(created.id, Page(limit=50, offset=0))
    assert rejects.total == 1
    r = rejects.items[0]
    assert r.import_batch_id == created.id
    assert r.line_number == 2
    assert r.reason  # message lisible
    assert service.list_rejects("inconnu", Page(limit=50, offset=0)).total == 0


async def test_reimport_same_file_is_idempotent(service: SqlImportService) -> None:
    first = await service.process_import("demo-jsonl", [("demo.jsonl", PAYLOAD)])
    second = await service.process_import("demo-jsonl", [("demo.jsonl", PAYLOAD)])

    assert first.id == second.id
    assert service.list_imports(Page(limit=50, offset=0)).total == 1


async def test_unknown_mapping_raises_domain_error(service: SqlImportService) -> None:
    with pytest.raises(DomainError):
        await service.process_import("inconnu", [("demo.jsonl", PAYLOAD)])


async def test_unsupported_extension_raises_domain_error(service: SqlImportService) -> None:
    with pytest.raises(DomainError):
        await service.process_import("demo-jsonl", [("demo.txt", PAYLOAD)])
