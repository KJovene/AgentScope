from __future__ import annotations

from datetime import UTC, datetime

from agentscope.domain import RawRecord
from agentscope.infrastructure.profiling.field_profiler import DefaultFieldProfiler


def _record(index: int, payload: dict) -> RawRecord:
    return RawRecord(index=index, payload=payload, sha256=f"hash-{index}")


def test_profiler_handles_nested_paths_types_nulls_cardinality_and_samples() -> None:
    records = [
        _record(0, {"id": 1, "user": {"name": "Alice", "email": None}, "tags": ["a"]}),
        _record(1, {"id": 2, "user": {"name": "Bob", "email": "b@example.com"}, "tags": ["b"]}),
        _record(2, {"id": 1, "user": {"name": "Alice"}, "tags": None}),
    ]

    profile = DefaultFieldProfiler().profile(records, sample_size=2)

    assert profile.record_count == 3
    assert [field.path for field in profile.fields] == [
        "id",
        "tags",
        "user.email",
        "user.name",
    ]
    assert profile.by_path("id").inferred_type == "int"
    assert profile.by_path("id").distinct_count == 2
    assert profile.by_path("id").sample_values == (1, 2)
    assert profile.by_path("user.email").null_ratio == 2 / 3
    assert profile.by_path("tags").inferred_type == "array"


def test_profiler_infers_mixed_and_datetime_types_deterministically() -> None:
    records = [
        _record(0, {"value": 1, "created_at": datetime(2024, 1, 1, tzinfo=UTC)}),
        _record(1, {"value": "1", "created_at": datetime(2024, 1, 2, tzinfo=UTC)}),
    ]

    profile = DefaultFieldProfiler().profile(records, sample_size=1)

    assert profile.by_path("value").inferred_type == "mixed"
    assert profile.by_path("created_at").inferred_type == "datetime"
    assert profile.by_path("created_at").sample_values == (datetime(2024, 1, 1, tzinfo=UTC),)


def test_profiler_rejects_negative_sample_size_and_supports_empty_input() -> None:
    profiler = DefaultFieldProfiler()

    assert profiler.profile([], sample_size=2).record_count == 0
    assert profiler.profile([], sample_size=2).fields == ()

    try:
        profiler.profile([], sample_size=-1)
    except ValueError as error:
        assert "sample_size" in str(error)
    else:
        raise AssertionError("negative sample_size was accepted")


def test_profiler_masque_les_donnees_sensibles_dans_les_echantillons() -> None:
    record = _record(
        0,
        {
            "email": "alice@example.com",
            "credentials": "api_key=fixture-value-to-redact",
            "path": r"C:\Users\alice\project\trace.jsonl",
        },
    )

    profile = DefaultFieldProfiler().profile([record], sample_size=1)

    samples = [value for field in profile.fields for value in field.sample_values]
    assert "alice@example.com" not in samples
    assert all("fixture-value-to-redact" not in str(value) for value in samples)
    assert all(r"C:\Users\alice" not in str(value) for value in samples)
    assert all("[REDACTED]" in str(value) for value in samples)
