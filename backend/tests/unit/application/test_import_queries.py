"""Tests des consultations d'import (issue I2.10)."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from agentscope.application.use_cases.import_queries import (
    GetImportReport,
    ImportNotFoundError,
    ListImports,
    ListRejects,
)
from agentscope.domain import FileFormat, ImportBatch, ImportReject, RejectReason

NOW = datetime(2026, 1, 1, tzinfo=UTC)


def _batch(file_sha256: str = "a" * 64) -> ImportBatch:
    return ImportBatch(
        source_name="demo",
        original_filename="demo.jsonl",
        file_sha256=file_sha256,
        file_format=FileFormat.JSONL,
        imported_at=NOW,
        mapping_name="demo-jsonl",
        record_count=2,
        imported_count=1,
        rejected_count=1,
    )


class FakeImportRepository:
    def __init__(self, batches: list[ImportBatch]) -> None:
        self.batches = batches

    def list_recent(self, limit: int, offset: int) -> list[ImportBatch]:
        return self.batches[offset : offset + limit]

    def count(self) -> int:
        return len(self.batches)

    def get_by_file(self, source_name: str, file_sha256: str) -> ImportBatch | None:
        return next(
            (
                batch
                for batch in self.batches
                if batch.source_name == source_name and batch.file_sha256 == file_sha256
            ),
            None,
        )


class FakeRejectRepository:
    def __init__(self, rejects: list[ImportReject]) -> None:
        self.rejects = rejects

    def list_for_import(
        self, source_name: str, file_sha256: str, limit: int, offset: int
    ) -> list[ImportReject]:
        return self.rejects[offset : offset + limit]

    def count_for_import(self, source_name: str, file_sha256: str) -> int:
        return len(self.rejects)


def test_list_imports_retourne_une_page_et_le_total() -> None:
    batches = [_batch("a" * 64), _batch("b" * 64)]

    page = ListImports(FakeImportRepository(batches)).execute(limit=1, offset=1)

    assert page.items == (batches[1],)
    assert page.total == 2
    assert page.limit == 1
    assert page.offset == 1


def test_get_report_and_list_rejects_retournent_les_donnees() -> None:
    batch = _batch()
    reject = ImportReject(
        record_index=1,
        reason=RejectReason.MISSING_REQUIRED_FIELD,
        detail="sid absent",
        payload={"agent": "demo"},
    )
    imports = FakeImportRepository([batch])

    report = GetImportReport(imports).execute(source_name="demo", file_sha256="a" * 64)
    rejects = ListRejects(imports, FakeRejectRepository([reject])).execute(
        source_name="demo", file_sha256="a" * 64
    )

    assert report == batch
    assert rejects.items == (reject,)
    assert rejects.total == 1


def test_consultation_d_un_import_inconnu_est_explicite() -> None:
    imports = FakeImportRepository([])

    with pytest.raises(ImportNotFoundError, match="Import introuvable"):
        GetImportReport(imports).execute(source_name="demo", file_sha256="a" * 64)

    with pytest.raises(ImportNotFoundError, match="Import introuvable"):
        ListRejects(imports, FakeRejectRepository([])).execute(
            source_name="demo", file_sha256="a" * 64
        )


@pytest.mark.parametrize("limit, offset", [(0, 0), (-1, 0), (1, -1)])
def test_pagination_refuse_des_valeurs_invalides(limit: int, offset: int) -> None:
    with pytest.raises(ValueError):
        ListImports(FakeImportRepository([])).execute(limit=limit, offset=offset)
