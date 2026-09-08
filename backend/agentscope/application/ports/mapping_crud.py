"""Port ``MappingCrudService`` : gestion des mappings persistés via l'API (§5.3).

CRUD versionné (issue I4.5) : ``create`` pose la version 1, ``update`` crée
toujours la version suivante — jamais de mutation en place. S'appuie sur les
cas d'utilisation ``manage_mappings`` (I3.10) + le ``MappingRepository``.
"""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

from agentscope.domain import FileFormat, SourceMapping


@runtime_checkable
class MappingCrudService(Protocol):
    def create(
        self,
        *,
        name: str,
        source_format: FileFormat,
        definition: dict[str, Any],
        created_by: str | None = None,
    ) -> SourceMapping:
        """Persiste un nouveau mapping (version 1). La source est déduite de
        ``definition.constants.source_name`` et créée si besoin."""
        ...

    def update(
        self,
        *,
        name: str,
        definition: dict[str, Any],
        created_by: str | None = None,
    ) -> SourceMapping:
        """Crée la version suivante d'un mapping existant."""
        ...

    def list(self, *, source_name: str | None = None) -> list[SourceMapping]: ...

    def get(self, *, name: str, version: int | None = None) -> SourceMapping | None: ...
