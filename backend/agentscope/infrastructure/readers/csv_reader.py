"""Lecteur CSV avec détection de dialecte et d'encodage."""

from __future__ import annotations

import csv
import hashlib
import io
import json
from collections.abc import Iterator
from io import BufferedIOBase

from agentscope.domain import RawRecord


class CsvReader:
    """Lit un CSV à en-têtes en produisant un dictionnaire par ligne."""

    def supports(self, file_format: str) -> bool:
        return file_format.lower() == "csv"

    def read(self, source: BufferedIOBase) -> Iterator[RawRecord]:
        content = source.read()
        text = self._decode(content)
        if not text.strip():
            return

        try:
            dialect = csv.Sniffer().sniff(text[:8192], delimiters=",;")
        except csv.Error:
            dialect = csv.excel

        try:
            rows = csv.reader(io.StringIO(text), dialect, strict=True)
            headers = next(rows, None)
        except csv.Error as error:
            yield self._error_record(0, content, f"invalid CSV: {error}")
            return

        if not headers or any(not header.strip() for header in headers):
            yield self._error_record(0, content, "CSV header is missing or contains an empty name")
            return
        if len(set(headers)) != len(headers):
            yield self._error_record(0, content, "CSV header contains duplicate names")
            return

        for index, row in enumerate(rows):
            row_bytes = json.dumps(row, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
            record_hash = hashlib.sha256(row_bytes).hexdigest()
            if len(row) != len(headers):
                yield RawRecord(
                    index=index,
                    payload={},
                    sha256=record_hash,
                    parse_error=(f"CSV row has {len(row)} values but expected {len(headers)}"),
                )
                continue
            payload = dict(zip(headers, row, strict=True))
            yield RawRecord(index=index, payload=payload, sha256=record_hash)

    @staticmethod
    def _decode(content: bytes) -> str:
        for encoding in ("utf-8-sig", "cp1252", "latin-1"):
            try:
                return content.decode(encoding)
            except UnicodeDecodeError:
                continue
        raise UnicodeDecodeError("unknown", content, 0, len(content), "unsupported CSV encoding")

    @staticmethod
    def _error_record(index: int, content: bytes, detail: str) -> RawRecord:
        return RawRecord(
            index=index,
            payload={},
            sha256=hashlib.sha256(content).hexdigest(),
            parse_error=detail,
        )
