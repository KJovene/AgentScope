"""Conteneur de composition de l'API.

Point unique où les *ports* (couche application) rencontrent leurs implémentations
d'infrastructure. Créé une fois par process dans le *lifespan* de l'app
(`app.state.container`) ; les routes y accèdent via `dependencies.py`.
"""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from agentscope.application.ports.data_quality import DataQualityQueryService
from agentscope.application.ports.metrics import MetricsQueryService
from agentscope.application.ports.sources import SourcesQueryService
from agentscope.infrastructure.config.settings import Settings


class Database:
    """Moteur SQLAlchemy + fabrique de sessions pour la durée du process."""

    def __init__(self, db_url: str) -> None:
        connect_args: dict[str, object] = {}
        if db_url.startswith("sqlite"):
            connect_args["check_same_thread"] = False
        self.engine = create_engine(db_url, pool_pre_ping=True, connect_args=connect_args)
        self.session_factory = sessionmaker(
            bind=self.engine, autoflush=False, autocommit=False, expire_on_commit=False
        )

    @contextmanager
    def session(self) -> Iterator[Session]:
        """Session transactionnelle : commit si succès, rollback sinon."""
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
    """Graphe d'objets de l'application."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        db_url = (
            getattr(settings, "database_url", None)
            or getattr(settings, "db_url", None)
            or "sqlite:///:memory:"
        )
        self.database = Database(db_url)

    # -- Services de lecture (CQRS, issue I1.9) : une instance par requête -----

    def make_metrics_service(self, session: Session) -> MetricsQueryService:
        from agentscope.infrastructure.persistence.queries.metrics import (
            SqlMetricsQueryService,
        )

        return SqlMetricsQueryService(session)

    def make_sources_service(self, session: Session) -> SourcesQueryService:
        from agentscope.infrastructure.persistence.queries.sources import (
            SqlSourcesQueryService,
        )

        return SqlSourcesQueryService(session)

    def make_data_quality_service(self, session: Session) -> DataQualityQueryService:
        from agentscope.infrastructure.persistence.queries.data_quality import (
            SqlDataQualityQueryService,
        )

        return SqlDataQualityQueryService(session)
