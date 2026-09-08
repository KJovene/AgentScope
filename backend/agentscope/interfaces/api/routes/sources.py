from __future__ import annotations

import dataclasses
from typing import Any

from fastapi import APIRouter

from agentscope.interfaces.api.dependencies import SourcesServiceDep
from agentscope.interfaces.api.schemas.sources import SourceResponse

router = APIRouter(tags=["sources"])


def _to_dict(obj: Any) -> dict[str, Any]:
    if isinstance(obj, dict):
        return obj
    if dataclasses.is_dataclass(obj) and not isinstance(obj, type):
        return dataclasses.asdict(obj)
    if hasattr(obj, "__dict__"):
        return obj.__dict__
    raise TypeError(f"Impossible de convertir {type(obj)} en dictionnaire")


@router.get("/sources", response_model=list[SourceResponse])
async def list_sources(
    service: SourcesServiceDep,
) -> list[SourceResponse]:
    """Référentiel des sources de traces d'agents enregistrées."""
    sources = service.list_sources()
    return [SourceResponse(**_to_dict(s)) for s in sources]
