from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class SessionRow(BaseModel):
    id: str
    source: str
    agent: str | None
    model: str | None
    started_at: datetime | None
    duration_ms: int | None
    n_model_calls: int
    n_tool_calls: int
    total_tokens: int | None
    cached_tokens: int | None
    total_cost_usd: float | None
    n_errors: int


class ModelCallRow(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    id: str
    model_name: str
    prompt_tokens: int | None
    completion_tokens: int | None
    total_tokens: int | None
    status: str
    started_at: datetime | None
    duration_ms: int | None


class ToolCallRow(BaseModel):
    id: str
    tool_name: str
    status: str
    started_at: datetime | None
    duration_ms: int | None


class SessionDetail(SessionRow):
    model_config = ConfigDict(protected_namespaces=())

    model_calls: list[ModelCallRow]
    tool_calls: list[ToolCallRow]
    raw_record_ref: str
