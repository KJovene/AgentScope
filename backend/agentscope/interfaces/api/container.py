"""Point de composition (composition root).

C'est le SEUL endroit où les cas d'utilisation sont reliés à leurs implémentations
concrètes. Aujourd'hui le conteneur ne câble que la configuration et la base ; les
fabriques de repositories, d'unité de travail et de fournisseur IA sont des points
d'extension explicites, remplis par les EPICs 1 à 3.
"""

from __future__ import annotations

from agentscope.infrastructure.config.settings import Settings, get_settings
from agentscope.infrastructure.persistence.database import Database


class Container:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings: Settings = settings or get_settings()
        self.database: Database = Database(self.settings)

    # --- Points d'extension (à implémenter par les workstreams concernés) ---

    def build_unit_of_work(self) -> object:
        """UoW transactionnelle enveloppant les repositories (I1.4 / I1.5)."""
        raise NotImplementedError("Unité de travail non branchée — voir issue I1.5.")

    def build_llm_provider(self) -> object:
        """Adaptateur LLM choisi d'après `settings.llm_provider` (I3.2 / I3.5).

        Le contrat `LLMProvider` et la fabrique pilotée par configuration vivent
        dans l'infrastructure ; le conteneur se contente de les assembler.
        """
        raise NotImplementedError(
            f"Aucun adaptateur pour le fournisseur '{self.settings.llm_provider}' "
            "— voir issues I3.2 (fake), I3.3/I3.4 (réels), I3.5 (fabrique)."
        )

    def build_metrics_query_service(self) -> object:
        """Service de lecture du dashboard (I1.9)."""
        raise NotImplementedError("MetricsQueryService non branché — voir issue I1.9.")
