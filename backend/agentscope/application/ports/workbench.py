"""Port ``MappingWorkbenchService`` : opérations « atelier de mapping » (§5.3).

Analyse d'un fichier inconnu et prévisualisation d'un mapping sur un échantillon.
Aucune persistance : tout est éphémère. Le contenu du fichier arrive en octets ;
l'implémentation choisit le lecteur d'après le nom du fichier.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from agentscope.application.ports.llm_provider import ChatMessage, MappingProposal
from agentscope.application.use_cases.analyze_unknown_file import AnalysisResult
from agentscope.application.use_cases.chat_about_mapping import ChatResult
from agentscope.application.use_cases.preview_mapping import PreviewReport


@runtime_checkable
class MappingWorkbenchService(Protocol):
    def analyze(self, filename: str, content: bytes) -> AnalysisResult:
        """Fichier inconnu → profil + proposition de mapping validée."""
        ...

    def preview(
        self,
        filename: str,
        content: bytes,
        definition: dict,
        sample_size: int = 50,
    ) -> PreviewReport:
        """Dry-run de normalisation d'un mapping sur un échantillon."""
        ...

    def chat(
        self,
        conversation_id: str,
        messages: list[ChatMessage],
        current_proposal: MappingProposal,
    ) -> ChatResult:
        """Un tour d'échange sur une proposition de mapping — aucune écriture DB."""
        ...
