from __future__ import annotations

from fastapi import APIRouter

from agentscope.interfaces.api import fixtures
from agentscope.interfaces.api.schemas.chat import ChatReply, ChatRequest

router = APIRouter(tags=["chat"])


@router.post("/chat", response_model=ChatReply)
async def chat_about_mapping(payload: ChatRequest) -> ChatReply:
    """Aucun effet de bord DB (§5.3) — relais vers l'agent en I3.8."""
    return ChatReply(**fixtures.CHAT_REPLY)
