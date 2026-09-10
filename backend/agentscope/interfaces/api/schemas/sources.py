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


class RepositoryInput(BaseModel):
    name: str
    url: str | None = None
    language: str | None = None


class RepositoryResponse(BaseModel):
    name: str
    url: str | None = None
    language: str | None = None


class RepositoryRegisterResult(BaseModel):
    registered: int
    skipped: int
    total: int


class ModelPriceInput(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    model_name: str
    input_usd_per_mtok: float
    output_usd_per_mtok: float
    cached_usd_per_mtok: float | None = None


class ModelPriceResponse(ModelPriceInput):
    pass


class PricingUpsertResult(BaseModel):
    upserted: int
