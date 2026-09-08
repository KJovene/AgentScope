"""Route ``POST /chat`` (issue I4.4) — échange avec l'agent sur une proposition
de mapping.

Branchée sur ``MappingWorkbenchService.chat`` (``ChatAboutMapping``, I3.8).
**Aucun effet de bord DB** : le serveur ne conserve aucun état, le client
renvoie l'historique et la proposition en cours à chaque tour (§5.3).
"""

from __future__ import annotations

import dataclasses
from typing import Any

from fastapi import APIRouter

from agentscope.application.ports.llm_provider import (
    ChatMessage,
    FieldExplanation as PortFieldExplanation,
    MappingProposal as PortMappingProposal,
)
from agentscope.interfaces.api.dependencies import WorkbenchServiceDep
from agentscope.interfaces.api.schemas.chat import ChatReply, ChatRequest
from agentscope.interfaces.api.schemas.mappings import MappingProposal as ProposalSchema

router = APIRouter(tags=["chat"])


def _to_port_proposal(p: ProposalSchema) -> PortMappingProposal:
    return PortMappingProposal(
        definition=p.definition,
        explanations=[
            PortFieldExplanation(
                target_field=e.target_field,
                source_field=e.source_field,
                rationale=e.rationale,
                confidence=e.confidence,
            )
            for e in p.explanations
        ],
        ambiguities=list(p.ambiguities),
        unmapped_fields=list(p.unmapped_fields),
    )


def _to_schema_proposal(p: Any) -> ProposalSchema:
    return ProposalSchema(**dataclasses.asdict(p))


@router.post("/chat", response_model=ChatReply)
async def chat_about_mapping(
    payload: ChatRequest,
    service: WorkbenchServiceDep,
) -> ChatReply:
    result = service.chat(
        conversation_id=payload.conversation_id,
        messages=[ChatMessage(role=m.role, text=m.text) for m in payload.messages],
        current_proposal=_to_port_proposal(payload.current_proposal),
    )
    return ChatReply(
        text=result.text,
        revised_proposal=(
            _to_schema_proposal(result.revised_proposal)
            if result.revised_proposal is not None
            else None
        ),
        current_proposal=_to_schema_proposal(result.current_proposal),
    )
