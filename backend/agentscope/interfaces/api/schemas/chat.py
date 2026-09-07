from __future__ import annotations

from pydantic import BaseModel

from agentscope.interfaces.api.schemas.mappings import MappingProposal


class ChatRequest(BaseModel):
    conversation_id: str
    message: str
    file_ref: str


class ChatReply(BaseModel):
    text: str
    revised_proposal: MappingProposal | None = None
