"""Fournisseur IA factice (I3.2) : aucun appel réseau, déterministe.

Sert de doublure pour les tests et la CI, en attendant les adaptateurs réels
(Anthropic I3.3, OpenAI-compatible I3.4).
"""

from __future__ import annotations

from agentscope.application.ports.llm_provider import (
    ChatMessage,
    ChatReply,
    FieldExplanation,
    FieldProfileSet,
    MappingContext,
    MappingProposal,
    TargetSchema,
)


class FakeLLMProvider:
    """Implémentation déterministe de `LLMProvider` : propose un mapping identité.

    Pour un même échantillon, `propose_mapping` renvoie toujours la même
    `MappingProposal` — aucun état interne, aucun appel externe.
    """

    name = "fake"

    def propose_mapping(
        self,
        profile: FieldProfileSet,
        sample: list[dict[str, object]],
        target_schema: TargetSchema,
    ) -> MappingProposal:
        fields = sorted({key for record in sample for key in record})

        explanations = [
            FieldExplanation(
                target_field=field,
                source_field=field,
                rationale="Fake provider : mapping identité déduit de l'échantillon.",
                confidence=1.0,
            )
            for field in fields
        ]

        definition = {
            "source_format": "jsonl",
            "entities": {
                "record": {
                    "iterate": {"path": "", "where": []},
                    "fields": {field: {"from": field, "transform": "identity"} for field in fields},
                }
            },
        }

        return MappingProposal(
            definition=definition,
            explanations=explanations,
            ambiguities=[],
            unmapped_fields=[],
        )

    def chat(
        self,
        conversation_id: str,
        messages: list[ChatMessage],
        context: MappingContext,
    ) -> ChatReply:
        return ChatReply(
            text="Fake provider : aucune analyse réelle, pas de révision proposée.",
            revised_proposal=None,
        )
