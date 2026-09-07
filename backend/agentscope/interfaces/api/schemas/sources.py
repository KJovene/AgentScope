from __future__ import annotations

from pydantic import BaseModel


class Source(BaseModel):
    id: str
    name: str


class DataQuality(BaseModel):
    source_id: str
    imported_count: int
    duplicate_count: int
    rejected_count: int
    completeness_ratio: float
