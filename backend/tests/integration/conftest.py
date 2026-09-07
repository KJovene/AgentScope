"""Fixtures partagées des tests d'intégration : une base SQLite migrée par test."""

from __future__ import annotations

from collections.abc import Callable, Iterator
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config

import agentscope.infrastructure.persistence as persistence_pkg
from agentscope.infrastructure.config.settings import Settings
from agentscope.infrastructure.persistence.database import Database
from agentscope.infrastructure.persistence.unit_of_work import SqlAlchemyUnitOfWork

MIGRATIONS_DIR = Path(persistence_pkg.__file__).parent / "migrations"


@pytest.fixture
def database(tmp_path: Path) -> Iterator[Database]:
    url = f"sqlite:///{tmp_path / 'it.db'}"
    cfg = Config()
    cfg.set_main_option("script_location", str(MIGRATIONS_DIR))
    cfg.set_main_option("sqlalchemy.url", url)
    command.upgrade(cfg, "head")

    db = Database(Settings(database_url=url))
    try:
        yield db
    finally:
        db.engine.dispose()


@pytest.fixture
def make_uow(database: Database) -> Callable[[], SqlAlchemyUnitOfWork]:
    """Fabrique de `SqlAlchemyUnitOfWork` liées à la base migrée."""

    def _factory() -> SqlAlchemyUnitOfWork:
        return SqlAlchemyUnitOfWork(database)

    return _factory
