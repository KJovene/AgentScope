from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Query

from agentscope.interfaces.api import fixtures
from agentscope.interfaces.api.schemas.metrics import Indicators, Point, ToolUsage

router = APIRouter(prefix="/metrics", tags=["metrics"])


@router.get("/indicators", response_model=Indicators)
async def get_indicators(
    sources: list[str] = Query(default=[]),
    agents: list[str] = Query(default=[]),
    models: list[str] = Query(default=[]),
    date_from: datetime | None = None,
    date_to: datetime | None = None,
) -> Indicators:
    return Indicators(**fixtures.INDICATORS)


@router.get("/timeseries", response_model=list[Point])
async def get_timeseries(
    metric: str,
    granularity: str = "day",
    sources: list[str] = Query(default=[]),
) -> list[Point]:
    return [Point(**p) for p in fixtures.TIMESERIES]


@router.get("/tool-usage", response_model=list[ToolUsage])
async def get_tool_usage(sources: list[str] = Query(default=[])) -> list[ToolUsage]:
    return [ToolUsage(**t) for t in fixtures.TOOL_USAGE]
