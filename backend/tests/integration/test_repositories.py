"""Implémentations SQLAlchemy des repositories + UnitOfWork (issue I1.5).

Vérifie : câblage des clés étrangères par clé naturelle, idempotence
(ignore-on-conflict), atomicité de l'UoW, conservation des relations.
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime

import pytest
from sqlalchemy import text

from agentscope.application.ports import UpsertOutcome
from agentscope.domain import (
    CallStatus,
    FieldProfile,
    FileFormat,
    ImportBatch,
    ImportReject,
    ImportStatus,
    Interval,
    ModelCall,
    Provenance,
    RawRecord,
    RejectReason,
    Repository,
    Session,
    Source,
    SourceMapping,
    TokenUsage,
    ToolCall,
)
from agentscope.infrastructure.persistence.database import Database
from agentscope.infrastructure.persistence.repositories.errors import UnknownReferenceError
from agentscope.infrastructure.persistence.unit_of_work import SqlAlchemyUnitOfWork

NOW = datetime(2026, 1, 1, 12, 0, 0, tzinfo=UTC)
SHA = "SHA-FILE-1"

MakeUow = Callable[[], SqlAlchemyUnitOfWork]


# --- fabriques d'entités ---------------------------------------------------


def a_batch(status: ImportStatus = ImportStatus.RUNNING) -> ImportBatch:
    return ImportBatch(
        source_name="tracelab",
        original_filename="sessions.jsonl",
        file_sha256=SHA,
        file_format=FileFormat.JSONL,
        imported_at=NOW,
        status=status,
        mapping_name="tracelab-jsonl",
    )


def raw_records() -> list[RawRecord]:
    return [
        RawRecord(index=0, payload={"session_id": "sess-1"}, sha256="rr-0"),
        RawRecord(index=1, payload={"session_id": "sess-1"}, sha256="rr-1"),
    ]


def sessions() -> list[Session]:
    return [
        Session(
            source_name="tracelab",
            external_id="sess-1",
            provenance=Provenance(record_index=0, record_sha256="rr-0"),
            agent_name="claude",
            interval=Interval(started_at=NOW, ended_at=NOW),
            repository_name="acme/widgets",
        )
    ]


def model_calls() -> list[ModelCall]:
    return [
        ModelCall(
            source_name="tracelab",
            session_external_id="sess-1",
            sequence=0,
            model_name="claude-sonnet",
            provenance=Provenance(record_index=0, record_sha256="rr-0"),
            tokens=TokenUsage(prompt_tokens=100, completion_tokens=40),
            status=CallStatus.SUCCESS,
        )
    ]


def tool_calls() -> list[ToolCall]:
    return [
        ToolCall(
            source_name="tracelab",
            session_external_id="sess-1",
            sequence=0,
            tool_name="bash",
            provenance=Provenance(record_index=1, record_sha256="rr-1"),
            model_call_sequence=0,
            status=CallStatus.SUCCESS,
        )
    ]


def seed_full(uow: SqlAlchemyUnitOfWork) -> None:
    with uow:
        uow.reference.add_source(Source(name="tracelab", display_name="TraceLab"))
        uow.reference.upsert_code_repositories(
            "tracelab", [Repository(source_name="tracelab", name="acme/widgets")]
        )
        uow.mappings.add(
            SourceMapping(
                name="tracelab-jsonl",
                version=1,
                source_name="tracelab",
                source_format=FileFormat.JSONL,
                definition={"entities": {}},
                created_at=NOW,
            )
        )
        batch = a_batch()
        uow.imports.add(batch)
        uow.raw_records.upsert_many(batch, raw_records())
        uow.sessions.upsert_many(batch, sessions())
        uow.model_calls.upsert_many(batch, model_calls())
        uow.tool_calls.upsert_many(batch, tool_calls())
        uow.imports.update(a_batch(status=ImportStatus.SUCCEEDED))
        uow.commit()


def row_counts(database: Database) -> dict[str, int]:
    tables = ["source", "session", "model_call", "tool_call", "raw_record", "import_batch"]
    with database.engine.connect() as conn:
        return {
            t: conn.execute(text(f"SELECT count(*) FROM {t}")).scalar_one() for t in tables
        }


# --- référence & mapping --------------------------------------------------------


def test_reference_add_and_get_source(make_uow: MakeUow) -> None:
    with make_uow() as uow:
        uow.reference.add_source(Source(name="tracelab", homepage_url="https://x"))
        uow.commit()
    with make_uow() as uow:
        got = uow.reference.get_source("tracelab")
        assert got == Source(name="tracelab", homepage_url="https://x")
        assert uow.reference.get_source("absent") is None


def test_upsert_code_repositories_is_idempotent(make_uow: MakeUow) -> None:
    repos = [Repository(source_name="tracelab", name="a/b")]
    with make_uow() as uow:
        uow.reference.add_source(Source(name="tracelab"))
        first = uow.reference.upsert_code_repositories("tracelab", repos)
        second = uow.reference.upsert_code_repositories("tracelab", repos)
        uow.commit()
    assert first == UpsertOutcome(inserted=1, skipped=0)
    assert second == UpsertOutcome(inserted=0, skipped=1)


def test_mapping_get_returns_latest_active(make_uow: MakeUow) -> None:
    with make_uow() as uow:
        uow.reference.add_source(Source(name="tracelab"))
        for version in (1, 2):
            uow.mappings.add(
                SourceMapping(
                    name="m",
                    version=version,
                    source_name="tracelab",
                    source_format=FileFormat.JSONL,
                    definition={"v": version},
                    created_at=NOW,
                )
            )
        uow.commit()
    with make_uow() as uow:
        latest = uow.mappings.get("m")
        assert latest is not None and latest.version == 2
        assert uow.mappings.get("m", version=1) is not None
        assert uow.mappings.get("m", version=1).version == 1  # type: ignore[union-attr]


# --- import_batch -----------------------------------------------------------------


def test_import_add_get_update_list_count(make_uow: MakeUow) -> None:
    with make_uow() as uow:
        uow.reference.add_source(Source(name="tracelab"))
        uow.mappings.add(
            SourceMapping(
                name="tracelab-jsonl",
                version=1,
                source_name="tracelab",
                source_format=FileFormat.JSONL,
                definition={"entities": {}},
                created_at=NOW,
            )
        )
        uow.imports.add(a_batch())
        uow.imports.update(
            ImportBatch(
                source_name="tracelab",
                original_filename="sessions.jsonl",
                file_sha256=SHA,
                file_format=FileFormat.JSONL,
                imported_at=NOW,
                status=ImportStatus.SUCCEEDED,
                mapping_name="tracelab-jsonl",
                imported_count=7,
                duplicate_count=2,
            )
        )
        uow.commit()
    with make_uow() as uow:
        got = uow.imports.get_by_file("tracelab", SHA)
        assert got is not None
        assert got.status is ImportStatus.SUCCEEDED
        assert got.imported_count == 7
        assert got.mapping_name == "tracelab-jsonl"
        assert uow.imports.count() == 1
        assert [b.file_sha256 for b in uow.imports.list_recent(10, 0)] == [SHA]
        assert uow.imports.get_by_file("tracelab", "other") is None


def test_import_add_without_active_mapping_raises(make_uow: MakeUow) -> None:
    with make_uow() as uow:
        uow.reference.add_source(Source(name="tracelab"))
        with pytest.raises(UnknownReferenceError):
            uow.imports.add(a_batch())


# --- enfants d'un import + résolution des FK -------------------------------------


def test_full_import_preserves_relations(make_uow: MakeUow, database: Database) -> None:
    seed_full(make_uow())

    with database.engine.connect() as conn:
        session_row = conn.execute(
            text(
                "SELECT s.id, s.external_id, s.repository_id, s.raw_record_id, "
                "s.import_batch_id, rr.record_index "
                "FROM session s JOIN raw_record rr ON rr.id = s.raw_record_id"
            )
        ).one()
        session_id, external_id, repository_id, raw_record_id, batch_id, rr_index = session_row
        assert external_id == "sess-1"
        assert rr_index == 0  # provenance.record_index respectée

        repo_name = conn.execute(
            text("SELECT name FROM repository WHERE id = :r"), {"r": repository_id}
        ).scalar_one()
        assert repo_name == "acme/widgets"

        mc = conn.execute(
            text(
                "SELECT id, session_id, import_batch_id, total_tokens "
                "FROM model_call WHERE sequence = 0"
            )
        ).one()
        mc_id, mc_session_id, mc_batch_id, total_tokens = mc
        assert mc_session_id == session_id
        assert mc_batch_id == batch_id
        assert total_tokens == 140  # dérivé prompt+completion, persisté

        tc = conn.execute(
            text("SELECT session_id, model_call_id, raw_record_id FROM tool_call")
        ).one()
        assert tc == (session_id, mc_id, raw_record_id + 1)  # rr index 1

        status = conn.execute(text("SELECT status FROM import_batch")).scalar_one()
        assert status == "succeeded"  # update() a bien pris


def test_reimport_same_file_creates_no_duplicate_rows(
    make_uow: MakeUow, database: Database
) -> None:
    seed_full(make_uow())
    before = row_counts(database)

    with make_uow() as uow:
        batch = a_batch()
        assert uow.imports.get_by_file("tracelab", SHA) is not None  # garde d'idempotence
        rr = uow.raw_records.upsert_many(batch, raw_records())
        ss = uow.sessions.upsert_many(batch, sessions())
        mc = uow.model_calls.upsert_many(batch, model_calls())
        tc = uow.tool_calls.upsert_many(batch, tool_calls())
        uow.commit()

    assert rr == UpsertOutcome(inserted=0, skipped=2)
    assert (ss.inserted, mc.inserted, tc.inserted) == (0, 0, 0)
    assert row_counts(database) == before


def test_model_call_without_parent_session_raises(make_uow: MakeUow) -> None:
    with make_uow() as uow:
        uow.reference.add_source(Source(name="tracelab"))
        uow.mappings.add(
            SourceMapping(
                name="tracelab-jsonl",
                version=1,
                source_name="tracelab",
                source_format=FileFormat.JSONL,
                definition={"entities": {}},
                created_at=NOW,
            )
        )
        batch = a_batch()
        uow.imports.add(batch)
        with pytest.raises(UnknownReferenceError):
            uow.model_calls.upsert_many(batch, model_calls())


# --- rejets & profils -----------------------------------------------------------


def test_rejects_add_list_count(make_uow: MakeUow) -> None:
    with make_uow() as uow:
        uow.reference.add_source(Source(name="tracelab"))
        uow.mappings.add(
            SourceMapping(
                name="tracelab-jsonl",
                version=1,
                source_name="tracelab",
                source_format=FileFormat.JSONL,
                definition={"entities": {}},
                created_at=NOW,
            )
        )
        batch = a_batch()
        uow.imports.add(batch)
        n = uow.rejects.add_many(
            batch,
            [
                ImportReject(
                    record_index=4,
                    reason=RejectReason.MISSING_REQUIRED_FIELD,
                    detail="model_name manquant",
                    payload={"raw": 1},
                )
            ],
        )
        uow.commit()
    assert n == 1
    with make_uow() as uow:
        assert uow.rejects.count_for_import("tracelab", SHA) == 1
        listed = uow.rejects.list_for_import("tracelab", SHA, 10, 0)
        assert listed[0].reason is RejectReason.MISSING_REQUIRED_FIELD
        assert listed[0].detail == "model_name manquant"


def test_field_profiles_upsert_idempotent(make_uow: MakeUow) -> None:
    profiles = [
        FieldProfile(
            path="usage.input_tokens",
            inferred_type="int",
            null_ratio=0.1,
            distinct_count=42,
            sample_values=(1, 2, 3),
        )
    ]
    with make_uow() as uow:
        uow.reference.add_source(Source(name="tracelab"))
        uow.mappings.add(
            SourceMapping(
                name="tracelab-jsonl",
                version=1,
                source_name="tracelab",
                source_format=FileFormat.JSONL,
                definition={"entities": {}},
                created_at=NOW,
            )
        )
        batch = a_batch()
        uow.imports.add(batch)
        first = uow.field_profiles.upsert_many(batch, profiles)
        second = uow.field_profiles.upsert_many(batch, profiles)
        uow.commit()
    assert (first.inserted, second.skipped) == (1, 1)


# --- UnitOfWork ---------------------------------------------------------------------


def test_uow_rollback_on_exception_leaves_db_empty(
    make_uow: MakeUow, database: Database
) -> None:
    with pytest.raises(RuntimeError, match="boom"), make_uow() as uow:
        uow.reference.add_source(Source(name="tracelab"))
        raise RuntimeError("boom")

    assert row_counts(database)["source"] == 0


def test_uow_without_commit_does_not_persist(
    make_uow: MakeUow, database: Database
) -> None:
    with make_uow() as uow:
        uow.reference.add_source(Source(name="tracelab"))
        # pas de commit

    assert row_counts(database)["source"] == 0
