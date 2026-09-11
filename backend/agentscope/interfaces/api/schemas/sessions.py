from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class SessionItemResponse(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    session_id: int
    source_name: str
    agent_name: str | None = None
    repository_name: str | None = None
    started_at: datetime | None = None
    duration_ms: int | None = None
    model_call_count: int
    tool_call_count: int
    total_tokens: int | None = None
    total_cost_usd: float | None = None
    error_count: int


class TimelineEntryResponse(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    kind: str = Field(description="'model_call' ou 'tool_call'")
    sequence: int
    name: str = Field(description="Nom du modèle ou de l'outil")
    status: str
    error_type: str | None = None
    started_at: datetime | None = None
    ended_at: datetime | None = None
    duration_ms: int | None = None
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    total_tokens: int | None = None
    cost_usd: float | None = None


class SessionDetailResponse(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    session_id: int
    source_name: str
    external_id: str
    agent_name: str | None = None
    repository_name: str | None = None
    started_at: datetime | None = None
    ended_at: datetime | None = None
    duration_ms: int | None = None
    total_tokens: int | None = None
    total_cost_usd: float | None = None
    error_count: int
    has_raw_record: bool
    timeline: list[TimelineEntryResponse] = Field(default_factory=list)
