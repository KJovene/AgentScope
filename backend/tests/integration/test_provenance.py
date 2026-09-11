"""Provenance : remonter d'une entité normalisée à son enregistrement brut,
et rétention configurable (issue I1.7)."""

from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime

import pytest
from sqlalchemy import text

from agentscope.domain import (
    CallStatus,
    FileFormat,
    ImportBatch,
    ImportStatus,
    Interval,
    ModelCall,
    Provenance,
    RawRecord,
    RetentionMode,
    RetentionPolicy,
    Session,
    Source,
    SourceMapping,
    ToolCall,
)
from agentscope.infrastructure.persistence.database import Database
from agentscope.infrastructure.persistence.repositories import SqlProvenanceRepository
from agentscope.infrastructure.persistence.unit_of_work import SqlAlchemyUnitOfWork

NOW = datetime(2026, 4, 1, 9, 0, 0, tzinfo=UTC)
SHA = "SHA-PROV"
MakeUow = Callable[[], SqlAlchemyUnitOfWork]


def _batch() -> ImportBatch:
    return ImportBatch(
        source_name="tracelab",
        original_filename="s.jsonl",
        file_sha256=SHA,
        file_format=FileFormat.JSONL,
        imported_at=NOW,
        status=ImportStatus.SUCCEEDED,
        mapping_name="m",
    )


def _seed(uow: SqlAlchemyUnitOfWork, records: list[RawRecord]) -> None:
    with uow:
        uow.reference.add_source(Source(name="tracelab"))
        uow.mappings.add(
            SourceMapping(
                name="m",
                version=1,
                source_name="tracelab",
                source_format=FileFormat.JSONL,
                definition={"e": 1},
                created_at=NOW,
            )
        )
        batch = _batch()
        uow.imports.add(batch)
        uow.raw_records.upsert_many(batch, records)
        uow.sessions.upsert_many(
            batch,
            [
                Session(
                    source_name="tracelab",
                    external_id="sess-1",
                    provenance=Provenance(record_index=0, record_sha256="rr-0"),
                    interval=Interval(started_at=NOW, ended_at=NOW),
                )
            ],
        )
        uow.model_calls.upsert_many(
            batch,
            [
                ModelCall(
                    source_name="tracelab",
                    session_external_id="sess-1",
                    sequence=0,
                    model_name="claude-sonnet",
                    provenance=Provenance(record_index=1, record_sha256="rr-1"),
                    status=CallStatus.SUCCESS,
                )
            ],
        )
        uow.tool_calls.upsert_many(
            batch,
            [
                ToolCall(
                    source_name="tracelab",
                    session_external_id="sess-1",
                    sequence=0,
                    tool_name="bash",
                    provenance=Provenance(record_index=1, record_sha256="rr-1"),
                    status=CallStatus.SUCCESS,
                )
            ],
        )
        uow.commit()


def _records_full() -> list[RawRecord]:
    return [
        RawRecord(index=0, payload={"session_id": "sess-1"}, sha256="rr-0"),
        RawRecord(index=1, payload={"type": "model", "model": "claude"}, sha256="rr-1"),
    ]


def test_walk_back_from_each_normalised_entity(make_uow: MakeUow, database: Database) -> None:
    _seed(make_uow(), _records_full())
    prov = SqlProvenanceRepository(database.create_session())

    from_session = prov.raw_record_for_session("tracelab", "sess-1")
    assert from_session is not None
    assert from_session.index == 0
    assert from_session.payload == {"session_id": "sess-1"}

    from_model = prov.raw_record_for_model_call("tracelab", "sess-1", 0)
    assert from_model is not None
    assert from_model.sha256 == "rr-1"
    assert from_model.payload["model"] == "claude"

    from_tool = prov.raw_record_for_tool_call("tracelab", "sess-1", 0)
    assert from_tool is not None
    assert from_tool.index == 1


def test_walk_back_returns_none_for_unknown_keys(make_uow: MakeUow, database: Database) -> None:
    _seed(make_uow(), _records_full())
    prov = SqlProvenanceRepository(database.create_session())
    assert prov.raw_record_for_session("tracelab", "absent") is None
    assert prov.raw_record_for_model_call("tracelab", "sess-1", 99) is None


@pytest.mark.parametrize(
    ("mode", "payload_stored"),
    [(RetentionMode.FULL, True), (RetentionMode.MINIMAL, False)],
)
def test_retention_policy_controls_payload_but_never_the_link(
    make_uow: MakeUow, database: Database, mode: RetentionMode, payload_stored: bool
) -> None:
    policy = RetentionPolicy(mode=mode)
    records = [policy.apply(r) for r in _records_full()]  # ce que fera l'import (I2.8)
    _seed(make_uow(), records)

    with database.engine.connect() as conn:
        payloads = (
            conn.execute(text("SELECT payload_json FROM raw_record ORDER BY record_index"))
            .scalars()
            .all()
        )
        # la ligne raw_record existe toujours, seule la charge varie
        assert conn.execute(text("SELECT count(*) FROM raw_record")).scalar_one() == 2
        # le lien de provenance reste intact quelle que soit la rétention
        linked = conn.execute(
            text("SELECT raw_record_id FROM session WHERE external_id = 'sess-1'")
        ).scalar_one()
        assert linked is not None

    if payload_stored:
        assert all(p is not None for p in payloads)
    else:
        assert all(p is None for p in payloads)

    prov = SqlProvenanceRepository(database.create_session())
    walked = prov.raw_record_for_session("tracelab", "sess-1")
    assert walked is not None and walked.index == 0
    assert walked.payload == ({"session_id": "sess-1"} if payload_stored else {})


def test_settings_reads_retention_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    from agentscope.infrastructure.config.settings import Settings

    monkeypatch.setenv("AGENTSCOPE_RAW_RECORD_RETENTION", "minimal")
    assert Settings().raw_record_retention is RetentionMode.MINIMAL
