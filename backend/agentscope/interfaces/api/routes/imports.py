from __future__ import annotations

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from agentscope.interfaces.api import fixtures
from agentscope.interfaces.api.schemas.common import Paginated
from agentscope.interfaces.api.schemas.imports import ImportReport, RejectRecord

router = APIRouter(tags=["imports"])


@router.post("/imports", response_model=ImportReport)
async def create_import(
    mapping_id: str = Form(...),
    files: list[UploadFile] = File(...),
) -> ImportReport:
    """Stub synchrone (v1) : renvoie un bilan de démonstration."""
    return ImportReport(**fixtures.IMPORT_REPORT)


@router.get("/imports", response_model=Paginated[ImportReport])
async def list_imports(limit: int = 50, offset: int = 0) -> Paginated[ImportReport]:
    limit = min(limit, 200)
    item = ImportReport(**fixtures.IMPORT_REPORT)
    return Paginated(items=[item], total=1, limit=limit, offset=offset)


@router.get("/imports/{import_id}", response_model=ImportReport)
async def get_import(import_id: str) -> ImportReport:
    if import_id != fixtures.IMPORT_REPORT["id"]:
        raise HTTPException(status_code=404, detail=f"Import '{import_id}' introuvable.")
    return ImportReport(**fixtures.IMPORT_REPORT)


@router.get("/imports/{import_id}/rejects", response_model=Paginated[RejectRecord])
async def list_rejects(import_id: str, limit: int = 50, offset: int = 0) -> Paginated[RejectRecord]:
    if import_id != fixtures.IMPORT_REPORT["id"]:
        raise HTTPException(status_code=404, detail=f"Import '{import_id}' introuvable.")
    limit = min(limit, 200)
    items = [RejectRecord(**r) for r in fixtures.REJECTS]
    return Paginated(items=items, total=len(items), limit=limit, offset=offset)
