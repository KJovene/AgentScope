"""Lecteur Parquet par lots, basé sur PyArrow."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Iterator
from io import BufferedIOBase
from typing import Any

import pyarrow as pa
import pyarrow.parquet as pq

from agentscope.domain import RawRecord


class ParquetReader:
    """Lit un fichier Parquet par batches sans convertir les types en chaînes."""

    def supports(self, file_format: str) -> bool:
        return file_format.lower() == "parquet"

    def read(self, source: BufferedIOBase) -> Iterator[RawRecord]:
        index = 0
        try:
            parquet_file = pq.ParquetFile(source)
            for batch in parquet_file.iter_batches():
                for payload in batch.to_pylist():
                    yield RawRecord(
                        index=index,
                        payload=payload,
                        sha256=self._hash_payload(payload),
                    )
                    index += 1
        except (OSError, ValueError, pa.ArrowException) as error:
            yield RawRecord(
                index=index,
                payload={},
                sha256=hashlib.sha256(b"").hexdigest(),
                parse_error=f"invalid Parquet file: {error}",
            )

    @staticmethod
    def _hash_payload(payload: dict[str, Any]) -> str:
        canonical = json.dumps(
            payload,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            default=str,
        ).encode("utf-8")
        return hashlib.sha256(canonical).hexdigest()