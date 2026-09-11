"""Cas d'utilisation ``ImportFile`` (issues I2.8 et I2.7).

Orchestre le parcours d'ingestion de bout en bout :

    fichier --> lecteur --> Normalizer --> repositories --> bilan

Deux garanties :

- **Atomique** : tout est écrit dans une seule ``UnitOfWork``. La moindre
  exception ⇒ ``rollback`` ⇒ aucune ligne partielle (tests I7.1 / I7.2).
- **Idempotent** : un fichier déjà importé avec succès (même ``sha256``) n'est pas
  ré-ingéré ; et même en forçant, les clés naturelles + ``upsert`` ignore-on-conflict
  garantissent « réimport ⇒ 0 doublon » (issue I2.7).
"""

from __future__ import annotations

import hashlib
from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from io import BytesIO

from agentscope.application.mapping.normalizer import NormalizationResult, Normalizer
from agentscope.application.mapping.validator import parse_and_validate
from agentscope.application.ports import SourceReader, UnitOfWork, UpsertOutcome
from agentscope.domain import (
    DomainError,
    FileFormat,
    ImportBatch,
    ImportStatus,
    RawRecord,
)


class ImportFailedError(DomainError):
    """L'import ne peut pas aboutir : format non géré, mapping absent ou incohérent."""


@dataclass(frozen=True, slots=True)
class ImportReport:
    """Bilan d'un import, renvoyé à l'appelant (contrat du plan §5.3)."""

    source_name: str
    original_filename: str
    file_sha256: str
    status: ImportStatus
    record_count: int
    imported_count: int
    duplicate_count: int
    rejected_count: int
    missing_info_count: int
    already_imported: bool = False  # court-circuit : le fichier était déjà ingéré


class ImportFile:
    """Ingestion d'un fichier de traces selon un mapping enregistré."""

    def __init__(
        self,
        uow_factory: Callable[[], UnitOfWork],
        readers: Sequence[SourceReader],
        normalizer: Normalizer | None = None,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self._uow_factory = uow_factory
        self._readers = tuple(readers)
        self._normalizer = normalizer or Normalizer()
        self._clock = clock or (lambda: datetime.now(UTC))

    def execute(
        self,
        *,
        content: bytes,
        original_filename: str,
        file_format: FileFormat,
        mapping_name: str,
    ) -> ImportReport:
        file_sha256 = hashlib.sha256(content).hexdigest()

        with self._uow_factory() as uow:
            mapping_row = uow.mappings.get(mapping_name)
            if mapping_row is None:
                raise ImportFailedError(f"mapping `{mapping_name}` introuvable")
            source_name = mapping_row.source_name

            existing = uow.imports.get_by_file(source_name, file_sha256)
            if existing is not None and existing.status is ImportStatus.SUCCEEDED:
                return _report(existing, already_imported=True)

            mapping = parse_and_validate(mapping_row.definition)
            if mapping.constants.get("source_name") != source_name:
                raise ImportFailedError(
                    "`constants.source_name` du mapping incohérent avec sa source "
                    f"(`{mapping.constants.get('source_name')}` != `{source_name}`)"
                )

            reader = self._reader_for(file_format)
            records = list(reader.read(BytesIO(content)))
            result = self._normalizer.normalize(records, mapping)

            batch = ImportBatch(
                source_name=source_name,
                original_filename=original_filename,
                file_sha256=file_sha256,
                file_format=file_format,
                imported_at=self._clock(),
                status=ImportStatus.RUNNING,
                mapping_name=mapping_name,
                record_count=len(records),
            )
            if existing is None:
                uow.imports.add(batch)

            written = _persist(uow, batch, records, result)
            final = _finalize(batch, written, result)
            uow.imports.update(final)
            uow.commit()

        return _report(final)

    def _reader_for(self, file_format: FileFormat) -> SourceReader:
        for reader in self._readers:
            if reader.supports(file_format.value):
                return reader
        raise ImportFailedError(f"aucun lecteur pour le format `{file_format.value}`")


# ---------------------------------------------------------------------------


def _persist(
    uow: UnitOfWork,
    batch: ImportBatch,
    records: Iterable[RawRecord],
    result: NormalizationResult,
) -> UpsertOutcome:
    """Écrit tout dans l'ordre des dépendances ; renvoie le cumul inséré / ignoré."""
    known = {session.external_id for session in result.sessions}
    model_calls = [c for c in result.model_calls if c.session_external_id in known]
    tool_calls = [c for c in result.tool_calls if c.session_external_id in known]

    uow.raw_records.upsert_many(batch, records)
    total = (
        uow.sessions.upsert_many(batch, result.sessions)
        + uow.model_calls.upsert_many(batch, model_calls)
        + uow.tool_calls.upsert_many(batch, tool_calls)
    )
    uow.rejects.add_many(batch, result.rejects)
    return total


def _finalize(
    batch: ImportBatch, written: UpsertOutcome, result: NormalizationResult
) -> ImportBatch:
    return ImportBatch(
        source_name=batch.source_name,
        original_filename=batch.original_filename,
        file_sha256=batch.file_sha256,
        file_format=batch.file_format,
        imported_at=batch.imported_at,
        status=ImportStatus.SUCCEEDED,
        mapping_name=batch.mapping_name,
        record_count=batch.record_count,
        imported_count=written.inserted,
        duplicate_count=written.skipped,
        rejected_count=len(result.rejects),
        missing_info_count=sum(result.missing_info.values()),
    )


def _report(batch: ImportBatch, already_imported: bool = False) -> ImportReport:
    return ImportReport(
        source_name=batch.source_name,
        original_filename=batch.original_filename,
        file_sha256=batch.file_sha256,
        status=batch.status,
        record_count=batch.record_count or 0,
        imported_count=batch.imported_count,
        duplicate_count=batch.duplicate_count,
        rejected_count=batch.rejected_count,
        missing_info_count=batch.missing_info_count,
        already_imported=already_imported,
    )
