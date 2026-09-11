"""Implémentation SQLAlchemy de ``DataQualityQueryService``.

Lit la vue agrégée ``v_data_quality`` (issue I1.6) : un bilan par import, avec
le ratio de complétude (``NULL`` si non calculable — jamais ``0``).
"""

from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.orm import Session

from agentscope.application.ports.data_quality import DataQualityBatchItem


class SqlDataQualityQueryService:
    def __init__(self, session: Session) -> None:
        self._s = session

    def get_quality_metrics(self, source_id: str | None = None) -> list[DataQualityBatchItem]:
        sql = """
            SELECT
                import_batch_id,
                source_name,
                imported_count,
                duplicate_count,
                rejected_count,
                missing_info_count,
                completeness_ratio,
                imported_at
            FROM v_data_quality
        """
        params: dict[str, object] = {}
        if source_id is not None:
            sql += " WHERE source_name = :source_name"
            params["source_name"] = source_id
        sql += " ORDER BY imported_at DESC, import_batch_id DESC"

        return [
            DataQualityBatchItem(
                import_batch_id=str(row.import_batch_id),
                source_name=row.source_name,
                imported_count=int(row.imported_count or 0),
                duplicate_count=int(row.duplicate_count or 0),
                rejected_count=int(row.rejected_count or 0),
                missing_info_count=int(row.missing_info_count or 0),
                completeness_rate=(
                    float(row.completeness_ratio) if row.completeness_ratio is not None else None
                ),
                imported_at=row.imported_at,
            )
            for row in self._s.execute(text(sql), params)
        ]
