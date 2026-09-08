"""Implémentation de ``ImportService`` (issue I4.2).

Adapte les routes ``/imports`` aux cas d'utilisation existants :

- ``process_import`` : orchestre ``ImportFile`` (I2.8) pour 1..N fichiers, puis
  agrège les bilans en un ``ImportBatchItem`` ;
- ``list_imports`` / ``get_import_detail`` / ``list_rejects`` : lectures via les
  repositories SQLAlchemy.

Identifiant public d'un import (``import_id``) = son ``file_sha256`` (clé
d'idempotence, cf. §5.3). Pour un envoi multi-fichiers, ``process_import``
renvoie le bilan agrégé et prend le ``sha256`` du premier fichier comme ``id`` ;
chaque lot reste consultable individuellement via ``GET /imports``.
"""

from __future__ import annotations

import json
from collections.abc import Callable, Sequence
from datetime import UTC, datetime
from pathlib import PurePosixPath

from sqlalchemy.orm import Session

from agentscope.application.ports.imports import ImportBatchItem, ImportRejectItem
from agentscope.application.ports.metrics import Page, Paginated
from agentscope.application.ports.source_reader import SourceReader
from agentscope.application.ports.unit_of_work import UnitOfWork
from agentscope.application.use_cases.import_file import ImportFile, ImportReport
from agentscope.domain import DomainError, FileFormat, ImportBatch, ImportStatus
from agentscope.infrastructure.persistence.repositories.sql import (
    SqlImportRepository,
    SqlRejectRepository,
)

_SUFFIX_TO_FORMAT = {
    ".jsonl": FileFormat.JSONL,
    ".ndjson": FileFormat.JSONL,
    ".csv": FileFormat.CSV,
    ".parquet": FileFormat.PARQUET,
}


class UnsupportedFileError(DomainError):
    """Extension de fichier non reconnue pour l'import."""


def _format_for(filename: str) -> FileFormat:
    suffix = PurePosixPath(filename).suffix.lower()
    fmt = _SUFFIX_TO_FORMAT.get(suffix)
    if fmt is None:
        accepted = ", ".join(sorted(_SUFFIX_TO_FORMAT))
        raise UnsupportedFileError(
            f"Format non reconnu pour « {filename} » (extensions acceptées : {accepted})."
        )
    return fmt


_STATUS_MAP = {
    ImportStatus.FAILED: "failed",
    ImportStatus.PENDING: "partial",
    ImportStatus.RUNNING: "partial",
}


def _api_status(status: ImportStatus, rejected_count: int) -> str:
    if status in _STATUS_MAP:
        return _STATUS_MAP[status]
    return "partial" if rejected_count > 0 else "completed"


def _batch_to_item(batch: ImportBatch) -> ImportBatchItem:
    return ImportBatchItem(
        id=batch.file_sha256,
        source_id=batch.source_name,
        mapping_id=batch.mapping_name or "",
        status=_api_status(batch.status, batch.rejected_count),
        imported_count=batch.imported_count,
        duplicate_count=batch.duplicate_count,
        rejected_count=batch.rejected_count,
        missing_info_count=batch.missing_info_count,
        imported_at=batch.imported_at,
    )


class SqlImportService:
    def __init__(
        self,
        session: Session,
        uow_factory: Callable[[], UnitOfWork],
        readers: Sequence[SourceReader],
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self._s = session
        self._uow_factory = uow_factory
        self._readers = tuple(readers)
        self._clock = clock or (lambda: datetime.now(UTC))

    # -- écriture -------------------------------------------------------------

    async def process_import(
        self, mapping_id: str, files: list[tuple[str, bytes]]
    ) -> ImportBatchItem:
        if not files:
            raise DomainError("Au moins un fichier est requis pour l'import.")

        importer = ImportFile(self._uow_factory, self._readers, clock=self._clock)
        reports: list[ImportReport] = [
            importer.execute(
                content=content,
                original_filename=filename,
                file_format=_format_for(filename),
                mapping_name=mapping_id,
            )
            for filename, content in files
        ]
        return self._aggregate(reports, mapping_id)

    def _aggregate(
        self, reports: list[ImportReport], mapping_id: str
    ) -> ImportBatchItem:
        rejected = sum(r.rejected_count for r in reports)
        statuses = {r.status for r in reports}
        if ImportStatus.FAILED in statuses:
            status = "failed"
        elif rejected > 0 or statuses != {ImportStatus.SUCCEEDED}:
            status = "partial"
        else:
            status = "completed"
        head = reports[0]
        return ImportBatchItem(
            id=head.file_sha256,
            source_id=head.source_name,
            mapping_id=mapping_id,
            status=status,
            imported_count=sum(r.imported_count for r in reports),
            duplicate_count=sum(r.duplicate_count for r in reports),
            rejected_count=rejected,
            missing_info_count=sum(r.missing_info_count for r in reports),
            imported_at=self._clock(),
        )

    # -- lecture -----------------------------------------------------------

    def list_imports(self, page: Page) -> Paginated[ImportBatchItem]:
        repo = SqlImportRepository(self._s)
        batches = repo.list_recent(page.limit, page.offset)
        return Paginated(
            items=tuple(_batch_to_item(b) for b in batches),
            total=repo.count(),
            limit=page.limit,
            offset=page.offset,
        )

    def get_import_detail(self, import_id: str) -> ImportBatchItem | None:
        batch = SqlImportRepository(self._s).get_by_sha256(import_id)
        return _batch_to_item(batch) if batch is not None else None

    def list_rejects(
        self, import_id: str, page: Page
    ) -> Paginated[ImportRejectItem]:
        batch = SqlImportRepository(self._s).get_by_sha256(import_id)
        if batch is None:
            return Paginated(items=(), total=0, limit=page.limit, offset=page.offset)

        rejects_repo = SqlRejectRepository(self._s)
        rejects = rejects_repo.list_for_import(
            batch.source_name, import_id, page.limit, page.offset
        )
        total = rejects_repo.count_for_import(batch.source_name, import_id)
        return Paginated(
            items=tuple(
                ImportRejectItem(
                    id=f"{import_id}:{r.record_index}",
                    import_batch_id=import_id,
                    reason=r.detail or r.reason.value,
                    line_number=r.record_index,
                    raw_record=json.dumps(r.payload, ensure_ascii=False) if r.payload else None,
                    rejected_at=batch.imported_at,
                )
                for r in rejects
            ),
            total=total,
            limit=page.limit,
            offset=page.offset,
        )
