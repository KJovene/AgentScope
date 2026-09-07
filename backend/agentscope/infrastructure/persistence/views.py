"""Vues agrégées du dashboard (issue I1.6).

Définies en SQL car ce sont des vues de base de données, recalculées à la volée
(cf. `docs/data/relational-model.md` §4). Le SQL est majoritairement portable ;
seules l'expression de durée et l'extraction du jour diffèrent entre SQLite et
PostgreSQL.

Règles respectées :
- une valeur non fournie reste `NULL` (jamais `0`) — `NULLIF(dénominateur, 0)`
  et `LEFT JOIN` sur des agrégats pré-calculés ;
- un vrai comptage nul (`n_model_calls` d'une session sans appel) est `0`.
"""

from __future__ import annotations

from sqlalchemy import Connection, text

VIEW_NAMES: tuple[str, ...] = (
    "v_session_metrics",
    "v_daily_activity",
    "v_tool_usage",
    "v_data_quality",
)

_ERROR_STATUSES = "('error', 'timeout')"


def _duration_ms(dialect: str, start: str, end: str) -> str:
    if dialect == "sqlite":
        return f"CAST((julianday({end}) - julianday({start})) * 86400000.0 AS INTEGER)"
    return f"CAST(EXTRACT(EPOCH FROM ({end} - {start})) * 1000 AS BIGINT)"


def _day(dialect: str, column: str) -> str:
    # SQLite : CAST(... AS DATE) tomberait en affinité numérique -> fonction date().
    return f"date({column})" if dialect == "sqlite" else f"CAST({column} AS date)"


def build_view_statements(dialect: str) -> dict[str, str]:
    dur_session = _duration_ms(dialect, "s.started_at", "s.ended_at")
    dur_tool = _duration_ms(dialect, "tc.started_at", "tc.ended_at")
    day = _day(dialect, "s.started_at")
    err = _ERROR_STATUSES

    model_agg = f"""
        SELECT
            session_id,
            COUNT(*) AS n_model_calls,
            SUM(total_tokens) AS total_tokens,
            SUM(prompt_tokens) AS prompt_tokens,
            SUM(completion_tokens) AS completion_tokens,
            SUM(cached_tokens) AS cached_tokens,
            SUM(cost_usd) AS total_cost_usd,
            SUM(CASE WHEN status IN {err} THEN 1 ELSE 0 END) AS n_model_errors
        FROM model_call
        GROUP BY session_id
    """
    tool_agg = f"""
        SELECT
            session_id,
            COUNT(*) AS n_tool_calls,
            SUM(CASE WHEN status IN {err} THEN 1 ELSE 0 END) AS n_tool_errors
        FROM tool_call
        GROUP BY session_id
    """

    return {
        "v_session_metrics": f"""
            CREATE VIEW v_session_metrics AS
            SELECT
                s.id AS session_id,
                src.name AS source_name,
                s.agent_name AS agent_name,
                s.started_at AS started_at,
                s.ended_at AS ended_at,
                s.import_batch_id AS import_batch_id,
                CASE
                    WHEN s.started_at IS NOT NULL AND s.ended_at IS NOT NULL
                    THEN {dur_session}
                END AS duration_ms,
                COALESCE(m.n_model_calls, 0) AS n_model_calls,
                COALESCE(t.n_tool_calls, 0) AS n_tool_calls,
                m.total_tokens AS total_tokens,
                m.prompt_tokens AS prompt_tokens,
                m.completion_tokens AS completion_tokens,
                m.cached_tokens AS cached_tokens,
                CAST(m.cached_tokens AS REAL) / NULLIF(m.prompt_tokens, 0) AS cache_hit_ratio,
                m.total_cost_usd AS total_cost_usd,
                COALESCE(m.n_model_errors, 0) + COALESCE(t.n_tool_errors, 0) AS n_errors
            FROM session s
            JOIN source src ON src.id = s.source_id
            LEFT JOIN ({model_agg}) m ON m.session_id = s.id
            LEFT JOIN ({tool_agg}) t ON t.session_id = s.id
        """,
        "v_daily_activity": f"""
            CREATE VIEW v_daily_activity AS
            SELECT
                src.name AS source_name,
                {day} AS day,
                COUNT(DISTINCT s.id) AS n_sessions,
                COALESCE(SUM(m.n_model_calls), 0) AS n_model_calls,
                COALESCE(SUM(t.n_tool_calls), 0) AS n_tool_calls,
                SUM(m.total_tokens) AS total_tokens
            FROM session s
            JOIN source src ON src.id = s.source_id
            LEFT JOIN ({model_agg}) m ON m.session_id = s.id
            LEFT JOIN ({tool_agg}) t ON t.session_id = s.id
            WHERE s.started_at IS NOT NULL
            GROUP BY src.name, {day}
        """,
        "v_tool_usage": f"""
            CREATE VIEW v_tool_usage AS
            SELECT
                src.name AS source_name,
                tc.tool_name AS tool_name,
                COUNT(*) AS n_calls,
                SUM(CASE WHEN tc.status IN {err} THEN 1 ELSE 0 END) AS n_errors,
                CAST(SUM(CASE WHEN tc.status IN {err} THEN 1 ELSE 0 END) AS REAL)
                    / NULLIF(COUNT(*), 0) AS error_rate,
                AVG(
                    CASE
                        WHEN tc.started_at IS NOT NULL AND tc.ended_at IS NOT NULL
                        THEN {dur_tool}
                    END
                ) AS avg_duration_ms
            FROM tool_call tc
            JOIN session s ON s.id = tc.session_id
            JOIN source src ON src.id = s.source_id
            GROUP BY src.name, tc.tool_name
        """,
        "v_data_quality": """
            CREATE VIEW v_data_quality AS
            SELECT
                ib.id AS import_batch_id,
                src.name AS source_name,
                ib.file_sha256 AS file_sha256,
                ib.status AS status,
                ib.imported_at AS imported_at,
                ib.record_count AS record_count,
                ib.imported_count AS imported_count,
                ib.duplicate_count AS duplicate_count,
                ib.rejected_count AS rejected_count,
                ib.missing_info_count AS missing_info_count,
                CAST(ib.imported_count AS REAL) / NULLIF(ib.record_count, 0)
                    AS completeness_ratio,
                COALESCE(fp.n_profiled_fields, 0) AS n_profiled_fields,
                fp.avg_null_ratio AS avg_null_ratio
            FROM import_batch ib
            JOIN source src ON src.id = ib.source_id
            LEFT JOIN (
                SELECT
                    import_batch_id,
                    COUNT(*) AS n_profiled_fields,
                    AVG(null_ratio) AS avg_null_ratio
                FROM field_profile
                GROUP BY import_batch_id
            ) fp ON fp.import_batch_id = ib.id
        """,
    }


def create_all_views(connection: Connection) -> None:
    dialect = connection.dialect.name
    for statement in build_view_statements(dialect).values():
        connection.execute(text(statement))


def drop_all_views(connection: Connection) -> None:
    for name in reversed(VIEW_NAMES):
        connection.execute(text(f"DROP VIEW IF EXISTS {name}"))
