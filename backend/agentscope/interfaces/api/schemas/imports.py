from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class ImportReport(BaseModel):
    id: str
    source_id: str
    mapping_id: str
    status: str  # success | partial | failed (vocabulaire à figer avec I2.9)
    imported_count: int
    duplicate_count: int
    rejected_count: int
    missing_info_count: dict[str, int]
    imported_at: datetime


class RejectRecord(BaseModel):
    record_index: int
    reason_code: str
    reason_detail: str
    payload: dict
