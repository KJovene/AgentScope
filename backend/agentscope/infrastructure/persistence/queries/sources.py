"""Implémentation SQLAlchemy de ``SourcesQueryService`` (référentiel des sources).

Lecture seule : liste les sources enregistrées avec leur nombre de sessions.
"""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from agentscope.application.ports.sources import SourceItem
from agentscope.infrastructure.persistence.orm_models import SessionRow, SourceRow


class SqlSourcesQueryService:
    def __init__(self, session: Session) -> None:
        self._s = session

    def list_sources(self) -> list[SourceItem]:
        stmt = (
            select(
                SourceRow.id,
                SourceRow.name,
                SourceRow.display_name,
                func.count(SessionRow.id).label("session_count"),
            )
            .select_from(SourceRow)
            .outerjoin(SessionRow, SessionRow.source_id == SourceRow.id)
            .group_by(SourceRow.id, SourceRow.name, SourceRow.display_name)
            .order_by(SourceRow.name)
        )
        return [
            SourceItem(
                id=str(row.id),
                name=row.name,
                description=row.display_name,
                format=None,
                session_count=int(row.session_count or 0),
                created_at=None,
            )
            for row in self._s.execute(stmt)
        ]
