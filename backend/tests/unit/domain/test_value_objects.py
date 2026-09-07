"""Invariants des value objects."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from agentscope.domain import Interval, Provenance, TokenUsage
from agentscope.domain.errors import InvariantViolationError


class TestTokenUsage:
    def test_total_is_sum_when_both_present(self) -> None:
        assert TokenUsage(prompt_tokens=100, completion_tokens=40).total_tokens == 140

    def test_total_is_none_when_both_absent(self) -> None:
        assert TokenUsage().total_tokens is None

    def test_total_counts_present_side_only(self) -> None:
        assert TokenUsage(prompt_tokens=100).total_tokens == 100

    def test_negative_is_rejected(self) -> None:
        with pytest.raises(InvariantViolationError):
            TokenUsage(prompt_tokens=-1)

    def test_cached_cannot_exceed_prompt(self) -> None:
        with pytest.raises(InvariantViolationError):
            TokenUsage(prompt_tokens=10, cached_tokens=11)

    def test_cache_hit_ratio(self) -> None:
        assert TokenUsage(prompt_tokens=200, cached_tokens=50).cache_hit_ratio == 0.25

    def test_cache_hit_ratio_none_without_data(self) -> None:
        assert TokenUsage(prompt_tokens=200).cache_hit_ratio is None
        assert TokenUsage(cached_tokens=0).cache_hit_ratio is None


class TestInterval:
    def test_duration_ms(self) -> None:
        start = datetime(2026, 1, 1, 12, 0, 0, tzinfo=UTC)
        interval = Interval(started_at=start, ended_at=start + timedelta(seconds=1.5))
        assert interval.duration_ms == 1500

    def test_duration_none_when_incomplete(self) -> None:
        assert Interval(started_at=datetime(2026, 1, 1, tzinfo=UTC)).duration_ms is None
        assert Interval().duration_ms is None

    def test_end_before_start_is_rejected(self) -> None:
        start = datetime(2026, 1, 1, 12, 0, 0, tzinfo=UTC)
        with pytest.raises(InvariantViolationError):
            Interval(started_at=start, ended_at=start - timedelta(seconds=1))

    def test_naive_datetime_is_rejected(self) -> None:
        with pytest.raises(ValueError, match="UTC"):
            Interval(started_at=datetime(2026, 1, 1, 12, 0, 0))  # noqa: DTZ001


class TestProvenance:
    def test_requires_hash(self) -> None:
        with pytest.raises(InvariantViolationError):
            Provenance(record_index=0, record_sha256="  ")

    def test_negative_index_rejected(self) -> None:
        with pytest.raises(InvariantViolationError):
            Provenance(record_index=-1, record_sha256="abc")
