"""Port LLMProvider : abstraction IA (§5.2 du plan).

Contrat fige le Jour 1. Les fournisseurs concrets (Anthropic, OpenAI-compatible,
Fake) implementent ce Protocol dans agentscope.infrastructure.llm.*.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol, runtime_checkable

# Types fournis par d'autres ports pas encore codes (WS-B pour le profileur,
# I3.6/I3.8 pour le chat). A remplacer par le vrai import des qu'ils existent :
#   from agentscope.application.ports.profiler import FieldProfileSet
FieldProfileSet = Any
TargetSchema = Any
ChatMessage = Any
MappingContext = Any


@dataclass(frozen=True)
class FieldExplanation:
    """Justification d'un champ propose par l'agent dans un mapping."""

    target_field: str  # ex. "model_call.prompt_tokens"
    source_field: str | None
    rationale: str
    confidence: float  # 0..1, estime par l'agent


@dataclass(frozen=True)
class MappingProposal:
    """Proposition de mapping generee par l'agent (contrat commun)."""

    definition: dict[str, Any]  # conforme au contrat de mapping (§5.1), non persiste tel quel
    explanations: list[FieldExplanation]
    ambiguities: list[str]  # points que l'agent signale comme incertains
    unmapped_fields: list[str]


@dataclass(frozen=True)
class ChatReply:
    """Reponse de l'agent lors d'un echange sur un mapping."""

    text: str
    revised_proposal: MappingProposal | None


@runtime_checkable
class LLMProvider(Protocol):
    """Fournisseur IA interchangeable : propose un mapping, discute dessus."""

    name: str

    def propose_mapping(
        self,
        profile: FieldProfileSet,
        sample: list[dict[str, Any]],
        target_schema: TargetSchema,
    ) -> MappingProposal: ...

    def chat(
        self,
        conversation_id: str,
        messages: list[ChatMessage],
        context: MappingContext,
    ) -> ChatReply: ...
