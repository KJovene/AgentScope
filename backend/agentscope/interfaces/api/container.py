from __future__ import annotations

from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from agentscope.application.ports.llm_provider import LLMProvider
from agentscope.application.use_cases.analyze_unknown_file import AnalyzeUnknownFileUseCase
from agentscope.application.use_cases.import_file import ImportFileUseCase
from agentscope.infrastructure.config.settings import Settings
from agentscope.infrastructure.llm.factory import create_llm_provider
from agentscope.infrastructure.persistence.repositories.import_repo import SQLAlchemyImportRepository
from agentscope.infrastructure.persistence.repositories.model_call_repo import SQLAlchemyModelCallRepository
from agentscope.infrastructure.persistence.repositories.session_repo import SQLAlchemySessionRepository
from agentscope.infrastructure.persistence.repositories.tool_call_repo import SQLAlchemyToolCallRepository
from agentscope.infrastructure.readers.jsonl_reader import JSONLSourceReader


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

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.database = Database(settings.db_url)
        self.jsonl_reader = JSONLSourceReader()
        self._llm_provider: LLMProvider | None = None

    @property
    def llm_provider(self) -> LLMProvider:
        if self._llm_provider is None:
            self._llm_provider = create_llm_provider(self.settings)
        return self._llm_provider

    # --- Fabriques de cas d'usage ---

    def make_import_file_use_case(self, session: Session) -> ImportFileUseCase:
        return ImportFileUseCase(
            session_repo=SQLAlchemySessionRepository(session),
            import_repo=SQLAlchemyImportRepository(session),
            model_call_repo=SQLAlchemyModelCallRepository(session),
            tool_call_repo=SQLAlchemyToolCallRepository(session),
            reader=self.jsonl_reader,
        )

    def make_analyze_file_use_case(self) -> AnalyzeUnknownFileUseCase:
        return AnalyzeUnknownFileUseCase(llm_provider=self.llm_provider)
