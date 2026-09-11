"""Politique de rétention des enregistrements bruts (issue I1.7)."""

from __future__ import annotations

import pytest

from agentscope.domain import RawRecord, RetentionMode, RetentionPolicy

RECORD = RawRecord(index=3, payload={"model": "claude", "tokens": 42}, sha256="abc123")


def test_full_keeps_every_payload() -> None:
    policy = RetentionPolicy(mode=RetentionMode.FULL)
    assert policy.apply(RECORD) is RECORD
    assert policy.apply(RECORD, rejected=True) is RECORD


def test_minimal_strips_payload_but_keeps_index_and_hash() -> None:
    policy = RetentionPolicy(mode=RetentionMode.MINIMAL)
    stripped = policy.apply(RECORD)
    assert stripped.payload == {}
    assert (stripped.index, stripped.sha256) == (3, "abc123")


def test_minimal_keeps_payload_of_rejected_records() -> None:
    policy = RetentionPolicy(mode=RetentionMode.MINIMAL)
    assert policy.apply(RECORD, rejected=True) is RECORD


def test_default_mode_is_full() -> None:
    assert RetentionPolicy().mode is RetentionMode.FULL


@pytest.mark.parametrize(
    ("mode", "rejected", "expected"),
    [
        (RetentionMode.FULL, False, True),
        (RetentionMode.FULL, True, True),
        (RetentionMode.MINIMAL, False, False),
        (RetentionMode.MINIMAL, True, True),
    ],
)
def test_keep_payload_matrix(mode: RetentionMode, rejected: bool, expected: bool) -> None:
    assert RetentionPolicy(mode=mode).keep_payload(rejected=rejected) is expected
