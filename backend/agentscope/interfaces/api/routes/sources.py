from __future__ import annotations

from fastapi import APIRouter

from agentscope.interfaces.api import fixtures
from agentscope.interfaces.api.schemas.sources import DataQuality, Source

router = APIRouter(tags=["sources"])


@router.get("/sources", response_model=list[Source])
async def list_sources() -> list[Source]:
    return [Source(**s) for s in fixtures.SOURCES]


@router.get("/data-quality", response_model=list[DataQuality])
async def get_data_quality() -> list[DataQuality]:
    return [DataQuality(**d) for d in fixtures.DATA_QUALITY]
