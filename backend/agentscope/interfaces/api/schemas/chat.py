from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from agentscope.interfaces.api.schemas.mappings import MappingProposal


class ChatTurn(BaseModel):
    role: Literal["user", "assistant"]
    text: str


class ChatRequest(BaseModel):
    conversation_id: str
    # Historique complet de la conversation (dernier élément = nouveau message
    # de l'utilisateur). Le serveur ne conserve aucun état (§5.3).
    messages: list[ChatTurn] = Field(min_length=1)
    # Proposition de mapping en cours de discussion (issue de /analyze, non persistée).
    current_proposal: MappingProposal
    # Référence libre du fichier/profil analysé — informatif, non utilisé côté serveur.
    file_ref: str | None = None


class ChatReply(BaseModel):
    text: str
    # `None` si l'agent n'a pas révisé la proposition à ce tour.
    revised_proposal: MappingProposal | None = None
    # Toujours la proposition en vigueur après ce tour (révision ou proposition reçue).
    current_proposal: MappingProposal | None = None
