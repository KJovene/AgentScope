"""Services de lecture ``SqlSourcesQueryService`` / ``SqlDataQualityQueryService``
et ``SqlMetricsQueryService.tool_usage`` — lus contre une base SQLite migrée.
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime, timedelta

import pytest

from agentscope.application.ports.metrics import MetricFilter
from agentscope.domain import (
    CallStatus,
    ErrorType,
    FileFormat,
    ImportBatch,
    ImportStatus,
    Interval,
    Provenance,
    RawRecord,
    Session,
    Source,
    SourceMapping,
    ToolCall,
)
from agentscope.infrastructure.persistence.database import Database
from agentscope.infrastructure.persistence.queries import (
    SqlDataQualityQueryService,
    SqlMetricsQueryService,
    SqlSourcesQueryService,
)
from agentscope.infrastructure.persistence.unit_of_work import SqlAlchemyUnitOfWork

D1 = datetime(2026, 5, 1, 10, 0, 0, tzinfo=UTC)
MakeUow = Callable[[], SqlAlchemyUnitOfWork]


def _prov(i: int) -> Provenance:
    return Provenance(record_index=i, record_sha256=f"rr-{i}")


@pytest.fixture
def seeded(make_uow: MakeUow, database: Database) -> Database:
    with make_uow() as uow:
        uow.reference.add_source(Source(name="tracelab", display_name="TraceLab"))
        uow.reference.add_source(Source(name="swe-chat", display_name="SWE-chat"))
        uow.mappings.add(
            SourceMapping(
                name="m",
                version=1,
                source_name="tracelab",
                source_format=FileFormat.JSONL,
                definition={"e": 1},
                created_at=D1,
            )
        )
        batch = ImportBatch(
            source_name="tracelab",
            original_filename="s.jsonl",
            file_sha256="SHA-DQ",
            file_format=FileFormat.JSONL,
            imported_at=D1,
            status=ImportStatus.SUCCEEDED,
            mapping_name="m",
            record_count=4,
            imported_count=3,
            duplicate_count=1,
            rejected_count=1,
            missing_info_count=2,
        )
        uow.imports.add(batch)
        uow.raw_records.upsert_many(
            batch, [RawRecord(index=i, payload={"i": i}, sha256=f"rr-{i}") for i in (0, 1)]
        )
        uow.sessions.upsert_many(
            batch,
            [
                Session(
                    source_name="tracelab",
                    external_id="S1",
                    provenance=_prov(0),
                    agent_name="claude",
                    interval=Interval(started_at=D1, ended_at=D1 + timedelta(seconds=2)),
                ),
                Session(
                    source_name="tracelab",
                    external_id="S2",
                    provenance=_prov(1),
                    agent_name="codex",
                ),
            ],
        )
        uow.tool_calls.upsert_many(
            batch,
            [
                ToolCall(
                    source_name="tracelab",
                    session_external_id="S1",
                    sequence=0,
                    tool_name="bash",
                    provenance=_prov(0),
                    interval=Interval(
                        started_at=D1, ended_at=D1 + timedelta(milliseconds=800)
                    ),
                    status=CallStatus.SUCCESS,
                ),
                ToolCall(
                    source_name="tracelab",
                    session_external_id="S1",
                    sequence=1,
                    tool_name="bash",
                    provenance=_prov(0),
                    status=CallStatus.ERROR,
                    error_type=ErrorType.TOOL_ERROR,
                ),
            ],
        )
        uow.commit()
    return database


def test_list_sources_with_session_counts(seeded: Database) -> None:
    svc = SqlSourcesQueryService(seeded.create_session())
    sources = svc.list_sources()

    by_name = {s.name: s for s in sources}
    assert set(by_name) == {"tracelab", "swe-chat"}
    assert by_name["tracelab"].description == "TraceLab"
    assert by_name["tracelab"].session_count == 2
    assert by_name["swe-chat"].session_count == 0


def test_data_quality_metrics_from_view(seeded: Database) -> None:
    svc = SqlDataQualityQueryService(seeded.create_session())
    batches = svc.get_quality_metrics()

    assert len(batches) == 1
    b = batches[0]
    assert b.source_name == "tracelab"
    assert (b.imported_count, b.duplicate_count, b.rejected_count) == (3, 1, 1)
    assert b.missing_info_count == 2
    assert b.completeness_rate == pytest.approx(3 / 4)

    assert svc.get_quality_metrics(source_id="tracelab") == batches
    assert svc.get_quality_metrics(source_id="inconnue") == []


def test_tool_usage_aggregates_and_filters(seeded: Database) -> None:
    svc = SqlMetricsQueryService(seeded.create_session())

    rows = svc.tool_usage(MetricFilter())
    assert rows == [
        {"tool_name": "bash", "n_calls": 2, "n_errors": 1, "avg_duration_ms": pytest.approx(800.0)}
    ]

    assert svc.tool_usage(MetricFilter(sources=("tracelab",))) == rows
    assert svc.tool_usage(MetricFilter(sources=("swe-chat",))) == []
