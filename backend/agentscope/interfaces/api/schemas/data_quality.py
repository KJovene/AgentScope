from __future__ import annotations

from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class DataQualityBatchMetrics(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    import_batch_id: str
    source_name: str
    imported_count: int
    duplicate_count: int
    rejected_count: int
    missing_info_count: int
    completeness_rate: float | None = Field(
        default=None, description="Ratio de complétude (0..1), null si indisponible"
    )
    imported_at: datetime | None = None


class DataQualityResponse(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    batches: list[DataQualityBatchMetrics] = Field(default_factory=list)
