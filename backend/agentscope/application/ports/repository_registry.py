"""Port d'écriture du référentiel de dépôts de code (dimension SWE-chat, I1.10).

Les sessions se rattachent à un dépôt **déjà déclaré** (rattachement best-effort,
cf. ``SqlSessionRepository.upsert_many``). Ce port permet de déclarer ces dépôts
pour une source — appelé après un import par ``scripts/seed_import.py``.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable


@dataclass(frozen=True, slots=True)
class RepositoryEntry:
    name: str
    url: str | None = None
    language: str | None = None


@dataclass(frozen=True, slots=True)
class RegisterOutcome:
    registered: int  # lignes réellement créées
    skipped: int  # déjà présentes (idempotent)


@runtime_checkable
class RepositoryRegistryService(Protocol):
    def list(self, source_name: str) -> list[RepositoryEntry]:
        """Dépôts déclarés pour une source. ``LookupError`` si la source est inconnue."""
        ...

    def register(self, source_name: str, repositories: list[RepositoryEntry]) -> RegisterOutcome:
        """Déclare (idempotent) des dépôts. ``LookupError`` si la source est inconnue."""
        ...
