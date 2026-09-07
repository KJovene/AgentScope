"""Lecture de la provenance : d'une entité normalisée vers son enregistrement source."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from agentscope.domain import RawRecord
from agentscope.infrastructure.persistence.orm_models import (
    ModelCallRow,
    RawRecordRow,
    SessionRow,
    SourceRow,
    ToolCallRow,
)
from agentscope.infrastructure.persistence.repositories._mappers import row_to_raw_record


class SqlProvenanceRepository:
    def __init__(self, session: Session) -> None:
        self._s = session

    def raw_record_for_session(
        self, source_name: str, external_id: str
    ) -> RawRecord | None:
        row = self._s.execute(
            select(RawRecordRow)
            .join(SessionRow, SessionRow.raw_record_id == RawRecordRow.id)
            .join(SourceRow, SourceRow.id == SessionRow.source_id)
            .where(SourceRow.name == source_name, SessionRow.external_id == external_id)
        ).scalar_one_or_none()
        return row_to_raw_record(row) if row is not None else None

    def raw_record_for_model_call(
        self, source_name: str, session_external_id: str, sequence: int
    ) -> RawRecord | None:
        row = self._s.execute(
            select(RawRecordRow)
            .join(ModelCallRow, ModelCallRow.raw_record_id == RawRecordRow.id)
            .join(SessionRow, SessionRow.id == ModelCallRow.session_id)
            .join(SourceRow, SourceRow.id == SessionRow.source_id)
            .where(
                SourceRow.name == source_name,
                SessionRow.external_id == session_external_id,
                ModelCallRow.sequence == sequence,
            )
        ).scalar_one_or_none()
        return row_to_raw_record(row) if row is not None else None

    def raw_record_for_tool_call(
        self, source_name: str, session_external_id: str, sequence: int
    ) -> RawRecord | None:
        row = self._s.execute(
            select(RawRecordRow)
            .join(ToolCallRow, ToolCallRow.raw_record_id == RawRecordRow.id)
            .join(SessionRow, SessionRow.id == ToolCallRow.session_id)
            .join(SourceRow, SourceRow.id == SessionRow.source_id)
            .where(
                SourceRow.name == source_name,
                SessionRow.external_id == session_external_id,
                ToolCallRow.sequence == sequence,
            )
        ).scalar_one_or_none()
        return row_to_raw_record(row) if row is not None else None
