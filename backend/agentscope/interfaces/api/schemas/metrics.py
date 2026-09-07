from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class Indicators(BaseModel):
    """Une valeur absente est `null`, jamais `0` (cf. §4 « Indicateurs »)."""

    sessions: int | None
    tokens_in: int | None
    tokens_out: int | None
    tokens_cached: int | None
    cost_usd: float | None
    median_session_duration_s: float | None
    error_rate: float | None
    cache_hit_rate: float | None


class Point(BaseModel):
    timestamp: datetime
    value: float | None


class ToolUsage(BaseModel):
    tool_name: str
    n_calls: int
    n_errors: int
    avg_duration_ms: float | None
