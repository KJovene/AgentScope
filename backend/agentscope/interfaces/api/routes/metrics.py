from __future__ import annotations

import dataclasses
from datetime import datetime
import logging
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query, status

from agentscope.application.ports.metrics import (
    Granularity,
    MetricFilter,
    MetricsQueryService,
    TimeseriesMetric,
)
from agentscope.interfaces.api.dependencies import MetricsServiceDep
from agentscope.interfaces.api.schemas.metrics import (
    IndicatorsResponse,
    TimeseriesPointResponse,
    TimeseriesResponse,
    ToolUsageResponseItem,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/metrics", tags=["metrics"])


def parse_metric_filter(
    sources: list[str] = Query(default=[]),
    agents: list[str] = Query(default=[]),
    models: list[str] = Query(default=[]),
    repositories: list[str] = Query(default=[]),
    date_from: datetime | None = Query(default=None, alias="from"),
    date_to: datetime | None = Query(default=None, alias="to"),
) -> MetricFilter:
    return MetricFilter(
        sources=tuple(sources),
        agents=tuple(agents),
        models=tuple(models),
        repositories=tuple(repositories),
        date_from=date_from,
        date_to=date_to,
    )


FilterDep = Annotated[MetricFilter, Depends(parse_metric_filter)]


def _to_dict_safe(obj: Any) -> dict[str, Any]:
    if isinstance(obj, dict):
        return obj
    if dataclasses.is_dataclass(obj) and not isinstance(obj, type):
        return {k: getattr(obj, k) for k in obj.__dataclass_fields__}
    if hasattr(obj, "__dict__"):
        return {k: v for k, v in obj.__dict__.items() if not k.startswith("_")}
    return {}


def _map_indicators(obj: Any) -> dict[str, Any]:
    d = _to_dict_safe(obj)
    return {
        "session_count": d.get("session_count") if d.get("session_count") is not None else d.get("n_sessions", 0),
        "model_call_count": d.get("model_call_count") if d.get("model_call_count") is not None else d.get("n_model_calls", 0),
        "tool_call_count": d.get("tool_call_count") if d.get("tool_call_count") is not None else d.get("n_tool_calls", 0),
        "error_count": d.get("error_count") if d.get("error_count") is not None else d.get("n_errors", 0),
        "total_tokens": d.get("total_tokens"),
        "prompt_tokens": d.get("prompt_tokens"),
        "completion_tokens": d.get("completion_tokens"),
        "cached_tokens": d.get("cached_tokens"),
        "total_cost_usd": d.get("total_cost_usd"),
        "cost_is_estimated": bool(d.get("cost_is_estimated", False)),
        "error_rate": d.get("error_rate"),
        "cache_hit_ratio": d.get("cache_hit_ratio"),
        "median_session_duration_ms": d.get("median_session_duration_ms"),
    }


@router.get("/indicators", response_model=IndicatorsResponse)
async def get_indicators(
    filters: FilterDep,
    service: MetricsServiceDep,
) -> IndicatorsResponse:
    try:
        indicators_obj = service.indicators(filters)
        return IndicatorsResponse(**_map_indicators(indicators_obj))
    except Exception as exc:
        logger.exception("Erreur lors du calcul des indicateurs métriques")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur métriques [{type(exc).__name__}]: {exc}",
        )


@router.get("/timeseries", response_model=TimeseriesResponse)
async def get_timeseries(
    filters: FilterDep,
    service: MetricsServiceDep,
    metric: TimeseriesMetric = Query(default=TimeseriesMetric.SESSIONS),
    granularity: Granularity = Query(default=Granularity.DAY),
) -> TimeseriesResponse:
    points = service.timeseries(filters, metric=metric, granularity=granularity)
    return TimeseriesResponse(
        metric=metric,
        granularity=granularity,
        points=[TimeseriesPointResponse(**_to_dict_safe(pt)) for pt in points],
    )


@router.get("/tool-usage", response_model=list[ToolUsageResponseItem])
async def get_tool_usage(
    filters: FilterDep,
    service: MetricsServiceDep,
) -> list[ToolUsageResponseItem]:
    items = service.tool_usage(filters)
    return [ToolUsageResponseItem(**_to_dict_safe(item)) for item in items]
