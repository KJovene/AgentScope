from __future__ import annotations

import dataclasses
from typing import Any

from fastapi import APIRouter, Query

from agentscope.interfaces.api.dependencies import DataQualityServiceDep
from agentscope.interfaces.api.schemas.data_quality import (
    DataQualityBatchMetrics,
    DataQualityResponse,
)

router = APIRouter(tags=["data-quality"])


def _to_dict(obj: Any) -> dict[str, Any]:
    if isinstance(obj, dict):
        return obj
    if dataclasses.is_dataclass(obj) and not isinstance(obj, type):
        return dataclasses.asdict(obj)
    if hasattr(obj, "__dict__"):
        return obj.__dict__
    raise TypeError(f"Impossible de convertir {type(obj)} en dictionnaire")


@router.get("/data-quality", response_model=DataQualityResponse)
async def get_data_quality(
    service: DataQualityServiceDep,
    source_id: str | None = Query(default=None, description="Filtrer par ID de source"),
) -> DataQualityResponse:
    """Panneau de qualité des données : bilans d'import et ratios de complétude."""
    batches = service.get_quality_metrics(source_id=source_id)
    return DataQualityResponse(
        batches=[DataQualityBatchMetrics(**_to_dict(b)) for b in batches]
    )
