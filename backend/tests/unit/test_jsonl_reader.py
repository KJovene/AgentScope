from __future__ import annotations

from io import BytesIO

from agentscope.infrastructure.readers.jsonl_reader import JsonlReader


def test_jsonl_reader_streams_valid_objects() -> None:
    source = BytesIO(b'{"id": 1}\n{"id": 2}\n')

    records = list(JsonlReader().read(source))

    assert [record.payload for record in records] == [{"id": 1}, {"id": 2}]
    assert [record.index for record in records] == [0, 1]
    assert all(record.parse_error is None for record in records)
    assert records[0].sha256 != records[1].sha256


def test_jsonl_reader_keeps_invalid_lines_as_parse_errors() -> None:
    source = BytesIO(b'{"id": 1}\nnot-json\n{"id": 3}\n')

    records = list(JsonlReader().read(source))

    assert len(records) == 3
    assert records[1].index == 1
    assert records[1].payload == {}
    assert records[1].parse_error is not None
    assert records[0].parse_error is None
    assert records[2].payload == {"id": 3}


def test_jsonl_reader_rejects_non_object_and_empty_lines_without_crashing() -> None:
    source = BytesIO(b"[]\n\n42\n")

    records = list(JsonlReader().read(source))

    assert [record.index for record in records] == [0, 1, 2]
    assert all(record.payload == {} for record in records)
    assert all(record.parse_error is not None for record in records)


def test_jsonl_reader_supports_only_jsonl() -> None:
    reader = JsonlReader()

    assert reader.supports("jsonl")
    assert reader.supports("JSONL")
    assert not reader.supports("csv")