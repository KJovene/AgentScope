"""Route ``POST /analyze`` (issue I4.3) — fichier inconnu → profil + proposition.

Branchée sur ``MappingWorkbenchService`` (``AnalyzeUnknownFile``, I3.7). Aucune
ressource créée : la proposition est éphémère. Une proposition non conforme au
contrat remonte en erreur explicite (``AnalysisFailedError`` → HTTP 400).
"""

from __future__ import annotations

import dataclasses
from typing import Any

from fastapi import APIRouter, File, UploadFile

from agentscope.interfaces.api.dependencies import WorkbenchServiceDep
from agentscope.interfaces.api.schemas.mappings import (
    AnalyzeResponse,
    FieldProfileSet,
    MappingProposal,
)

router = APIRouter(tags=["analyze"])


def _asdict(obj: Any) -> Any:
    if dataclasses.is_dataclass(obj) and not isinstance(obj, type):
        return dataclasses.asdict(obj)
    return obj


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze_unknown_file(
    service: WorkbenchServiceDep,
    file: UploadFile = File(...),
) -> AnalyzeResponse:
    content = await file.read()
    result = service.analyze(file.filename or "upload", content)
    return AnalyzeResponse(
        profile=FieldProfileSet(**_asdict(result.profile)),
        proposal=MappingProposal(**_asdict(result.proposal)),
    )
