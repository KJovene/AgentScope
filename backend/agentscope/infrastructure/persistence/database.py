"""Fondations SQLAlchemy : moteur, fabrique de sessions, classe de base ORM.

Plomberie d'infrastructure uniquement — aucune table n'est déclarée ici (I1.1/I1.3).
Le domaine et les cas d'utilisation ne connaissent que les *ports* repository ; ils
ne voient jamais `Session` ni `Engine`.
"""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager

from sqlalchemy import Engine, MetaData, create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from agentscope.infrastructure.config.settings import Settings

# Nommage déterministe des contraintes -> migrations lisibles et tests qui peuvent
# assarter une contrainte par son nom (ex. uq_import_batch_source_id_file_sha256).
NAMING_CONVENTION = {
    "ix": "ix_%(table_name)s_%(column_0_N_name)s",
    "uq": "uq_%(table_name)s_%(column_0_N_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    """Classe de base commune à tous les modèles ORM (couche infrastructure)."""

    metadata = MetaData(naming_convention=NAMING_CONVENTION)


def create_db_engine(settings: Settings) -> Engine:
    connect_args: dict[str, object] = {}
    if settings.database_url.startswith("sqlite"):
        # Autorise le partage de la connexion entre threads (TestClient, uvicorn).
        connect_args["check_same_thread"] = False
    return create_engine(
        settings.database_url,
        echo=settings.db_echo,
        future=True,
        pool_pre_ping=True,
        connect_args=connect_args,
    )


class Database:
    """Détient le moteur et la fabrique de sessions pour la durée du process."""

    def __init__(self, settings: Settings) -> None:
        self.engine: Engine = create_db_engine(settings)
        self._session_factory: sessionmaker[Session] = sessionmaker(
            bind=self.engine,
            autoflush=False,
            expire_on_commit=False,
            future=True,
        )

    def create_session(self) -> Session:
        """Session brute — la gestion de transaction est à l'appelant (cf. UnitOfWork)."""
        return self._session_factory()

    @contextmanager
    def session(self) -> Iterator[Session]:
        """Session transactionnelle : commit si succès, rollback sinon."""
        session = self._session_factory()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
