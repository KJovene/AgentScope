from __future__ import annotations

import dataclasses
from typing import Annotated, Any

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status

from agentscope.application.ports.metrics import Page
from agentscope.interfaces.api.dependencies import ImportServiceDep
from agentscope.interfaces.api.schemas.common import Paginated
from agentscope.interfaces.api.schemas.imports import ImportReport, RejectRecord

router = APIRouter(prefix="/imports", tags=["imports"])


def _to_dict(obj: Any) -> dict[str, Any]:
    if isinstance(obj, dict):
        return obj
    if dataclasses.is_dataclass(obj) and not isinstance(obj, type):
        return dataclasses.asdict(obj)
    if hasattr(obj, "__dict__"):
        return obj.__dict__
    raise TypeError(f"Impossible de convertir {type(obj)} en dictionnaire")


def _to_reject_record(item: Any) -> RejectRecord:
    d = _to_dict(item)
    if "record_index" not in d or d["record_index"] is None:
        d["record_index"] = d.get("line_number") or 0
    if "reason_detail" not in d or not d["reason_detail"]:
        d["reason_detail"] = d.get("reason") or "Enregistrement rejeté"
    if "reason_code" not in d or not d["reason_code"]:
        d["reason_code"] = "REJECTED_RECORD"
    if "payload" not in d or not d["payload"]:
        raw = d.get("raw_record")
        d["payload"] = {"raw": raw} if isinstance(raw, str) else (raw or {})
    return RejectRecord(**d)


@router.post("", response_model=ImportReport, status_code=status.HTTP_201_CREATED)
async def create_import(
    mapping_id: Annotated[str, Form(...)],
    files: Annotated[list[UploadFile], File(...)],
    service: ImportServiceDep,
) -> ImportReport:
    """Téléverse un ou plusieurs fichiers de traces et génère un lot d'importation."""
    if not files:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Au moins un fichier doit être fourni pour l'importation.",
        )

    file_payloads: list[tuple[str, bytes]] = []
    for f in files:
        content = await f.read()
        file_payloads.append((f.filename or "unknown", content))

    batch = await service.process_import(mapping_id=mapping_id, files=file_payloads)
    return ImportReport(**_to_dict(batch))


@router.get("", response_model=Paginated[ImportReport])
async def list_imports(
    service: ImportServiceDep,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> Paginated[ImportReport]:
    """Historique paginé des lots d'importation."""
    page_req = Page(limit=limit, offset=offset)
    result = service.list_imports(page_req)

    items = [ImportReport(**_to_dict(item)) for item in result.items]
    return Paginated(
        items=items,
        total=result.total,
        limit=result.limit,
        offset=result.offset,
    )


@router.get("/{import_id}", response_model=ImportReport)
async def get_import(
    import_id: str,
    service: ImportServiceDep,
) -> ImportReport:
    """Détail synthétique d'un lot d'importation."""
    batch = service.get_import_detail(import_id)
    if batch is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Import '{import_id}' introuvable.",
        )
    return ImportReport(**_to_dict(batch))


@router.get("/{import_id}/rejects", response_model=Paginated[RejectRecord])
async def list_rejects(
    import_id: str,
    service: ImportServiceDep,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> Paginated[RejectRecord]:
    """Liste paginée des enregistrements rejetés."""
    batch = service.get_import_detail(import_id)
    if batch is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Import '{import_id}' introuvable.",
        )

    page_req = Page(limit=limit, offset=offset)
    result = service.list_rejects(import_id, page_req)

    items = [_to_reject_record(item) for item in result.items]
    return Paginated(
        items=items,
        total=result.total,
        limit=result.limit,
        offset=result.offset,
    )
