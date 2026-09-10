"""Implémentation de ``RepositoryRegistryService`` (issue I4.8 / dimension I1.10).

Câble le port au ``SqlReferenceRepository`` dans la session de la requête, avec
commit explicite après écriture.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from agentscope.application.ports.repository_registry import (
    RegisterOutcome,
    RepositoryEntry,
)
from agentscope.domain import Repository
from agentscope.infrastructure.persistence.repositories.sql import SqlReferenceRepository


class SqlRepositoryRegistryService:
    def __init__(self, session: Session) -> None:
        self._s = session
        self._ref = SqlReferenceRepository(session)

    def _require_source(self, source_name: str) -> None:
        if self._ref.get_source(source_name) is None:
            raise LookupError(f"source inconnue : {source_name!r}")

    def list(self, source_name: str) -> list[RepositoryEntry]:
        self._require_source(source_name)
        return [
            RepositoryEntry(name=r.name, url=r.url, language=r.language)
            for r in self._ref.list_code_repositories(source_name)
        ]

    def register(
        self, source_name: str, repositories: list[RepositoryEntry]
    ) -> RegisterOutcome:
        self._require_source(source_name)
        outcome = self._ref.upsert_code_repositories(
            source_name,
            [
                Repository(
                    source_name=source_name,
                    name=entry.name,
                    url=entry.url,
                    language=entry.language,
                )
                for entry in repositories
            ],
        )
        self._s.commit()
        return RegisterOutcome(registered=outcome.inserted, skipped=outcome.skipped)
