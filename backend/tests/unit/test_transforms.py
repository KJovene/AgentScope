from __future__ import annotations

import pytest

from agentscope.application.mapping.transforms import TransformError, apply_transform
from agentscope.domain import InvalidMappingError


@pytest.mark.parametrize(
    ("name", "value", "args", "expected"),
    [
        ("identity", "x", {}, "x"),
        ("to_int", "42", {}, 42),
        ("to_float", "4.5", {}, 4.5),
        ("lower", "Hello", {}, "hello"),
        ("upper", "Hello", {}, "HELLO"),
        ("trim", "  hello  ", {}, "hello"),
        ("json_stringify", {"b": 2, "a": 1}, {}, '{"a":1,"b":2}'),
        ("const", "ignored", {"value": "fixed"}, "fixed"),
        ("map_enum", "ok", {"mapping": {"ok": "success"}, "default": "unknown"}, "success"),
        ("map_enum", "other", {"mapping": {"ok": "success"}, "default": "unknown"}, "unknown"),
        ("split", "a/b/c", {"sep": "/", "index": 1}, "b"),
        ("regex_extract", "run-123", {"pattern": r"run-(\d+)"}, "123"),
        ("cents_to_usd", 1234, {}, 12.34),
        ("ms_to_s", 2500, {}, 2.5),
    ],
)
def test_apply_transform_nominal(name: str, value: object, args: dict, expected: object) -> None:
    assert apply_transform(name, value, args) == expected


def test_to_iso8601_supports_epoch_ms_and_normalizes_to_utc() -> None:
    result = apply_transform("to_iso8601", 0, {"unit": "epoch_ms"})

    assert result == "1970-01-01T00:00:00Z"


def test_to_iso8601_supports_iso_input() -> None:
    result = apply_transform(
        "to_iso8601", "2024-01-02 03:04", {"unit": "iso", "input_format": "%Y-%m-%d %H:%M"}
    )

    assert result == "2024-01-02T03:04:00Z"


def test_coalesce_reads_first_non_null_context_field() -> None:
    result = apply_transform(
        "coalesce",
        args={"fields": ["missing", "fallback", "last"]},
        context={"fallback": "value", "last": "ignored"},
    )

    assert result == "value"


def test_nullable_transforms_preserve_none() -> None:
    assert apply_transform("to_int", None) is None
    assert apply_transform("lower", None) is None
    assert apply_transform("to_iso8601", None, {"unit": "epoch_s"}) is None


def test_unknown_transform_is_rejected() -> None:
    with pytest.raises(InvalidMappingError, match="inconnue"):
        apply_transform("execute_python", "__import__('os')")


@pytest.mark.parametrize(
    ("name", "value", "args"),
    [
        ("to_int", "not-a-number", {}),
        ("lower", 42, {}),
        ("const", None, {}),
        ("coalesce", None, {"fields": ["a"]}),
        ("split", "a", {"sep": "/", "index": 3}),
        (
            "regex_extract",
            "x",
            {
                "pattern": "(",
            },
        ),
    ],
)
def test_invalid_transform_input_is_rejected(name: str, value: object, args: dict) -> None:
    with pytest.raises(TransformError):
        apply_transform(name, value, args)
