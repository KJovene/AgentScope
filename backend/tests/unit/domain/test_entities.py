"""Invariants des entités et cohérence des relations par clé naturelle."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from agentscope.domain import (
    CallStatus,
    ErrorType,
    FieldProfile,
    FileFormat,
    ImportBatch,
    ModelCall,
    Provenance,
    Session,
    SourceMapping,
    ToolCall,
)
from agentscope.domain.errors import InvariantViolationError

PROV = Provenance(record_index=3, record_sha256="deadbeef")
NOW = datetime(2026, 1, 1, tzinfo=UTC)


def test_session_requires_external_id() -> None:
    with pytest.raises(InvariantViolationError):
        Session(source_name="tracelab", external_id="", provenance=PROV)


def test_model_call_links_to_session_by_natural_key() -> None:
    session = Session(source_name="tracelab", external_id="s-1", provenance=PROV)
    call = ModelCall(
        source_name="tracelab",
        session_external_id="s-1",
        sequence=0,
        model_name="claude-sonnet",
        provenance=PROV,
    )
    assert (call.source_name, call.session_external_id) == (
        session.source_name,
        session.external_id,
    )


def test_model_call_rejects_empty_model_name() -> None:
    with pytest.raises(InvariantViolationError):
        ModelCall(
            source_name="s",
            session_external_id="s-1",
            sequence=0,
            model_name="  ",
            provenance=PROV,
        )


def test_model_call_rejects_negative_sequence() -> None:
    with pytest.raises(InvariantViolationError):
        ModelCall(
            source_name="s",
            session_external_id="s-1",
            sequence=-1,
            model_name="m",
            provenance=PROV,
        )


def test_error_status_requires_error_type() -> None:
    with pytest.raises(InvariantViolationError):
        ModelCall(
            source_name="s",
            session_external_id="s-1",
            sequence=0,
            model_name="m",
            provenance=PROV,
            status=CallStatus.ERROR,
        )


def test_success_status_forbids_error_type() -> None:
    with pytest.raises(InvariantViolationError):
        ToolCall(
            source_name="s",
            session_external_id="s-1",
            sequence=0,
            tool_name="bash",
            provenance=PROV,
            status=CallStatus.SUCCESS,
            error_type=ErrorType.TOOL_ERROR,
        )


def test_tool_call_error_is_valid_with_error_type() -> None:
    call = ToolCall(
        source_name="s",
        session_external_id="s-1",
        sequence=1,
        tool_name="bash",
        provenance=PROV,
        status=CallStatus.ERROR,
        error_type=ErrorType.TOOL_ERROR,
    )
    assert call.is_error is True


def test_import_batch_defaults_counts_to_zero() -> None:
    batch = ImportBatch(
        source_name="tracelab",
        original_filename="sessions.jsonl",
        file_sha256="abc123",
        file_format=FileFormat.JSONL,
        imported_at=NOW,
    )
    assert batch.total_processed == 0


def test_import_batch_rejects_negative_count() -> None:
    with pytest.raises(InvariantViolationError):
        ImportBatch(
            source_name="tracelab",
            original_filename="f.jsonl",
            file_sha256="abc",
            file_format=FileFormat.JSONL,
            imported_at=NOW,
            rejected_count=-1,
        )


def test_source_mapping_requires_version_ge_1() -> None:
    with pytest.raises(InvariantViolationError):
        SourceMapping(
            name="tracelab",
            version=0,
            source_name="tracelab",
            source_format=FileFormat.JSONL,
            definition={"entities": {}},
            created_at=NOW,
        )


def test_field_profile_null_ratio_bounds() -> None:
    FieldProfile(path="usage.input", inferred_type="int", null_ratio=0.0, distinct_count=5)
    with pytest.raises(InvariantViolationError):
        FieldProfile(path="x", inferred_type="int", null_ratio=1.5, distinct_count=0)


def test_entities_are_immutable() -> None:
    session = Session(source_name="tracelab", external_id="s-1", provenance=PROV)
    with pytest.raises(AttributeError):
        session.external_id = "s-2"  # type: ignore[misc]
