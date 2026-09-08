from __future__ import annotations

from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from agentscope.infrastructure.config.settings import Settings
from agentscope.application.ports.sources import SourcesQueryService
from agentscope.application.ports.data_quality import DataQualityQueryService

class Database:

    def __init__(self, db_url: str) -> None:
        self.engine = create_engine(db_url, pool_pre_ping=True)
        self.session_factory = sessionmaker(bind=self.engine, autoflush=False, autocommit=False)

    @contextmanager
    def session(self) -> Generator[Session, None, None]:
        session = self.session_factory()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()


class Container:

  def make_metrics_service(self, session: Session) -> MetricsQueryService:
    from agentscope.infrastructure.persistence.services.metrics_service import (
        SQLAlchemyMetricsQueryService,
    )
    return SQLAlchemyMetricsQueryService(session)

  def make_sources_service(self, session: Session) -> SourcesQueryService:
        from agentscope.infrastructure.persistence.services.sources_service import (
            SQLAlchemySourcesQueryService,
        )
        return SQLAlchemySourcesQueryService(session)

  def make_data_quality_service(self, session: Session) -> DataQualityQueryService:
        from agentscope.infrastructure.persistence.services.data_quality_service import (
            SQLAlchemyDataQualityQueryService,
        )
        return SQLAlchemyDataQualityQueryService(session)

  def __init__(self, settings: Settings) -> None:
        self.settings = settings
        # Résolution robuste de l'URL DB (database_url ou db_url)
        db_url = (
            getattr(settings, "database_url", None)
            or getattr(settings, "db_url", None)
            or "sqlite:///:memory:"
        )
        self.database = Database(db_url)

