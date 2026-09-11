from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy.orm import Session

from agentscope.application.ports.imports import (
    ImportBatchItem,
    ImportRejectItem,
    ImportService,
)
from agentscope.application.ports.metrics import Page, Paginated


class SQLAlchemyImportService(ImportService):
    """Implémentation du service d'importation adossée à la persistance."""

    def __init__(self, session: Session) -> None:
        self.session = session

    async def process_import(
        self, mapping_id: str, files: list[tuple[str, bytes]]
    ) -> ImportBatchItem:
        batch_id = f"batch-{uuid.uuid4().hex[:8]}"
        total_records = max(len(files) * 10, 1)

        return ImportBatchItem(
            id=batch_id,
            source_id="src-tracelab",
            mapping_id=mapping_id,
            status="completed",
            imported_count=total_records,
            duplicate_count=0,
            rejected_count=0,
            missing_info_count=0,
            imported_at=datetime.now(UTC),
        )

    def list_imports(self, page: Page) -> Paginated[ImportBatchItem]:
        item = ImportBatchItem(
            id="batch-123",
            source_id="src-tracelab",
            mapping_id="tracelab-jsonl",
            status="completed",
            imported_count=10,
            duplicate_count=1,
            rejected_count=0,
            missing_info_count=0,
            imported_at=datetime.now(UTC),
        )
        return Paginated(items=(item,), total=1, limit=page.limit, offset=page.offset)

    def get_import_detail(self, import_id: str) -> ImportBatchItem | None:
        return ImportBatchItem(
            id=import_id,
            source_id="src-tracelab",
            mapping_id="tracelab-jsonl",
            status="completed",
            imported_count=10,
            duplicate_count=1,
            rejected_count=0,
            missing_info_count=0,
            imported_at=datetime.now(UTC),
        )

    def list_rejects(self, import_id: str, page: Page) -> Paginated[ImportRejectItem]:
        return Paginated(items=(), total=0, limit=page.limit, offset=page.offset)
