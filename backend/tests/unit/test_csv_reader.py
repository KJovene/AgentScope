from __future__ import annotations

from io import BytesIO

from agentscope.infrastructure.readers.csv_reader import CsvReader


def test_csv_reader_detects_comma_delimiter_and_headers() -> None:
    source = BytesIO(b"id,name\n1,Alice\n2,Bob\n")

    records = list(CsvReader().read(source))

    assert [record.payload for record in records] == [
        {"id": "1", "name": "Alice"},
        {"id": "2", "name": "Bob"},
    ]
    assert [record.index for record in records] == [0, 1]
    assert all(record.parse_error is None for record in records)


def test_csv_reader_detects_semicolon_delimiter() -> None:
    source = BytesIO("id;message\n1;Bonjour\n".encode("utf-8"))

    records = list(CsvReader().read(source))

    assert records[0].payload == {"id": "1", "message": "Bonjour"}


def test_csv_reader_decodes_utf8_bom_and_quoted_values() -> None:
    source = BytesIO("\ufeffname,description\nZoé,\"a,b\"\n".encode("utf-8"))

    records = list(CsvReader().read(source))

    assert records[0].payload == {"name": "Zoé", "description": "a,b"}


def test_csv_reader_keeps_rows_with_wrong_column_count_as_errors() -> None:
    source = BytesIO(b"id,name\n1,Alice\n2\n3,Bob\n")

    records = list(CsvReader().read(source))

    assert len(records) == 3
    assert records[1].payload == {}
    assert records[1].parse_error is not None
    assert records[2].payload == {"id": "3", "name": "Bob"}


def test_csv_reader_rejects_duplicate_headers_and_supports_only_csv() -> None:
    reader = CsvReader()
    records = list(reader.read(BytesIO(b"id,id\n1,2\n")))

    assert records[0].parse_error is not None
    assert reader.supports("CSV")
    assert not reader.supports("jsonl")