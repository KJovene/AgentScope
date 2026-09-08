from __future__ import annotations

import dataclasses
from datetime import datetime
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Query

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


def _to_dict(obj: Any) -> dict[str, Any]:
    if isinstance(obj, dict):
        return obj
    if dataclasses.is_dataclass(obj) and not isinstance(obj, type):
        return dataclasses.asdict(obj)
    if hasattr(obj, "__dict__"):
        return obj.__dict__
    raise TypeError(f"Impossible de convertir {type(obj)} en dictionnaire")


@router.get("/indicators", response_model=IndicatorsResponse)
async def get_indicators(
    filters: FilterDep,
    service: MetricsServiceDep,
) -> IndicatorsResponse:
    indicators_obj = service.indicators(filters)
    return IndicatorsResponse(**_to_dict(indicators_obj))


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
        points=[
            TimeseriesPointResponse(**_to_dict(pt)) for pt in points
        ],
    )


@router.get("/tool-usage", response_model=list[ToolUsageResponseItem])
async def get_tool_usage(
    filters: FilterDep,
    service: MetricsServiceDep,
) -> list[ToolUsageResponseItem]:
    items = service.tool_usage(filters)
    return [ToolUsageResponseItem(**_to_dict(item)) for item in items]
