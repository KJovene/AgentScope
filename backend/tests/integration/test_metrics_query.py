"""MetricsQueryService : lecture des vues du dashboard (issue I1.9).

DoD : indicators() / timeseries() / sessions() / session_detail() testés.
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import text

from agentscope.application.ports import (
    MetricFilter,
    Page,
    TimeseriesMetric,
)
from agentscope.domain import (
    CallStatus,
    ErrorType,
    FileFormat,
    ImportBatch,
    ImportStatus,
    Interval,
    ModelCall,
    Provenance,
    RawRecord,
    Session,
    Source,
    SourceMapping,
    ToolCall,
)
from agentscope.infrastructure.persistence.database import Database
from agentscope.infrastructure.persistence.queries import SqlMetricsQueryService
from agentscope.infrastructure.persistence.unit_of_work import SqlAlchemyUnitOfWork

D1 = datetime(2026, 5, 1, 10, 0, 0, tzinfo=UTC)
D2 = datetime(2026, 5, 2, 10, 0, 0, tzinfo=UTC)
MakeUow = Callable[[], SqlAlchemyUnitOfWork]


def _prov(i: int) -> Provenance:
    return Provenance(record_index=i, record_sha256=f"rr-{i}")


def _mc(
    ext: str,
    seq: int,
    model: str,
    *,
    prompt: int | None = None,
    completion: int | None = None,
    cached: int | None = None,
    cost: float | None = None,
    start: datetime | None = None,
    end: datetime | None = None,
    error: bool = False,
) -> ModelCall:
    from agentscope.domain import TokenUsage

    return ModelCall(
        source_name="tracelab",
        session_external_id=ext,
        sequence=seq,
        model_name=model,
        provenance=_prov(0),
        tokens=TokenUsage(prompt_tokens=prompt, completion_tokens=completion, cached_tokens=cached),
        cost_usd=cost,
        interval=Interval(started_at=start, ended_at=end),
        status=CallStatus.ERROR if error else CallStatus.SUCCESS,
        error_type=ErrorType.MODEL_ERROR if error else None,
    )


@pytest.fixture
def svc(make_uow: MakeUow, database: Database) -> SqlMetricsQueryService:
    with make_uow() as uow:
        uow.reference.add_source(Source(name="tracelab"))
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
            file_sha256="SHA-MQ",
            file_format=FileFormat.JSONL,
            imported_at=D1,
            status=ImportStatus.SUCCEEDED,
            mapping_name="m",
            record_count=3,
        )
        uow.imports.add(batch)
        uow.raw_records.upsert_many(
            batch, [RawRecord(index=i, payload={"i": i}, sha256=f"rr-{i}") for i in (0, 1, 2)]
        )
        uow.sessions.upsert_many(
            batch,
            [
                Session(
                    source_name="tracelab",
                    external_id="S1",
                    provenance=_prov(0),
                    agent_name="claude",
                    interval=Interval(started_at=D1, ended_at=D1 + timedelta(seconds=3)),
                ),
                Session(
                    source_name="tracelab",
                    external_id="S2",
                    provenance=_prov(1),
                    agent_name="codex",
                    interval=Interval(started_at=D2, ended_at=D2 + timedelta(seconds=1)),
                ),
                Session(
                    source_name="tracelab",
                    external_id="S3",
                    provenance=_prov(2),
                    agent_name="claude",
                ),
            ],
        )
        uow.model_calls.upsert_many(
            batch,
            [
                _mc(
                    "S1",
                    0,
                    "claude-sonnet",
                    prompt=100,
                    completion=40,
                    cached=20,
                    cost=0.5,
                    start=D1,
                    end=D1 + timedelta(seconds=1),
                ),
                _mc("S1", 1, "claude-sonnet", prompt=50, error=True),
                _mc(
                    "S2",
                    0,
                    "gpt-4o",
                    prompt=200,
                    completion=60,
                    start=D2,
                    end=D2 + timedelta(seconds=1),
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
                        started_at=D1 + timedelta(milliseconds=500),
                        ended_at=D1 + timedelta(milliseconds=1300),
                    ),
                    status=CallStatus.SUCCESS,
                )
            ],
        )
        uow.commit()
    return SqlMetricsQueryService(database.create_session())


def _session_id(database: Database, external_id: str) -> int:
    with database.engine.connect() as conn:
        return conn.execute(
            text("SELECT id FROM session WHERE external_id = :e"), {"e": external_id}
        ).scalar_one()


# --- indicators -------------------------------------------------------------


def test_indicators_no_filter(svc: SqlMetricsQueryService) -> None:
    ind = svc.indicators(MetricFilter())
    assert ind.session_count == 3
    assert ind.model_call_count == 3
    assert ind.tool_call_count == 1
    assert ind.error_count == 1
    assert ind.total_tokens == 450
    assert ind.prompt_tokens == 350
    assert ind.completion_tokens == 100
    assert ind.cached_tokens == 20
    assert ind.total_cost_usd == pytest.approx(0.5)
    assert ind.error_rate == pytest.approx(1 / 4)
    assert ind.cache_hit_ratio == pytest.approx(20 / 350)
    assert ind.median_session_duration_ms == 2000.0  # médiane de [3000, 1000]


def test_indicators_missing_data_is_none_not_zero(svc: SqlMetricsQueryService) -> None:
    ind = svc.indicators(MetricFilter(agents=("nobody",)))
    assert ind.session_count == 0
    assert ind.total_tokens is None
    assert ind.total_cost_usd is None
    assert ind.error_rate is None
    assert ind.cache_hit_ratio is None
    assert ind.median_session_duration_ms is None
    assert ind.model_call_count == 0  # vrai comptage nul


def test_indicators_filtered_by_model(svc: SqlMetricsQueryService) -> None:
    ind = svc.indicators(MetricFilter(models=("gpt-4o",)))
    assert ind.session_count == 1  # seule S2
    assert ind.total_tokens == 260


# --- timeseries -----------------------------------------------------------


def test_timeseries_sessions_per_day(svc: SqlMetricsQueryService) -> None:
    points = svc.timeseries(MetricFilter(), TimeseriesMetric.SESSIONS)
    assert [(p.period, p.value) for p in points] == [
        ("2026-05-01", 1.0),
        ("2026-05-02", 1.0),
    ]  # S3 (sans started_at) exclue


def test_timeseries_tokens_per_day(svc: SqlMetricsQueryService) -> None:
    points = svc.timeseries(MetricFilter(), TimeseriesMetric.TOKENS)
    assert {p.period: p.value for p in points} == {
        "2026-05-01": 190.0,
        "2026-05-02": 260.0,
    }


# --- sessions -----------------------------------------------------------------


def test_sessions_pagination_and_order(svc: SqlMetricsQueryService) -> None:
    page = svc.sessions(MetricFilter(), Page(limit=2, offset=0))
    assert page.total == 3
    assert [i.source_name for i in page.items] == ["tracelab", "tracelab"]
    # tri : started_at DESC, NULL en dernier -> S2 (05-02) puis S1 (05-01)
    assert page.items[0].agent_name == "codex"
    assert page.items[0].total_tokens == 260
    assert page.items[1].agent_name == "claude"

    page2 = svc.sessions(MetricFilter(), Page(limit=2, offset=2))
    assert len(page2.items) == 1
    assert page2.items[0].started_at is None  # S3
    assert page2.items[0].total_tokens is None


def test_sessions_filtered_by_agent(svc: SqlMetricsQueryService) -> None:
    page = svc.sessions(MetricFilter(agents=("codex",)), Page())
    assert page.total == 1
    assert page.items[0].agent_name == "codex"


def test_sessions_filtered_by_date_from(svc: SqlMetricsQueryService) -> None:
    page = svc.sessions(MetricFilter(date_from=D2), Page())
    assert [i.agent_name for i in page.items] == ["codex"]  # S1 trop tôt, S3 sans date


# --- session_detail ------------------------------------------------------------


def test_session_detail_timeline_and_aggregates(
    svc: SqlMetricsQueryService, database: Database
) -> None:
    detail = svc.session_detail(_session_id(database, "S1"))
    assert detail is not None
    assert detail.external_id == "S1"
    assert detail.duration_ms == 3000
    assert detail.total_tokens == 190  # 140 + 50
    assert detail.total_cost_usd == pytest.approx(0.5)
    assert detail.error_count == 1
    assert detail.has_raw_record is True

    kinds = [(e.kind, e.sequence) for e in detail.timeline]
    assert kinds == [("model_call", 0), ("tool_call", 0), ("model_call", 1)]
    assert detail.timeline[0].total_tokens == 140
    assert detail.timeline[0].duration_ms == 1000
    assert detail.timeline[2].status == "error"
    assert detail.timeline[2].error_type == "model_error"


def test_session_detail_unknown_id_returns_none(svc: SqlMetricsQueryService) -> None:
    assert svc.session_detail(999_999) is None
