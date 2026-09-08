from __future__ import annotations

import dataclasses
import json
from typing import Any

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from agentscope.interfaces.api import fixtures
from agentscope.interfaces.api.dependencies import WorkbenchServiceDep
from agentscope.interfaces.api.schemas.common import Paginated
from agentscope.interfaces.api.schemas.mappings import (
    Mapping,
    MappingCreate,
    MappingUpdate,
    PreviewResult,
    PreviewRow,
)

router = APIRouter(tags=["mappings"])


# --- CRUD : encore des stubs (issue I4.5) ------------------------------------


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


# --- Prévisualisation : branchée (issue I4.3) -------------------------------


_ENTITY_ATTRS = (("session", "sessions"), ("model_call", "model_calls"), ("tool_call", "tool_calls"))


def _row_dict(obj: Any) -> dict[str, Any]:
    return dataclasses.asdict(obj) if dataclasses.is_dataclass(obj) else dict(obj)


@router.post("/mappings/{mapping_id}/preview", response_model=PreviewResult)
async def preview_mapping(
    mapping_id: str,
    service: WorkbenchServiceDep,
    file: UploadFile = File(..., description="Échantillon du fichier source"),
    definition: str = Form(..., description="Définition du mapping (JSON) à prévisualiser"),
    sample_size: int = Form(50, ge=1, le=500),
) -> PreviewResult:
    """Dry-run de normalisation d'un mapping sur un échantillon — aucune écriture."""
    try:
        parsed = json.loads(definition)
    except json.JSONDecodeError as exc:
        raise HTTPException(
            status_code=422, detail="Le champ `definition` doit être un JSON valide."
        ) from exc

    content = await file.read()
    report = service.preview(file.filename or "upload", content, parsed, sample_size)
    result = report.result

    rows = [
        PreviewRow(entity=entity, row=_row_dict(item))
        for entity, attr in _ENTITY_ATTRS
        for item in getattr(result, attr)
    ]
    rejects = [_row_dict(r) for r in result.rejects]
    return PreviewResult(rows=rows, rejects=rejects)
