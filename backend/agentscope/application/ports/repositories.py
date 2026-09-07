"""Ports repository — couche application.

Interfaces structurelles (`Protocol`) que les cas d'utilisation attendent pour
persister et relire les agrégats du domaine. **Aucune implémentation ici** : les
adaptateurs SQLAlchemy arrivent avec l'issue I1.5.

Principes :

- **Côté écriture (commandes).** Les lectures riches du dashboard, adressées par
  `id` technique, passent par les *query services* (I1.9), pas par ces ports.
- **Idempotence.** Les insertions en masse suivent la politique
  *ignore-on-conflict* (le premier import gagne, cf.
  `docs/data/relational-model.md` §6) et renvoient un `UpsertOutcome` qui alimente
  le bilan d'import.
- **Atomicité.** Les cas d'utilisation composent ces ports via `UnitOfWork`
  (`agentscope.application.ports.unit_of_work`).
- **Identité.** L'identité métier est la clé naturelle du domaine ; l'adaptateur
  résout les clés étrangères techniques. Les méthodes d'écriture des enfants d'un
  import reçoivent l'`ImportBatch` parent pour ce rattachement.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from typing import Protocol, runtime_checkable

from agentscope.domain import (
    FieldProfile,
    ImportBatch,
    ImportReject,
    ModelCall,
    RawRecord,
    Repository,
    Session,
    Source,
    SourceMapping,
    ToolCall,
)


@dataclass(frozen=True, slots=True)
class UpsertOutcome:
    """Résultat d'une insertion en masse idempotente."""

    inserted: int
    skipped: int  # conflits ignorés = doublons détectés

    @property
    def total(self) -> int:
        return self.inserted + self.skipped

    @classmethod
    def empty(cls) -> UpsertOutcome:
        return cls(inserted=0, skipped=0)

    def __add__(self, other: UpsertOutcome) -> UpsertOutcome:
        return UpsertOutcome(
            inserted=self.inserted + other.inserted,
            skipped=self.skipped + other.skipped,
        )


@runtime_checkable
class ReferenceRepository(Protocol):
    """Données de référence (dimensions) : sources et dépôts de code."""

    def add_source(self, source: Source) -> None: ...

    def get_source(self, name: str) -> Source | None: ...

    def list_sources(self) -> list[Source]: ...

    def upsert_code_repositories(
        self, source_name: str, repositories: Iterable[Repository]
    ) -> UpsertOutcome: ...

    def get_code_repository(self, source_name: str, name: str) -> Repository | None: ...

    def list_code_repositories(self, source_name: str | None = None) -> list[Repository]:
        """Tous les dépôts, ou ceux d'une source (dimension de filtre du dashboard)."""
        ...


@runtime_checkable
class MappingRepository(Protocol):
    def add(self, mapping: SourceMapping) -> None: ...

    def get(self, name: str, version: int | None = None) -> SourceMapping | None:
        """`version=None` → dernière version active."""
        ...

    def list_for_source(self, source_name: str) -> list[SourceMapping]: ...

    def list_all(self) -> list[SourceMapping]: ...


@runtime_checkable
class ImportRepository(Protocol):
    def add(self, batch: ImportBatch) -> None: ...

    def update(self, batch: ImportBatch) -> None:
        """Met à jour par clé naturelle `(source, file_sha256)` : statut, compteurs."""
        ...

    def get_by_file(self, source_name: str, file_sha256: str) -> ImportBatch | None:
        """Cœur de l'idempotence niveau fichier : `None` → import inédit."""
        ...

    def list_recent(self, limit: int, offset: int) -> list[ImportBatch]: ...

    def count(self) -> int: ...


@runtime_checkable
class RawRecordRepository(Protocol):
    def upsert_many(
        self, batch: ImportBatch, records: Iterable[RawRecord]
    ) -> UpsertOutcome: ...


@runtime_checkable
class SessionRepository(Protocol):
    def upsert_many(
        self, batch: ImportBatch, sessions: Iterable[Session]
    ) -> UpsertOutcome: ...


@runtime_checkable
class ModelCallRepository(Protocol):
    def upsert_many(
        self, batch: ImportBatch, calls: Iterable[ModelCall]
    ) -> UpsertOutcome: ...


@runtime_checkable
class ToolCallRepository(Protocol):
    def upsert_many(
        self, batch: ImportBatch, calls: Iterable[ToolCall]
    ) -> UpsertOutcome: ...


@runtime_checkable
class RejectRepository(Protocol):
    def add_many(self, batch: ImportBatch, rejects: Iterable[ImportReject]) -> int: ...

    def list_for_import(
        self, source_name: str, file_sha256: str, limit: int, offset: int
    ) -> list[ImportReject]: ...

    def count_for_import(self, source_name: str, file_sha256: str) -> int: ...


@runtime_checkable
class FieldProfileRepository(Protocol):
    def upsert_many(
        self, batch: ImportBatch, profiles: Iterable[FieldProfile]
    ) -> UpsertOutcome: ...
