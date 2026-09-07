"""Vues agrégées du dashboard (issue I1.6).

DoD : les 4 vues existent et renvoient des lignes correctes sur un jeu de test,
en respectant « valeur absente = NULL, jamais 0 ».
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import inspect, text

from agentscope.domain import (
    CallStatus,
    ErrorType,
    FieldProfile,
    FileFormat,
    ImportBatch,
    ImportStatus,
    Interval,
    ModelCall,
    Provenance,
    RawRecord,
    Repository,
    Session,
    Source,
    SourceMapping,
    TokenUsage,
    ToolCall,
)
from agentscope.infrastructure.persistence.database import Database
from agentscope.infrastructure.persistence.unit_of_work import SqlAlchemyUnitOfWork
from agentscope.infrastructure.persistence.views import VIEW_NAMES

DAY = datetime(2026, 3, 1, 10, 0, 0, tzinfo=UTC)
SHA = "SHA-VIEWS"
MakeUow = Callable[[], SqlAlchemyUnitOfWork]


def _prov(index: int) -> Provenance:
    return Provenance(record_index=index, record_sha256=f"rr-{index}")


def seed(uow: SqlAlchemyUnitOfWork) -> None:
    with uow:
        uow.reference.add_source(Source(name="tracelab"))
        uow.reference.upsert_code_repositories(
            "tracelab", [Repository(source_name="tracelab", name="acme/app")]
        )
        uow.mappings.add(
            SourceMapping(
                name="tracelab-jsonl",
                version=1,
                source_name="tracelab",
                source_format=FileFormat.JSONL,
                definition={"entities": {}},
                created_at=DAY,
            )
        )
        batch = ImportBatch(
            source_name="tracelab",
            original_filename="s.jsonl",
            file_sha256=SHA,
            file_format=FileFormat.JSONL,
            imported_at=DAY,
            status=ImportStatus.SUCCEEDED,
            mapping_name="tracelab-jsonl",
            record_count=10,
            imported_count=8,
            duplicate_count=0,
            rejected_count=1,
            missing_info_count=2,
        )
        uow.imports.add(batch)

        uow.raw_records.upsert_many(
            batch, [RawRecord(index=i, payload={}, sha256=f"rr-{i}") for i in (0, 1)]
        )

        uow.sessions.upsert_many(
            batch,
            [
                Session(
                    source_name="tracelab",
                    external_id="sess-A",
                    provenance=_prov(0),
                    agent_name="claude",
                    interval=Interval(started_at=DAY, ended_at=DAY + timedelta(seconds=2)),
                    repository_name="acme/app",
                ),
                Session(
                    source_name="tracelab",
                    external_id="sess-B",  # sans timings -> exclue de v_daily_activity
                    provenance=_prov(1),
                    agent_name="codex",
                ),
            ],
        )

        uow.model_calls.upsert_many(
            batch,
            [
                ModelCall(
                    source_name="tracelab",
                    session_external_id="sess-A",
                    sequence=0,
                    model_name="claude-sonnet",
                    provenance=_prov(0),
                    tokens=TokenUsage(prompt_tokens=100, completion_tokens=40, cached_tokens=20),
                    cost_usd=0.5,
                    status=CallStatus.SUCCESS,
                ),
                ModelCall(
                    source_name="tracelab",
                    session_external_id="sess-A",
                    sequence=1,
                    model_name="claude-sonnet",
                    provenance=_prov(0),
                    tokens=TokenUsage(prompt_tokens=50, completion_tokens=0),
                    status=CallStatus.ERROR,
                    error_type=ErrorType.MODEL_ERROR,
                ),
            ],
        )

        uow.tool_calls.upsert_many(
            batch,
            [
                ToolCall(
                    source_name="tracelab",
                    session_external_id="sess-A",
                    sequence=0,
                    tool_name="bash",
                    provenance=_prov(0),
                    interval=Interval(started_at=DAY, ended_at=DAY + timedelta(milliseconds=500)),
                    status=CallStatus.SUCCESS,
                ),
                ToolCall(
                    source_name="tracelab",
                    session_external_id="sess-A",
                    sequence=1,
                    tool_name="bash",
                    provenance=_prov(0),
                    status=CallStatus.ERROR,
                    error_type=ErrorType.TOOL_ERROR,
                ),
            ],
        )

        uow.field_profiles.upsert_many(
            batch,
            [
                FieldProfile(path="a", inferred_type="int", null_ratio=0.0, distinct_count=5),
                FieldProfile(path="b", inferred_type="str", null_ratio=0.5, distinct_count=3),
            ],
        )
        uow.commit()


@pytest.fixture
def seeded(make_uow: MakeUow, database: Database) -> Database:
    seed(make_uow())
    return database


def _rows(database: Database, sql: str) -> list[dict[str, object]]:
    with database.engine.connect() as conn:
        result = conn.execute(text(sql))
        return [dict(r) for r in result.mappings()]


def test_all_four_views_exist(database: Database) -> None:
    view_names = set(inspect(database.engine).get_view_names())
    assert set(VIEW_NAMES) <= view_names


def test_session_metrics(seeded: Database) -> None:
    rows = {r["session_id"]: r for r in _rows(seeded, "SELECT * FROM v_session_metrics")}
    assert len(rows) == 2

    a = next(r for r in rows.values() if r["n_model_calls"] == 2)
    assert a["source_name"] == "tracelab"
    assert a["duration_ms"] == 2000
    assert a["n_tool_calls"] == 2
    assert a["total_tokens"] == 190  # 140 + 50
    assert a["prompt_tokens"] == 150
    assert a["cached_tokens"] == 20
    assert abs(float(a["cache_hit_ratio"]) - 20 / 150) < 1e-9
    assert abs(float(a["total_cost_usd"]) - 0.5) < 1e-9
    assert a["n_errors"] == 2  # 1 model + 1 tool

    b = next(r for r in rows.values() if r["n_model_calls"] == 0)
    assert b["total_tokens"] is None  # NULL, pas 0
    assert b["duration_ms"] is None
    assert b["n_tool_calls"] == 0
    assert b["cache_hit_ratio"] is None


def test_daily_activity_excludes_sessions_without_start(seeded: Database) -> None:
    rows = _rows(seeded, "SELECT * FROM v_daily_activity")
    assert len(rows) == 1
    row = rows[0]
    assert str(row["day"]).startswith("2026-03-01")
    assert row["n_sessions"] == 1  # sess-B (sans started_at) exclue
    assert row["n_model_calls"] == 2
    assert row["n_tool_calls"] == 2
    assert row["total_tokens"] == 190


def test_tool_usage(seeded: Database) -> None:
    rows = _rows(seeded, "SELECT * FROM v_tool_usage")
    assert len(rows) == 1
    row = rows[0]
    assert (row["source_name"], row["tool_name"]) == ("tracelab", "bash")
    assert row["n_calls"] == 2
    assert row["n_errors"] == 1
    assert abs(float(row["error_rate"]) - 0.5) < 1e-9
    assert row["avg_duration_ms"] == 500  # seul le 1er appel est chronométré


def test_data_quality(seeded: Database) -> None:
    rows = _rows(seeded, "SELECT * FROM v_data_quality")
    assert len(rows) == 1
    row = rows[0]
    assert row["source_name"] == "tracelab"
    assert row["record_count"] == 10
    assert row["imported_count"] == 8
    assert abs(float(row["completeness_ratio"]) - 0.8) < 1e-9
    assert row["n_profiled_fields"] == 2
    assert abs(float(row["avg_null_ratio"]) - 0.25) < 1e-9


def test_completeness_ratio_is_null_when_record_count_missing(
    make_uow: MakeUow, database: Database
) -> None:
    with make_uow() as uow:
        uow.reference.add_source(Source(name="s"))
        uow.mappings.add(
            SourceMapping(
                name="m",
                version=1,
                source_name="s",
                source_format=FileFormat.JSONL,
                definition={"e": 1},
                created_at=DAY,
            )
        )
        uow.imports.add(
            ImportBatch(
                source_name="s",
                original_filename="f.jsonl",
                file_sha256="NO-COUNT",
                file_format=FileFormat.JSONL,
                imported_at=DAY,
                mapping_name="m",
            )
        )
        uow.commit()

    row = _rows(database, "SELECT * FROM v_data_quality WHERE file_sha256 = 'NO-COUNT'")[0]
    assert row["completeness_ratio"] is None  # record_count NULL -> NULL, pas 0
