"""Lecteur JSONL streaming et tolérant aux lignes invalides."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Iterator
from io import BufferedIOBase

from agentscope.domain import RawRecord


class JsonlReader:
    """Lit un objet JSON par ligne sans interrompre le flux sur une ligne cassée."""

    def supports(self, file_format: str) -> bool:
        return file_format.lower() == "jsonl"

    def read(self, source: BufferedIOBase) -> Iterator[RawRecord]:
        for index, raw_line in enumerate(source):
            line = raw_line.rstrip(b"\r\n")
            record_hash = hashlib.sha256(line).hexdigest()

            if not line.strip():
                yield RawRecord(
                    index=index,
                    payload={},
                    sha256=record_hash,
                    parse_error="empty JSONL line",
                )
                continue

            try:
                payload = json.loads(line)
            except (UnicodeDecodeError, json.JSONDecodeError) as error:
                yield RawRecord(
                    index=index,
                    payload={},
                    sha256=record_hash,
                    parse_error=f"invalid JSON: {error}",
                )
                continue

            if not isinstance(payload, dict):
                yield RawRecord(
                    index=index,
                    payload={},
                    sha256=record_hash,
                    parse_error="JSONL record must be an object",
                )
                continue

            yield RawRecord(index=index, payload=payload, sha256=record_hash)