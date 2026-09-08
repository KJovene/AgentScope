from __future__ import annotations

from datetime import datetime
from pydantic import BaseModel, ConfigDict


class SourceResponse(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    id: str
    name: str
    description: str | None = None
    format: str | None = None
    session_count: int = 0
    created_at: datetime | None = None
