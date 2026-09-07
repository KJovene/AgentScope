from __future__ import annotations

from io import BytesIO

import pytest

pa = pytest.importorskip("pyarrow")
pq = pytest.importorskip("pyarrow.parquet")

from agentscope.infrastructure.readers.parquet_reader import ParquetReader


def _parquet_bytes() -> BytesIO:
    table = pa.table(
        {
            "id": pa.array([1, 2], type=pa.int64()),
            "score": pa.array([1.5, 2.5], type=pa.float64()),
            "active": pa.array([True, False], type=pa.bool_()),
            "tags": pa.array([["a"], ["b", "c"]], type=pa.list_(pa.string())),
        }
    )
    target = BytesIO()
    pq.write_table(table, target)
    target.seek(0)
    return target


def test_parquet_reader_preserves_column_types() -> None:
    records = list(ParquetReader().read(_parquet_bytes()))

    assert [record.index for record in records] == [0, 1]
    assert records[0].payload == {"id": 1, "score": 1.5, "active": True, "tags": ["a"]}
    assert records[1].payload["id"] == 2
    assert records[1].payload["active"] is False
    assert records[1].payload["tags"] == ["b", "c"]
    assert all(record.parse_error is None for record in records)
    assert records[0].sha256 != records[1].sha256


def test_parquet_reader_returns_parse_error_for_invalid_file() -> None:
    records = list(ParquetReader().read(BytesIO(b"not-a-parquet-file")))

    assert len(records) == 1
    assert records[0].payload == {}
    assert records[0].parse_error is not None


def test_parquet_reader_supports_only_parquet() -> None:
    reader = ParquetReader()

    assert reader.supports("parquet")
    assert reader.supports("PARQUET")
    assert not reader.supports("csv")