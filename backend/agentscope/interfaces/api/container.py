"""Point de composition (composition root).

C'est le SEUL endroit où les cas d'utilisation sont reliés à leurs implémentations
concrètes. Aujourd'hui le conteneur ne câble que la configuration et la base ; les
fabriques de repositories, d'unité de travail et de fournisseur IA sont des points
d'extension explicites, remplis par les EPICs 1 à 3.
"""

from __future__ import annotations

from agentscope.application.ports import (
    MetricsQueryService,
    ProvenanceRepository,
    UnitOfWork,
)
from agentscope.domain import RetentionPolicy
from agentscope.infrastructure.config.settings import Settings, get_settings
from agentscope.infrastructure.persistence.database import Database
from agentscope.infrastructure.persistence.queries import SqlMetricsQueryService
from agentscope.infrastructure.persistence.repositories import SqlProvenanceRepository
from agentscope.infrastructure.persistence.unit_of_work import SqlAlchemyUnitOfWork


class Container:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings: Settings = settings or get_settings()
        self.database: Database = Database(self.settings)
        # Règle métier de rétention des enregistrements bruts (I1.7).
        self.retention_policy = RetentionPolicy(mode=self.settings.raw_record_retention)

    # --- Points d'extension (à implémenter par les workstreams concernés) ---

    def build_unit_of_work(self) -> UnitOfWork:
        """UoW transactionnelle enveloppant les repositories (port I1.4, impl I1.5)."""
        return SqlAlchemyUnitOfWork(self.database)

    def build_provenance_repository(self) -> ProvenanceRepository:
        """Lecture « remonter à l'origine » (I1.7). Session dédiée, lecture seule."""
        return SqlProvenanceRepository(self.database.create_session())

    def build_llm_provider(self) -> object:
        """Adaptateur LLM choisi d'après `settings.llm_provider` (I3.2 / I3.5).

        Le contrat `LLMProvider` et la fabrique pilotée par configuration vivent
        dans l'infrastructure ; le conteneur se contente de les assembler.
        """
        raise NotImplementedError(
            f"Aucun adaptateur pour le fournisseur '{self.settings.llm_provider}' "
            "— voir issues I3.2 (fake), I3.3/I3.4 (réels), I3.5 (fabrique)."
        )

    def build_metrics_query_service(self) -> MetricsQueryService:
        """Service de lecture du dashboard (I1.9). Session dédiée, lecture seule."""
        return SqlMetricsQueryService(self.database.create_session())
