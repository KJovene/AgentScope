from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol, runtime_checkable


@dataclass(frozen=True, slots=True)
class SourceItem:
    id: str
    name: str
    description: str | None = None
    format: str | None = None
    session_count: int = 0
    created_at: datetime | None = None


@runtime_checkable
class SourcesQueryService(Protocol):
    def list_sources(self) -> list[SourceItem]: ...
