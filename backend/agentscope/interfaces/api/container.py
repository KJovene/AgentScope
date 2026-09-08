from __future__ import annotations

from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from agentscope.application.ports.metrics import MetricsQueryService
from agentscope.infrastructure.config.settings import Settings

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

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        db_url = (
            getattr(settings, "database_url", None)
            or getattr(settings, "db_url", None)
            or "sqlite:///:memory:"
        )
        self.database = Database(db_url)

    def make_metrics_service(self, session: Session) -> MetricsQueryService:
        from agentscope.infrastructure.persistence.services.metrics_service import (
            SQLAlchemyMetricsQueryService,
        )
        return SQLAlchemyMetricsQueryService(session)
