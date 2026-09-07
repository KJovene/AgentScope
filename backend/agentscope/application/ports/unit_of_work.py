"""Port `UnitOfWork` — transaction applicative explicite.

Un cas d'utilisation ouvre une UoW (context manager), écrit via les repositories
exposés en attributs, puis `commit()` — ou laisse le `__exit__` faire un
`rollback()` si une exception remonte. L'import d'un fichier est ainsi **atomique**
(tout ou rien), condition des tests I7.1/I7.2.

**Aucune implémentation ici** : l'adaptateur SQLAlchemy (une session = une UoW)
arrive avec l'issue I1.5 et sera assemblé dans le conteneur de composition.
"""

from __future__ import annotations

from types import TracebackType
from typing import Protocol, runtime_checkable

from agentscope.application.ports.repositories import (
    FieldProfileRepository,
    ImportRepository,
    MappingRepository,
    ModelCallRepository,
    RawRecordRepository,
    ReferenceRepository,
    RejectRepository,
    SessionRepository,
    ToolCallRepository,
)


@runtime_checkable
class UnitOfWork(Protocol):
    reference: ReferenceRepository
    mappings: MappingRepository
    imports: ImportRepository
    raw_records: RawRecordRepository
    sessions: SessionRepository
    model_calls: ModelCallRepository
    tool_calls: ToolCallRepository
    rejects: RejectRepository
    field_profiles: FieldProfileRepository

    def __enter__(self) -> UnitOfWork: ...

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None: ...

    def commit(self) -> None: ...

    def rollback(self) -> None: ...
