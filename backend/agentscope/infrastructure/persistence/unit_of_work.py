"""Unité de travail SQLAlchemy (issue I1.5).

Une UoW = une ``Session`` SQLAlchemy = une transaction. Les repositories exposés
partagent cette session ; ``commit()`` / ``rollback()`` la pilotent. Si le bloc
``with`` se termine sur une exception, ``__exit__`` fait un rollback.

Implémente le port ``agentscope.application.ports.UnitOfWork`` (typage structurel).
"""

from __future__ import annotations

from types import TracebackType

from sqlalchemy.orm import Session

from agentscope.application.ports import (
    FieldProfileRepository,
    ImportRepository,
    MappingRepository,
    ModelCallRepository,
    RawRecordRepository,
    ReferenceRepository,
    RejectRepository,
    SessionRepository,
    ToolCallRepository,
    UnitOfWork,
)
from agentscope.infrastructure.persistence.database import Database
from agentscope.infrastructure.persistence.repositories.sql import (
    SqlFieldProfileRepository,
    SqlImportRepository,
    SqlMappingRepository,
    SqlModelCallRepository,
    SqlRawRecordRepository,
    SqlReferenceRepository,
    SqlRejectRepository,
    SqlSessionRepository,
    SqlToolCallRepository,
)


class SqlAlchemyUnitOfWork:
    """Adaptateur du port ``UnitOfWork``. Les attributs sont typés par les *ports*
    (invariance des membres de Protocol) ; on y range des implémentations concrètes."""

    reference: ReferenceRepository
    mappings: MappingRepository
    imports: ImportRepository
    raw_records: RawRecordRepository
    sessions: SessionRepository
    model_calls: ModelCallRepository
    tool_calls: ToolCallRepository
    rejects: RejectRepository
    field_profiles: FieldProfileRepository

    def __init__(self, database: Database) -> None:
        self._database = database
        self._session: Session | None = None

    def __enter__(self) -> UnitOfWork:
        session = self._database.create_session()
        self._session = session
        self.reference = SqlReferenceRepository(session)
        self.mappings = SqlMappingRepository(session)
        self.imports = SqlImportRepository(session)
        self.raw_records = SqlRawRecordRepository(session)
        self.sessions = SqlSessionRepository(session)
        self.model_calls = SqlModelCallRepository(session)
        self.tool_calls = SqlToolCallRepository(session)
        self.rejects = SqlRejectRepository(session)
        self.field_profiles = SqlFieldProfileRepository(session)
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        try:
            if exc_type is not None:
                self.rollback()
        finally:
            if self._session is not None:
                self._session.close()
                self._session = None

    def commit(self) -> None:
        self._require_session().commit()

    def rollback(self) -> None:
        self._require_session().rollback()

    def _require_session(self) -> Session:
        if self._session is None:
            raise RuntimeError("UnitOfWork utilisée hors d'un bloc `with`")
        return self._session
