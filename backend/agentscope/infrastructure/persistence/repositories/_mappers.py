"""Conversions entité du domaine <-> valeurs de ligne ORM.

Regroupées ici pour rester DRY et pour que les classes repository ne fassent
que de l'orchestration. Les clés étrangères techniques sont résolues par
l'appelant et passées en argument.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from agentscope.domain import (
    FieldProfile,
    FileFormat,
    ImportBatch,
    ImportReject,
    ImportStatus,
    ModelCall,
    RawRecord,
    RejectReason,
    Repository,
    Session,
    Source,
    SourceMapping,
    ToolCall,
)


def _utc(value: datetime | None) -> datetime | None:
    """SQLite relit les timestamps sans fuseau : on rattache UTC (règle §5.4)."""
    if value is None:
        return None
    return value if value.tzinfo is not None else value.replace(tzinfo=UTC)


# --- Source -----------------------------------------------------------------


def source_to_values(source: Source) -> dict[str, Any]:
    return {
        "name": source.name,
        "display_name": source.display_name,
        "homepage_url": source.homepage_url,
    }


def row_to_source(row: Any) -> Source:
    return Source(
        name=row.name,
        display_name=row.display_name,
        homepage_url=row.homepage_url,
    )


# --- Repository (dépôt de code) -------------------------------------------------


def repository_to_values(repo: Repository, source_id: int) -> dict[str, Any]:
    return {
        "source_id": source_id,
        "name": repo.name,
        "url": repo.url,
        "language": repo.language,
    }


def row_to_repository(row: Any, source_name: str) -> Repository:
    return Repository(
        source_name=source_name,
        name=row.name,
        url=row.url,
        language=row.language,
    )


# --- SourceMapping ---------------------------------------------------------------


def mapping_to_values(mapping: SourceMapping, source_id: int) -> dict[str, Any]:
    return {
        "source_id": source_id,
        "name": mapping.name,
        "version": mapping.version,
        "source_format": mapping.source_format.value,
        "definition_json": mapping.definition,
        "is_active": mapping.is_active,
        "created_at": mapping.created_at,
        "created_by": mapping.created_by,
    }


def row_to_mapping(row: Any, source_name: str) -> SourceMapping:
    created_at = _utc(row.created_at)
    assert created_at is not None
    return SourceMapping(
        name=row.name,
        version=row.version,
        source_name=source_name,
        source_format=FileFormat(row.source_format),
        definition=dict(row.definition_json),
        created_at=created_at,
        is_active=row.is_active,
        created_by=row.created_by,
    )


# --- ImportBatch ---------------------------------------------------------------


def import_batch_to_values(batch: ImportBatch, source_id: int, mapping_id: int) -> dict[str, Any]:
    return {
        "source_id": source_id,
        "mapping_id": mapping_id,
        "original_filename": batch.original_filename,
        "file_sha256": batch.file_sha256,
        "file_format": batch.file_format.value,
        "status": batch.status.value,
        "imported_at": batch.imported_at,
        "record_count": batch.record_count,
        "imported_count": batch.imported_count,
        "duplicate_count": batch.duplicate_count,
        "rejected_count": batch.rejected_count,
        "missing_info_count": batch.missing_info_count,
    }


def import_batch_update_values(batch: ImportBatch) -> dict[str, Any]:
    return {
        "status": batch.status.value,
        "record_count": batch.record_count,
        "imported_count": batch.imported_count,
        "duplicate_count": batch.duplicate_count,
        "rejected_count": batch.rejected_count,
        "missing_info_count": batch.missing_info_count,
    }


def row_to_import_batch(row: Any, source_name: str, mapping_name: str | None) -> ImportBatch:
    imported_at = _utc(row.imported_at)
    assert imported_at is not None
    return ImportBatch(
        source_name=source_name,
        original_filename=row.original_filename,
        file_sha256=row.file_sha256,
        file_format=FileFormat(row.file_format),
        imported_at=imported_at,
        status=ImportStatus(row.status),
        mapping_name=mapping_name,
        record_count=row.record_count,
        imported_count=row.imported_count,
        duplicate_count=row.duplicate_count,
        rejected_count=row.rejected_count,
        missing_info_count=row.missing_info_count,
    )


# --- ImportReject ------------------------------------------------------------


def import_reject_to_values(reject: ImportReject, batch_id: int) -> dict[str, Any]:
    return {
        "import_batch_id": batch_id,
        "record_index": reject.record_index,
        "target_entity": None,
        "reason_code": reject.reason.value,
        "reason_detail": reject.detail,
        "payload_json": reject.payload or None,
    }


def row_to_import_reject(row: Any) -> ImportReject:
    return ImportReject(
        record_index=row.record_index,
        reason=RejectReason(row.reason_code),
        detail=row.reason_detail,
        payload=dict(row.payload_json) if row.payload_json else {},
    )


# --- Enregistrements normalisés (écriture seule) --------------------------------


def raw_record_to_values(record: RawRecord, batch_id: int) -> dict[str, Any]:
    return {
        "import_batch_id": batch_id,
        "record_index": record.index,
        "record_sha256": record.sha256,
        "payload_json": record.payload or None,
    }


def session_to_values(
    session: Session,
    *,
    source_id: int,
    import_batch_id: int,
    raw_record_id: int | None,
    repository_id: int | None,
) -> dict[str, Any]:
    return {
        "source_id": source_id,
        "import_batch_id": import_batch_id,
        "raw_record_id": raw_record_id,
        "repository_id": repository_id,
        "external_id": session.external_id,
        "agent_name": session.agent_name,
        "started_at": session.interval.started_at,
        "ended_at": session.interval.ended_at,
    }


def model_call_to_values(
    call: ModelCall,
    *,
    session_id: int,
    import_batch_id: int,
    raw_record_id: int | None,
) -> dict[str, Any]:
    return {
        "session_id": session_id,
        "import_batch_id": import_batch_id,
        "raw_record_id": raw_record_id,
        "sequence": call.sequence,
        "model_name": call.model_name,
        "provider": call.provider,
        "prompt_tokens": call.tokens.prompt_tokens,
        "completion_tokens": call.tokens.completion_tokens,
        "cached_tokens": call.tokens.cached_tokens,
        "total_tokens": call.tokens.total_tokens,
        "cost_usd": call.cost_usd,
        "started_at": call.interval.started_at,
        "ended_at": call.interval.ended_at,
        "status": call.status.value,
        "error_type": call.error_type.value if call.error_type is not None else None,
    }


def tool_call_to_values(
    call: ToolCall,
    *,
    session_id: int,
    import_batch_id: int,
    raw_record_id: int | None,
    model_call_id: int | None,
) -> dict[str, Any]:
    return {
        "session_id": session_id,
        "model_call_id": model_call_id,
        "import_batch_id": import_batch_id,
        "raw_record_id": raw_record_id,
        "sequence": call.sequence,
        "tool_name": call.tool_name,
        "status": call.status.value,
        "error_type": call.error_type.value if call.error_type is not None else None,
        "started_at": call.interval.started_at,
        "ended_at": call.interval.ended_at,
        "input_bytes": call.input_bytes,
        "output_bytes": call.output_bytes,
    }


def field_profile_to_values(profile: FieldProfile, batch_id: int) -> dict[str, Any]:
    return {
        "import_batch_id": batch_id,
        "path": profile.path,
        "inferred_type": profile.inferred_type,
        "null_ratio": profile.null_ratio,
        "distinct_count": profile.distinct_count,
        "sample_values_json": list(profile.sample_values),
    }
