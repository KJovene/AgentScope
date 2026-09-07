from __future__ import annotations

from fastapi import APIRouter, File, UploadFile

from agentscope.interfaces.api import fixtures
from agentscope.interfaces.api.schemas.mappings import AnalyzeResponse

router = APIRouter(tags=["analyze"])


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze_unknown_file(file: UploadFile = File(...)) -> AnalyzeResponse:
    """Ne crée aucune ressource — renvoie un profil + une proposition éphémères."""
    return AnalyzeResponse(profile=fixtures.FIELD_PROFILE_SET, proposal=fixtures.MAPPING_PROPOSAL)
