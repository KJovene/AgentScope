"""Conteneur de composition de l'API.

Point unique où les *ports* (couche application) rencontrent leurs implémentations
d'infrastructure. Créé une fois par process dans le *lifespan* de l'app
(`app.state.container`) ; les routes y accèdent via `dependencies.py`.
"""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from datetime import datetime, timezone
import uuid

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from agentscope.application.ports.data_quality import DataQualityQueryService
from agentscope.application.ports.imports import (
    ImportBatchItem,
    ImportRejectItem,
    ImportService,
)
from agentscope.application.ports.metrics import MetricsQueryService, Page, Paginated
from agentscope.application.ports.sources import SourcesQueryService
from agentscope.infrastructure.config.settings import Settings


class DefaultImportService(ImportService):
    """Implémentation par défaut (bouchon) du service d'import."""

    def __init__(self, session: Session) -> None:
        self.session = session

    async def process_import(
        self, mapping_id: str, files: list[tuple[str, bytes]]
    ) -> ImportBatchItem:
        return ImportBatchItem(
            id=f"batch-{uuid.uuid4().hex[:8]}",
            source_id="src-tracelab",
            mapping_id=mapping_id,
            status="completed",
            imported_count=max(len(files) * 10, 1),
            duplicate_count=0,
            rejected_count=0,
            missing_info_count=0,
            imported_at=datetime.now(timezone.utc),
        )

    def list_imports(self, page: Page) -> Paginated[ImportBatchItem]:
        item = ImportBatchItem(
            id="batch-123",
            source_id="src-tracelab",
            mapping_id="tracelab-jsonl",
            status="completed",
            imported_count=10,
            duplicate_count=1,
            rejected_count=0,
            missing_info_count=0,
            imported_at=datetime.now(timezone.utc),
        )
        return Paginated(items=(item,), total=1, limit=page.limit, offset=page.offset)

    def get_import_detail(self, import_id: str) -> ImportBatchItem | None:
        return ImportBatchItem(
            id=import_id,
            source_id="src-tracelab",
            mapping_id="tracelab-jsonl",
            status="completed",
            imported_count=10,
            duplicate_count=1,
            rejected_count=0,
            missing_info_count=0,
            imported_at=datetime.now(timezone.utc),
        )

    def list_rejects(
        self, import_id: str, page: Page
    ) -> Paginated[ImportRejectItem]:
        return Paginated(items=(), total=0, limit=page.limit, offset=page.offset)


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

    def make_import_service(self, session: Session) -> ImportService:
        # Utilise l'implémentation DefaultImportService définie plus haut dans ce fichier
        return DefaultImportService(session)
