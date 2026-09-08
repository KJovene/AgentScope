from __future__ import annotations

import dataclasses
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query, status

from agentscope.application.ports.metrics import MetricFilter, MetricsQueryService, Page
from agentscope.interfaces.api.dependencies import MetricsServiceDep
from agentscope.interfaces.api.routes.metrics import parse_metric_filter
from agentscope.interfaces.api.schemas.common import Paginated
from agentscope.interfaces.api.schemas.sessions import (
    SessionDetailResponse,
    SessionItemResponse,
)

router = APIRouter(prefix="/sessions", tags=["sessions"])

FilterDep = Annotated[MetricFilter, Depends(parse_metric_filter)]


def _to_dict(obj: Any) -> dict[str, Any]:
    if isinstance(obj, dict):
        return obj
    if dataclasses.is_dataclass(obj) and not isinstance(obj, type):
        return dataclasses.asdict(obj)
    if hasattr(obj, "__dict__"):
        return obj.__dict__
    raise TypeError(f"Impossible de convertir {type(obj)} en dictionnaire")


@router.get("", response_model=Paginated[SessionItemResponse])
async def list_sessions(
    filters: FilterDep,
    service: MetricsServiceDep,
    limit: int = Query(default=50, ge=1, le=200, description="Taille de page (max 200)"),
    offset: int = Query(default=0, ge=0, description="Index de départ"),
) -> Paginated[SessionItemResponse]:
    """Liste filtrée et paginée des sessions."""
    effective_limit = min(limit, 200)
    page_req = Page(limit=effective_limit, offset=offset)

    result = service.sessions(filters, page_req)

    items = [SessionItemResponse(**_to_dict(item)) for item in result.items]
    return Paginated(
        items=items,
        total=result.total,
        limit=result.limit,
        offset=result.offset,
    )


@router.get("/{session_id}", response_model=SessionDetailResponse)
async def get_session_detail(
    session_id: int,
    service: MetricsServiceDep,
) -> SessionDetailResponse:
    """Vue détaillée d'une session avec sa timeline chronologique d'appels."""
    detail = service.session_detail(session_id)
    if detail is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session #{session_id} introuvable.",
        )

    return SessionDetailResponse(**_to_dict(detail))
