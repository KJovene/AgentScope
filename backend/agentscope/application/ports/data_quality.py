from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol, runtime_checkable


@dataclass(frozen=True, slots=True)
class DataQualityBatchItem:
    import_batch_id: str
    source_name: str
    imported_count: int
    duplicate_count: int
    rejected_count: int
    missing_info_count: int
    completeness_rate: float | None = None
    imported_at: datetime | None = None


@runtime_checkable
class DataQualityQueryService(Protocol):
    def get_quality_metrics(self, source_id: str | None = None) -> list[DataQualityBatchItem]: ...
