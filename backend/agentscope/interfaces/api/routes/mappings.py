from __future__ import annotations

from fastapi import APIRouter, HTTPException

from agentscope.interfaces.api import fixtures
from agentscope.interfaces.api.schemas.common import Paginated
from agentscope.interfaces.api.schemas.mappings import (
    Mapping,
    MappingCreate,
    MappingUpdate,
    PreviewResult,
)

router = APIRouter(tags=["mappings"])


@router.post("/mappings", response_model=Mapping, status_code=201)
async def create_mapping(payload: MappingCreate) -> Mapping:
    return Mapping(**fixtures.MAPPING)


@router.get("/mappings", response_model=Paginated[Mapping])
async def list_mappings(limit: int = 50, offset: int = 0) -> Paginated[Mapping]:
    limit = min(limit, 200)
    item = Mapping(**fixtures.MAPPING)
    return Paginated(items=[item], total=1, limit=limit, offset=offset)


@router.get("/mappings/{mapping_id}", response_model=Mapping)
async def get_mapping(mapping_id: str) -> Mapping:
    if mapping_id != fixtures.MAPPING["mapping_id"]:
        raise HTTPException(status_code=404, detail=f"Mapping '{mapping_id}' introuvable.")
    return Mapping(**fixtures.MAPPING)


@router.put("/mappings/{mapping_id}", response_model=Mapping)
async def update_mapping(mapping_id: str, payload: MappingUpdate) -> Mapping:
    """PUT crée une nouvelle version (§5.3)."""
    if mapping_id != fixtures.MAPPING["mapping_id"]:
        raise HTTPException(status_code=404, detail=f"Mapping '{mapping_id}' introuvable.")
    updated = {**fixtures.MAPPING, "version": fixtures.MAPPING["version"] + 1, "definition": payload.definition}
    return Mapping(**updated)


@router.post("/mappings/{mapping_id}/preview", response_model=PreviewResult)
async def preview_mapping(mapping_id: str) -> PreviewResult:
    if mapping_id != fixtures.MAPPING["mapping_id"]:
        raise HTTPException(status_code=404, detail=f"Mapping '{mapping_id}' introuvable.")
    return PreviewResult(**fixtures.PREVIEW_RESULT)
