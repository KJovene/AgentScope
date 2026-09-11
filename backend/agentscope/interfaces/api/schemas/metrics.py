from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from agentscope.application.ports.metrics import Granularity, TimeseriesMetric


class IndicatorsResponse(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    session_count: int = Field(description="Nombre total de sessions")
    model_call_count: int
    tool_call_count: int
    error_count: int
    total_tokens: int | None = Field(default=None, description="null si indisponible")
    prompt_tokens: int | None = Field(default=None)
    completion_tokens: int | None = Field(default=None)
    cached_tokens: int | None = Field(default=None)
    total_cost_usd: float | None = Field(default=None)
    cost_is_estimated: bool = Field(
        default=False,
        description="true si un coût du périmètre est estimé (tarif) et non déclaré par la source",
    )
    error_rate: float | None = Field(default=None)
    cache_hit_ratio: float | None = Field(default=None)
    median_session_duration_ms: float | None = Field(default=None)


class TimeseriesPointResponse(BaseModel):
    period: str
    value: float | None = Field(default=None)


class TimeseriesResponse(BaseModel):
    metric: TimeseriesMetric
    granularity: Granularity
    points: list[TimeseriesPointResponse]


class ToolUsageResponseItem(BaseModel):
    tool_name: str
    n_calls: int
    n_errors: int
    avg_duration_ms: float | None = Field(default=None)


class FilterDimensionsResponse(BaseModel):
    """Valeurs distinctes disponibles pour les filtres à choix fermé du dashboard."""

    agents: list[str] = Field(default_factory=list)
    models: list[str] = Field(default_factory=list)
