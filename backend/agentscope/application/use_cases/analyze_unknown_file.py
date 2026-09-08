"""Cas d'utilisation ``AnalyzeUnknownFile`` (issue I3.7).

Profile un fichier inconnu, demande à un ``LLMProvider`` de proposer un
mapping, puis valide cette proposition contre le contrat de mapping (I2.13)
avant de la renvoyer. Une proposition non conforme ne remonte jamais telle
quelle : elle devient une erreur explicite.
"""

from __future__ import annotations

from dataclasses import dataclass

from agentscope.application.mapping.target_schema import TARGET_SCHEMA
from agentscope.application.mapping.validator import parse_and_validate
from agentscope.application.ports.llm_provider import LLMProvider, MappingProposal
from agentscope.application.ports.profiler import FieldProfiler
from agentscope.domain import (
    DomainError,
    FieldProfileSet,
    InvalidMappingError,
    RawRecord,
)


class AnalysisFailedError(DomainError):
    """Le fournisseur IA n'a pas produit un mapping conforme au contrat."""


@dataclass(frozen=True, slots=True)
class AnalysisResult:
    """Résultat renvoyé à l'appelant : la proposition validée + le profil calculé."""

    proposal: MappingProposal
    profile: FieldProfileSet


class AnalyzeUnknownFile:
    """Profile un fichier inconnu et renvoie une proposition de mapping validée."""

    def __init__(
        self,
        profiler: FieldProfiler,
        llm_provider: LLMProvider,
        sample_size: int = 20,
    ) -> None:
        self._profiler = profiler
        self._llm_provider = llm_provider
        self._sample_size = sample_size

    def execute(self, records: list[RawRecord]) -> AnalysisResult:
        profile = self._profiler.profile(records, self._sample_size)
        # Échantillon brut (enregistrements complets, pas seulement les champs
        # profilés) : le filtrage des données sensibles est de la responsabilité
        # du LLMProvider concret (via le PromptBuilder, I3.6), pas de ce use case.
        sample = [record.payload for record in records[: self._sample_size]]

        proposal = self._llm_provider.propose_mapping(
            profile=profile,
            sample=sample,
            target_schema=TARGET_SCHEMA,
        )

        try:
            parse_and_validate(proposal.definition)
        except InvalidMappingError as exc:
            raise AnalysisFailedError(
                f"Le fournisseur « {self._llm_provider.name} » a proposé un mapping "
                f"non conforme au contrat : {exc}"
            ) from exc

        return AnalysisResult(proposal=proposal, profile=profile)
