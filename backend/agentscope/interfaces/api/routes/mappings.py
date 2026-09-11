"""Routes ``/mappings`` (issue I4.5) — CRUD versionné des mappings persistés,
et prévisualisation (I4.3).

Branchées sur ``MappingCrudService`` (``manage_mappings``, I3.10) et
``MappingWorkbenchService`` (``PreviewMapping``, I3.9).
"""

from __future__ import annotations

import dataclasses
import json
from typing import Any

from fastapi import APIRouter, File, Form, HTTPException, Query, UploadFile

from agentscope.application.use_cases.manage_mappings import MappingNotFoundError
from agentscope.domain import FileFormat, SourceMapping
from agentscope.interfaces.api.dependencies import MappingServiceDep, WorkbenchServiceDep
from agentscope.interfaces.api.schemas.common import Paginated
from agentscope.interfaces.api.schemas.mappings import (
    Mapping,
    MappingCreate,
    MappingUpdate,
    PreviewResult,
    PreviewRow,
)

router = APIRouter(tags=["mappings"])


def _to_schema(mapping: SourceMapping) -> Mapping:
    return Mapping(
        mapping_id=mapping.name,
        name=mapping.name,
        version=mapping.version,
        source_name=mapping.source_name,
        source_format=mapping.source_format.value,
        definition=mapping.definition,
        is_active=mapping.is_active,
        created_at=mapping.created_at,
        created_by=mapping.created_by,
    )


# --- CRUD versionné (I4.5) ---------------------------------------------------


@router.post("/mappings", response_model=Mapping, status_code=201)
async def create_mapping(payload: MappingCreate, service: MappingServiceDep) -> Mapping:
    try:
        fmt = FileFormat(payload.source_format)
    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail=f"`source_format` doit être l'un de {[f.value for f in FileFormat]}.",
        ) from exc
    return _to_schema(
        service.create(name=payload.name, source_format=fmt, definition=payload.definition)
    )


@router.get("/mappings", response_model=Paginated[Mapping])
async def list_mappings(
    service: MappingServiceDep,
    source: str | None = Query(default=None, description="Filtrer par nom de source"),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> Paginated[Mapping]:
    items = service.list(source_name=source)
    window = items[offset : offset + limit]
    return Paginated(
        items=[_to_schema(m) for m in window],
        total=len(items),
        limit=limit,
        offset=offset,
    )


@router.get("/mappings/{mapping_id}", response_model=Mapping)
async def get_mapping(
    mapping_id: str,
    service: MappingServiceDep,
    version: int | None = Query(default=None, ge=1),
) -> Mapping:
    mapping = service.get(name=mapping_id, version=version)
    if mapping is None:
        raise HTTPException(status_code=404, detail=f"Mapping '{mapping_id}' introuvable.")
    return _to_schema(mapping)


@router.put("/mappings/{mapping_id}", response_model=Mapping)
async def update_mapping(
    mapping_id: str, payload: MappingUpdate, service: MappingServiceDep
) -> Mapping:
    """PUT crée une nouvelle version (§5.3), jamais de mutation en place."""
    try:
        updated = service.update(name=mapping_id, definition=payload.definition)
    except MappingNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return _to_schema(updated)


# --- Prévisualisation (I4.3) ----------------------------------------------


_ENTITY_ATTRS = (
    ("session", "sessions"),
    ("model_call", "model_calls"),
    ("tool_call", "tool_calls"),
)


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
