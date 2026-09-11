"""Implémentation de ``MappingCrudService`` (issue I4.5).

Câble les cas d'utilisation ``manage_mappings`` (I3.10) au ``MappingRepository``
SQLAlchemy, dans la session de la requête (commit explicite après écriture).
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any

from sqlalchemy.orm import Session

from agentscope.application.use_cases.manage_mappings import (
    GetMapping,
    ListMappings,
    SaveMapping,
    UpdateMapping,
)
from agentscope.domain import DomainError, FileFormat, Source, SourceMapping
from agentscope.infrastructure.persistence.repositories.sql import (
    SqlMappingRepository,
    SqlReferenceRepository,
)


class MissingSourceNameError(DomainError):
    """La définition ne déclare pas de `constants.source_name`."""


class SqlMappingService:
    def __init__(self, session: Session, clock: Callable[[], datetime] | None = None) -> None:
        self._s = session
        self._clock = clock or (lambda: datetime.now(UTC))
        self._repo = SqlMappingRepository(session)

    def create(
        self,
        *,
        name: str,
        source_format: FileFormat,
        definition: dict[str, Any],
        created_by: str | None = None,
    ) -> SourceMapping:
        source_name = str(definition.get("constants", {}).get("source_name") or "").strip()
        if not source_name:
            raise MissingSourceNameError("La définition doit déclarer `constants.source_name`.")
        self._ensure_source(source_name)

        mapping = SaveMapping(self._repo, self._clock).execute(
            name=name,
            source_name=source_name,
            source_format=source_format,
            definition=definition,
            created_by=created_by,
        )
        self._s.commit()
        return mapping

    def update(
        self,
        *,
        name: str,
        definition: dict[str, Any],
        created_by: str | None = None,
    ) -> SourceMapping:
        mapping = UpdateMapping(self._repo, self._clock).execute(
            name=name, definition=definition, created_by=created_by
        )
        self._s.commit()
        return mapping

    def list(self, *, source_name: str | None = None) -> list[SourceMapping]:
        return ListMappings(self._repo).execute(source_name=source_name)

    def get(self, *, name: str, version: int | None = None) -> SourceMapping | None:
        return GetMapping(self._repo).execute(name=name, version=version)

    def _ensure_source(self, source_name: str) -> None:
        reference = SqlReferenceRepository(self._s)
        if reference.get_source(source_name) is None:
            reference.add_source(Source(name=source_name))
            self._s.flush()
