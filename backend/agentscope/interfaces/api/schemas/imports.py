from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ImportReport(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    id: str
    source_id: str | None = None
    mapping_id: str
    status: str
    imported_count: int
    duplicate_count: int
    rejected_count: int
    missing_info_count: dict[str, int] | int = Field(default_factory=dict)
    imported_at: datetime | None = None


class RejectRecord(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    record_index: int = 0
    reason_code: str = "REJECTED_RECORD"
    reason_detail: str = ""
    payload: dict[str, Any] = Field(default_factory=dict)

    # Compatibilité avec ImportRejectItem
    id: str | None = None
    import_batch_id: str | None = None
    line_number: int | None = None
    reason: str | None = None
    raw_record: str | None = None
    rejected_at: datetime | None = None
