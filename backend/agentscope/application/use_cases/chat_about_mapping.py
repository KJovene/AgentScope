"""Cas d'utilisation ``ChatAboutMapping`` (issue I3.8).

Discute avec l'agent d'une proposition de mapping en cours : il explique ses
choix, signale les ambiguïtés, propose éventuellement une révision.

Ce use case ne dépend d'aucun repository ni d'aucune unité de travail : il est
**structurellement** incapable d'écrire en base, quoi que renvoie le
fournisseur IA — ce n'est pas une vérification à l'exécution, c'est une
propriété de sa signature.
"""

from __future__ import annotations

from dataclasses import dataclass

from agentscope.application.mapping.target_schema import TARGET_SCHEMA
from agentscope.application.ports.llm_provider import (
    ChatMessage,
    LLMProvider,
    MappingContext,
    MappingProposal,
)


@dataclass(frozen=True, slots=True)
class ChatResult:
    """Résultat d'un tour d'échange : réponse + proposition à jour.

    ``revised_proposal`` vaut ``None`` quand l'agent n'a pas révisé la
    proposition à ce tour ; ``current_proposal`` est toujours la version en
    vigueur (révision si elle existe, sinon la proposition reçue).
    """

    text: str
    current_proposal: MappingProposal
    revised_proposal: MappingProposal | None = None

    @property
    def ambiguities(self) -> list[str]:
        return self.current_proposal.ambiguities


class ChatAboutMapping:
    """Échange multi-tours sur une proposition de mapping, sans écriture DB."""

    def __init__(self, llm_provider: LLMProvider) -> None:
        self._llm_provider = llm_provider

    def execute(
        self,
        conversation_id: str,
        messages: list[ChatMessage],
        current_proposal: MappingProposal,
    ) -> ChatResult:
        context = MappingContext(proposal=current_proposal, target_schema=TARGET_SCHEMA)
        reply = self._llm_provider.chat(conversation_id, messages, context)

        updated_proposal = reply.revised_proposal or current_proposal
        return ChatResult(
            text=reply.text,
            current_proposal=updated_proposal,
            revised_proposal=reply.revised_proposal,
        )
