from __future__ import annotations

import dataclasses
from typing import Any

from fastapi import APIRouter, HTTPException

from agentscope.application.ports.repository_registry import RepositoryEntry
from agentscope.interfaces.api.dependencies import (
    RepositoryRegistryServiceDep,
    SourcesServiceDep,
)
from agentscope.interfaces.api.schemas.sources import (
    RepositoryInput,
    RepositoryRegisterResult,
    RepositoryResponse,
    SourceResponse,
)

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


@router.get(
    "/sources/{source_name}/repositories", response_model=list[RepositoryResponse]
)
async def list_source_repositories(
    source_name: str, service: RepositoryRegistryServiceDep
) -> list[RepositoryResponse]:
    """Dépôts de code déclarés pour une source (dimension de filtre du dashboard)."""
    try:
        entries = service.list(source_name)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return [RepositoryResponse(name=e.name, url=e.url, language=e.language) for e in entries]


@router.post(
    "/sources/{source_name}/repositories",
    response_model=RepositoryRegisterResult,
    status_code=201,
)
async def register_source_repositories(
    source_name: str,
    repositories: list[RepositoryInput],
    service: RepositoryRegistryServiceDep,
) -> RepositoryRegisterResult:
    """Déclare (idempotent) les dépôts de code d'une source, pour que les sessions
    qui les référencent s'y rattachent."""
    try:
        outcome = service.register(
            source_name,
            [RepositoryEntry(name=r.name, url=r.url, language=r.language) for r in repositories],
        )
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return RepositoryRegisterResult(
        registered=outcome.registered,
        skipped=outcome.skipped,
        total=outcome.registered + outcome.skipped,
    )
