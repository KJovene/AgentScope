"""Cas d'utilisation de gestion des mappings persistés (issue I3.10).

CRUD versionné : ``SaveMapping`` crée la version 1 ; ``UpdateMapping`` crée
toujours la version suivante — jamais de mutation d'une version existante
(traçabilité, cf. docs/PLAN.md §5.3 « PUT crée une nouvelle version »).
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any

from agentscope.application.mapping.validator import parse_and_validate
from agentscope.application.ports import MappingRepository
from agentscope.domain import DomainError, FileFormat, SourceMapping


class MappingAlreadyExistsError(DomainError):
    """Un mapping actif porte déjà ce nom."""


class MappingNotFoundError(DomainError):
    """Aucun mapping connu sous ce nom."""


class SaveMapping:
    """Persiste un nouveau mapping (version 1), après validation du contrat (I2.13)."""

    def __init__(
        self,
        repository: MappingRepository,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self._repository = repository
        self._clock = clock or (lambda: datetime.now(UTC))

    def execute(
        self,
        *,
        name: str,
        source_name: str,
        source_format: FileFormat,
        definition: dict[str, Any],
        created_by: str | None = None,
    ) -> SourceMapping:
        if self._repository.get(name) is not None:
            raise MappingAlreadyExistsError(f"Un mapping `{name}` existe déjà.")

        parse_and_validate(definition)  # lève InvalidMappingError si non conforme

        mapping = SourceMapping(
            name=name,
            version=1,
            source_name=source_name,
            source_format=source_format,
            definition=definition,
            created_at=self._clock(),
            is_active=True,
            created_by=created_by,
        )
        self._repository.add(mapping)
        return mapping


class UpdateMapping:
    """Crée une nouvelle version d'un mapping existant (jamais de mutation en place)."""

    def __init__(
        self,
        repository: MappingRepository,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self._repository = repository
        self._clock = clock or (lambda: datetime.now(UTC))

    def execute(
        self,
        *,
        name: str,
        definition: dict[str, Any],
        created_by: str | None = None,
    ) -> SourceMapping:
        existing = self._repository.get(name)
        if existing is None:
            raise MappingNotFoundError(f"Aucun mapping `{name}` à mettre à jour.")

        parse_and_validate(definition)

        mapping = SourceMapping(
            name=name,
            version=existing.version + 1,
            source_name=existing.source_name,
            source_format=existing.source_format,
            definition=definition,
            created_at=self._clock(),
            is_active=True,
            created_by=created_by,
        )
        self._repository.add(mapping)
        return mapping


class ListMappings:
    """Liste les mappings connus, éventuellement filtrés par source."""

    def __init__(self, repository: MappingRepository) -> None:
        self._repository = repository

    def execute(self, *, source_name: str | None = None) -> list[SourceMapping]:
        if source_name is not None:
            return self._repository.list_for_source(source_name)
        return self._repository.list_all()


class GetMapping:
    """Récupère un mapping par nom (dernière version active) ou par version précise."""

    def __init__(self, repository: MappingRepository) -> None:
        self._repository = repository

    def execute(self, *, name: str, version: int | None = None) -> SourceMapping | None:
        return self._repository.get(name, version)
