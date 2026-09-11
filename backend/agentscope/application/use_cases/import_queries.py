"""Consultation de l'historique des imports et de leurs rejets (issue I2.10)."""

from __future__ import annotations

from dataclasses import dataclass

from agentscope.application.ports import ImportRepository, RejectRepository
from agentscope.domain import DomainError, ImportBatch, ImportReject


class ImportNotFoundError(DomainError):
    """L'import demande n'existe pas pour la source indiquee."""


@dataclass(frozen=True, slots=True)
class Page[Item]:
    """Page immuable partagee par les consultations d'import."""

    items: tuple[Item, ...]
    total: int
    limit: int
    offset: int


def _pagination(limit: int, offset: int) -> tuple[int, int]:
    if limit <= 0:
        raise ValueError("limit doit etre > 0")
    if offset < 0:
        raise ValueError("offset doit etre >= 0")
    return min(limit, 200), offset


@dataclass(frozen=True, slots=True)
class ListImports:
    """Retourne l'historique pagine des imports les plus recents."""

    repository: ImportRepository

    def execute(self, *, limit: int = 50, offset: int = 0) -> Page[ImportBatch]:
        limit, offset = _pagination(limit, offset)
        return Page(
            items=tuple(self.repository.list_recent(limit, offset)),
            total=self.repository.count(),
            limit=limit,
            offset=offset,
        )


@dataclass(frozen=True, slots=True)
class GetImportReport:
    """Retourne le bilan d'un import identifie par son hash de fichier."""

    repository: ImportRepository

    def execute(self, *, source_name: str, file_sha256: str) -> ImportBatch:
        batch = self.repository.get_by_file(source_name, file_sha256)
        if batch is None:
            raise ImportNotFoundError(
                f"Import introuvable pour la source `{source_name}` et le fichier `{file_sha256}`."
            )
        return batch


@dataclass(frozen=True, slots=True)
class ListRejects:
    """Retourne les rejets pagines d'un import existant."""

    imports: ImportRepository
    rejects: RejectRepository

    def execute(
        self,
        *,
        source_name: str,
        file_sha256: str,
        limit: int = 50,
        offset: int = 0,
    ) -> Page[ImportReject]:
        limit, offset = _pagination(limit, offset)
        batch = self.imports.get_by_file(source_name, file_sha256)
        if batch is None:
            raise ImportNotFoundError(
                f"Import introuvable pour la source `{source_name}` et le fichier `{file_sha256}`."
            )
        return Page(
            items=tuple(self.rejects.list_for_import(source_name, file_sha256, limit, offset)),
            total=self.rejects.count_for_import(source_name, file_sha256),
            limit=limit,
            offset=offset,
        )
