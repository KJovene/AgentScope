"""``SqlMappingService`` (issue I4.5) — CRUD versionné sur base SQLite migrée."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from agentscope.application.use_cases.manage_mappings import (
    MappingAlreadyExistsError,
    MappingNotFoundError,
)
from agentscope.domain import DomainError, FileFormat, InvalidMappingError
from agentscope.infrastructure.persistence.database import Database
from agentscope.infrastructure.persistence.services.mapping_service import (
    MissingSourceNameError,
    SqlMappingService,
)

NOW = datetime(2026, 1, 1, 12, 0, 0, tzinfo=UTC)


def _definition(source_name: str = "TraceLab", field_name: str = "external_id") -> dict:
    return {
        "name": "tracelab-jsonl",
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
def service(database: Database) -> SqlMappingService:
    return SqlMappingService(database.create_session(), clock=lambda: NOW)


def test_create_autocreates_the_source_and_stores_version_1(service: SqlMappingService) -> None:
    created = service.create(
        name="tracelab-jsonl",
        source_format=FileFormat.JSONL,
        definition=_definition(),
    )
    assert created.version == 1
    assert created.source_name == "TraceLab"

    fetched = service.get(name="tracelab-jsonl")
    assert fetched is not None
    assert fetched.version == 1


def test_create_rejects_a_duplicate_name(service: SqlMappingService) -> None:
    service.create(name="m", source_format=FileFormat.JSONL, definition=_definition())
    with pytest.raises(MappingAlreadyExistsError):
        service.create(name="m", source_format=FileFormat.JSONL, definition=_definition())


def test_create_rejects_a_definition_without_source_name(service: SqlMappingService) -> None:
    bad = _definition()
    bad["constants"] = {}
    with pytest.raises(MissingSourceNameError):
        service.create(name="m", source_format=FileFormat.JSONL, definition=bad)


def test_create_rejects_an_invalid_definition(service: SqlMappingService) -> None:
    with pytest.raises(InvalidMappingError):
        service.create(
            name="m", source_format=FileFormat.JSONL, definition={"constants": {"source_name": "S"}}
        )


def test_update_creates_the_next_version(service: SqlMappingService) -> None:
    service.create(name="m", source_format=FileFormat.JSONL, definition=_definition())

    v2 = service.update(name="m", definition=_definition(field_name="agent_name"))
    assert v2.version == 2

    assert service.get(name="m").version == 2  # dernière version active
    assert service.get(name="m", version=1) is not None


def test_update_unknown_mapping_raises(service: SqlMappingService) -> None:
    with pytest.raises(MappingNotFoundError):
        service.update(name="absent", definition=_definition())


def test_list_all_and_filtered_by_source(service: SqlMappingService) -> None:
    service.create(name="a", source_format=FileFormat.JSONL, definition=_definition("TraceLab"))
    service.create(name="b", source_format=FileFormat.CSV, definition=_definition("SWE-chat"))

    assert {m.name for m in service.list()} == {"a", "b"}
    assert [m.name for m in service.list(source_name="SWE-chat")] == ["b"]


def test_get_unknown_returns_none(service: SqlMappingService) -> None:
    assert service.get(name="nope") is None
    assert isinstance(MissingSourceNameError("x"), DomainError)
