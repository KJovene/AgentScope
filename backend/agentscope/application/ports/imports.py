from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Protocol, runtime_checkable

from agentscope.application.ports.metrics import Page, Paginated


@dataclass(frozen=True, slots=True)
class ImportBatchItem:
    id: str
    mapping_id: str
    status: str  # "completed" | "failed" | "partial"
    imported_count: int
    duplicate_count: int
    rejected_count: int
    missing_info_count: int
    source_id: str | None = None
    imported_at: datetime | None = None


@dataclass(frozen=True, slots=True)
class ImportRejectItem:
    id: str
    import_batch_id: str
    reason: str
    line_number: int | None = None
    raw_record: str | None = None
    rejected_at: datetime | None = None


@runtime_checkable
class ImportService(Protocol):

    async def process_import(
        self, mapping_id: str, files: list[tuple[str, bytes]]
    ) -> ImportBatchItem: ...

    def list_imports(self, page: Page) -> Paginated[ImportBatchItem]: ...

    def get_import_detail(self, import_id: str) -> ImportBatchItem | None: ...

    def list_rejects(
        self, import_id: str, page: Page
    ) -> Paginated[ImportRejectItem]: ...
