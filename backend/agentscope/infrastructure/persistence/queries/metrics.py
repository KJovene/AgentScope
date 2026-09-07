"""Implémentation SQLAlchemy de ``MetricsQueryService`` (issue I1.9).

Lit ``v_session_metrics`` pour les indicateurs, la série temporelle et la liste
des sessions ; lit ``session`` + ``model_call`` + ``tool_call`` pour le détail.
"""

from __future__ import annotations

import statistics
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import bindparam, text
from sqlalchemy.engine import Row
from sqlalchemy.orm import Session

from agentscope.application.ports import (
    Granularity,
    Indicators,
    MetricFilter,
    Page,
    Paginated,
    SessionDetail,
    SessionListItem,
    TimelineEntry,
    TimeseriesMetric,
    TimeseriesPoint,
)
from agentscope.infrastructure.persistence.views import day_expr

_LIST_KEYS = ("sources", "agents", "models", "repositories")
_ERROR_STATUSES = ("error", "timeout")

_METRIC_AGG: dict[TimeseriesMetric, str] = {
    TimeseriesMetric.SESSIONS: "COUNT(*)",
    TimeseriesMetric.TOKENS: "SUM(total_tokens)",
    TimeseriesMetric.MODEL_CALLS: "SUM(n_model_calls)",
    TimeseriesMetric.TOOL_CALLS: "SUM(n_tool_calls)",
    TimeseriesMetric.COST: "SUM(total_cost_usd)",
    TimeseriesMetric.ERRORS: "SUM(n_errors)",
}


def _to_dt(value: Any) -> datetime | None:
    """Les lectures brutes de vues/tables renvoient un `str` ISO sur SQLite, un
    `datetime` sur PostgreSQL. On normalise en `datetime` UTC-aware."""
    if value is None:
        return None
    dt: datetime = datetime.fromisoformat(value) if isinstance(value, str) else value
    return dt if dt.tzinfo is not None else dt.replace(tzinfo=UTC)


def _duration_ms(start: datetime | None, end: datetime | None) -> int | None:
    if start is None or end is None:
        return None
    return int((end - start).total_seconds() * 1000)


def _int(value: Any) -> int:
    """PG renvoie `Decimal` pour un `SUM(bigint)` ; SQLite renvoie `int`."""
    return int(value)


def _opt_int(value: Any) -> int | None:
    return None if value is None else int(value)


def _opt_float(value: Any) -> float | None:
    return None if value is None else float(value)


def _ratio(numerator: float | None, denominator: float | None) -> float | None:
    if not denominator:  # None ou 0
        return None
    if numerator is None:
        return None
    return numerator / denominator


class SqlMetricsQueryService:
    def __init__(self, session: Session) -> None:
        self._s = session

    # -- construction de la clause WHERE (sur les colonnes de v_session_metrics) --

    def _where(self, filters: MetricFilter) -> tuple[str, dict[str, Any]]:
        conds: list[str] = []
        params: dict[str, Any] = {}
        if filters.sources:
            conds.append("source_name IN :sources")
            params["sources"] = list(filters.sources)
        if filters.agents:
            conds.append("agent_name IN :agents")
            params["agents"] = list(filters.agents)
        if filters.models:
            conds.append(
                "session_id IN (SELECT session_id FROM model_call WHERE model_name IN :models)"
            )
            params["models"] = list(filters.models)
        if filters.repositories:
            conds.append("repository_name IN :repositories")
            params["repositories"] = list(filters.repositories)
        if filters.date_from is not None:
            conds.append("started_at >= :date_from")
            params["date_from"] = filters.date_from
        if filters.date_to is not None:
            conds.append("started_at < :date_to")
            params["date_to"] = filters.date_to
        return (" AND ".join(conds) if conds else "1 = 1"), params

    def _execute(self, sql: str, params: dict[str, Any]) -> list[Row[Any]]:
        stmt = text(sql)
        expanding: list[Any] = [
            bindparam(k, expanding=True) for k in _LIST_KEYS if k in params
        ]
        if expanding:
            stmt = stmt.bindparams(*expanding)
        return list(self._s.execute(stmt, params))

    # -- indicateurs -----------------------------------------------------------

    def indicators(self, filters: MetricFilter) -> Indicators:
        where, params = self._where(filters)
        row = self._execute(
            f"""
            SELECT
                COUNT(*)                 AS session_count,
                COALESCE(SUM(n_model_calls), 0) AS model_call_count,
                COALESCE(SUM(n_tool_calls), 0)  AS tool_call_count,
                COALESCE(SUM(n_errors), 0)      AS error_count,
                SUM(total_tokens)        AS total_tokens,
                SUM(prompt_tokens)       AS prompt_tokens,
                SUM(completion_tokens)   AS completion_tokens,
                SUM(cached_tokens)       AS cached_tokens,
                SUM(total_cost_usd)      AS total_cost_usd
            FROM v_session_metrics
            WHERE {where}
            """,
            params,
        )[0]

        durations = [
            r[0]
            for r in self._execute(
                f"SELECT duration_ms FROM v_session_metrics "
                f"WHERE {where} AND duration_ms IS NOT NULL",
                params,
            )
        ]
        model_calls = _int(row.model_call_count)
        tool_calls = _int(row.tool_call_count)
        errors = _int(row.error_count)
        prompt = _opt_int(row.prompt_tokens)
        cached = _opt_int(row.cached_tokens)
        total_calls = model_calls + tool_calls
        return Indicators(
            session_count=_int(row.session_count),
            model_call_count=model_calls,
            tool_call_count=tool_calls,
            error_count=errors,
            total_tokens=_opt_int(row.total_tokens),
            prompt_tokens=prompt,
            completion_tokens=_opt_int(row.completion_tokens),
            cached_tokens=cached,
            total_cost_usd=_opt_float(row.total_cost_usd),
            error_rate=_ratio(errors, total_calls) if total_calls else None,
            cache_hit_ratio=_ratio(cached, prompt),
            median_session_duration_ms=(
                float(statistics.median(durations)) if durations else None
            ),
        )

    # -- série temporelle ----------------------------------------------------

    def timeseries(
        self,
        filters: MetricFilter,
        metric: TimeseriesMetric,
        granularity: Granularity = Granularity.DAY,
    ) -> list[TimeseriesPoint]:
        if granularity is not Granularity.DAY:
            raise NotImplementedError(f"granularité non supportée : {granularity}")
        where, params = self._where(filters)
        day = day_expr(self._s.get_bind().dialect.name, "started_at")
        rows = self._execute(
            f"""
            SELECT {day} AS period, {_METRIC_AGG[metric]} AS value
            FROM v_session_metrics
            WHERE {where} AND started_at IS NOT NULL
            GROUP BY {day}
            ORDER BY period
            """,
            params,
        )
        return [
            TimeseriesPoint(
                period=str(r.period),
                value=float(r.value) if r.value is not None else None,
            )
            for r in rows
        ]

    # -- liste des sessions -------------------------------------------------

    def sessions(
        self, filters: MetricFilter, page: Page
    ) -> Paginated[SessionListItem]:
        where, params = self._where(filters)
        total = self._execute(
            f"SELECT COUNT(*) AS n FROM v_session_metrics WHERE {where}", params
        )[0].n

        rows = self._execute(
            f"""
            SELECT session_id, source_name, agent_name, repository_name, started_at,
                   duration_ms, n_model_calls, n_tool_calls, total_tokens,
                   total_cost_usd, n_errors
            FROM v_session_metrics
            WHERE {where}
            ORDER BY (started_at IS NULL), started_at DESC, session_id DESC
            LIMIT :limit OFFSET :offset
            """,
            {**params, "limit": page.limit, "offset": page.offset},
        )
        items = tuple(
            SessionListItem(
                session_id=_int(r.session_id),
                source_name=r.source_name,
                agent_name=r.agent_name,
                repository_name=r.repository_name,
                started_at=_to_dt(r.started_at),
                duration_ms=_opt_int(r.duration_ms),
                model_call_count=_int(r.n_model_calls),
                tool_call_count=_int(r.n_tool_calls),
                total_tokens=_opt_int(r.total_tokens),
                total_cost_usd=_opt_float(r.total_cost_usd),
                error_count=_int(r.n_errors),
            )
            for r in rows
        )
        return Paginated(
            items=items, total=_int(total), limit=page.limit, offset=page.offset
        )

    # -- détail d'une session -----------------------------------------------

    def session_detail(self, session_id: int) -> SessionDetail | None:
        head = self._execute(
            """
            SELECT s.id, src.name AS source_name, s.external_id, s.agent_name,
                   r.name AS repository_name, s.started_at, s.ended_at, s.raw_record_id
            FROM session s
            JOIN source src ON src.id = s.source_id
            LEFT JOIN repository r ON r.id = s.repository_id
            WHERE s.id = :sid
            """,
            {"sid": session_id},
        )
        if not head:
            return None
        h = head[0]

        rows = self._execute(
            """
            SELECT * FROM (
                SELECT 'model_call' AS kind, sequence AS seq, model_name AS name,
                       status, error_type, started_at, ended_at,
                       prompt_tokens, completion_tokens, total_tokens, cost_usd
                FROM model_call WHERE session_id = :sid
                UNION ALL
                SELECT 'tool_call', sequence, tool_name, status, error_type,
                       started_at, ended_at, NULL, NULL, NULL, NULL
                FROM tool_call WHERE session_id = :sid
            ) timeline
            ORDER BY (started_at IS NULL), started_at, kind, seq
            """,
            {"sid": session_id},
        )

        timeline = tuple(_timeline_entry(r) for r in rows)
        started, ended = _to_dt(h.started_at), _to_dt(h.ended_at)
        token_values = [e.total_tokens for e in timeline if e.total_tokens is not None]
        cost_values = [e.cost_usd for e in timeline if e.cost_usd is not None]
        return SessionDetail(
            session_id=_int(h.id),
            source_name=h.source_name,
            external_id=h.external_id,
            agent_name=h.agent_name,
            repository_name=h.repository_name,
            started_at=started,
            ended_at=ended,
            duration_ms=_duration_ms(started, ended),
            total_tokens=sum(token_values) if token_values else None,
            total_cost_usd=sum(cost_values) if cost_values else None,
            error_count=sum(1 for e in timeline if e.status in _ERROR_STATUSES),
            has_raw_record=h.raw_record_id is not None,
            timeline=timeline,
        )


def _timeline_entry(r: Row[Any]) -> TimelineEntry:
    started, ended = _to_dt(r.started_at), _to_dt(r.ended_at)
    return TimelineEntry(
        kind=r.kind,
        sequence=r.seq,
        name=r.name,
        status=r.status,
        error_type=r.error_type,
        started_at=started,
        ended_at=ended,
        duration_ms=_duration_ms(started, ended),
        prompt_tokens=r.prompt_tokens,
        completion_tokens=r.completion_tokens,
        total_tokens=r.total_tokens,
        cost_usd=r.cost_usd,
    )
