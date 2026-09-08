from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class FieldProfile(BaseModel):
    path: str
    inferred_type: str
    null_ratio: float
    distinct_count: int
    sample_values: list[object]


class FieldProfileSet(BaseModel):
    record_count: int
    fields: list[FieldProfile]


class FieldExplanation(BaseModel):
    target_field: str
    source_field: str | None
    rationale: str
    confidence: float


class MappingProposal(BaseModel):
    definition: dict
    explanations: list[FieldExplanation]
    ambiguities: list[str]
    unmapped_fields: list[str]


class AnalyzeResponse(BaseModel):
    profile: FieldProfileSet
    proposal: MappingProposal


class MappingCreate(BaseModel):
    name: str
    source_format: str
    definition: dict


class MappingUpdate(BaseModel):
    definition: dict


class Mapping(BaseModel):
    mapping_id: str  # = name (identifiant public, aligné sur le champ `mapping_id` de /imports)
    name: str
    version: int
    source_name: str
    source_format: str
    definition: dict
    is_active: bool
    created_at: datetime
    created_by: str | None = None


class PreviewRow(BaseModel):
    entity: str  # session | model_call | tool_call
    row: dict


class PreviewResult(BaseModel):
    rows: list[PreviewRow]
    rejects: list[dict]
