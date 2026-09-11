"""Implémentations SQLAlchemy des ports repository (issue I1.5).

Chaque classe reçoit une ``Session`` SQLAlchemy (fournie par l'``UnitOfWork``) et
n'ouvre ni ne valide de transaction : c'est l'UoW qui `commit()` / `rollback()`.

Ordre d'écriture attendu (assuré par le cas d'utilisation d'import) :
``source -> code repositories -> mapping -> import_batch -> raw_records ->
sessions -> model_calls -> tool_calls -> rejects -> field_profiles``.
Chaque étape résout ses clés étrangères contre les lignes déjà écrites.
"""

from __future__ import annotations

from collections.abc import Iterable

from sqlalchemy import func, insert, select, update
from sqlalchemy.orm import Session

from agentscope.application.ports import UpsertOutcome
from agentscope.domain import (
    FieldProfile as FieldProfileEntity,
)
from agentscope.domain import (
    ImportBatch,
    ImportReject,
    SourceMapping,
    ToolCall,
)
from agentscope.domain import (
    ModelCall as ModelCallEntity,
)
from agentscope.domain import (
    RawRecord as RawRecordEntity,
)
from agentscope.domain import (
    Repository as RepositoryEntity,
)
from agentscope.domain import (
    Session as SessionEntity,
)
from agentscope.domain import (
    Source as SourceEntity,
)
from agentscope.infrastructure.persistence.orm_models import (
    FieldProfileRow,
    ImportBatchRow,
    ImportRejectRow,
    MappingRow,
    ModelCallRow,
    RawRecordRow,
    RepositoryRow,
    SessionRow,
    SourceRow,
    ToolCallRow,
)
from agentscope.infrastructure.persistence.repositories import _helpers as h
from agentscope.infrastructure.persistence.repositories import _mappers as m
from agentscope.infrastructure.persistence.repositories.errors import UnknownReferenceError


class SqlReferenceRepository:
    def __init__(self, session: Session) -> None:
        self._s = session

    def add_source(self, source: SourceEntity) -> None:
        self._s.execute(insert(SourceRow).values(**m.source_to_values(source)))

    def get_source(self, name: str) -> SourceEntity | None:
        row = self._s.execute(select(SourceRow).where(SourceRow.name == name)).scalar_one_or_none()
        return m.row_to_source(row) if row is not None else None

    def list_sources(self) -> list[SourceEntity]:
        rows = self._s.execute(select(SourceRow).order_by(SourceRow.name)).scalars().all()
        return [m.row_to_source(r) for r in rows]

    def upsert_code_repositories(
        self, source_name: str, repositories: Iterable[RepositoryEntity]
    ) -> UpsertOutcome:
        sid = h.source_id(self._s, source_name)
        rows = [m.repository_to_values(r, sid) for r in repositories]
        return h.bulk_insert_ignore(self._s, RepositoryRow, rows, ["source_id", "name"])

    def get_code_repository(self, source_name: str, name: str) -> RepositoryEntity | None:
        sid = h.source_id_or_none(self._s, source_name)
        if sid is None:
            return None
        row = self._s.execute(
            select(RepositoryRow).where(RepositoryRow.source_id == sid, RepositoryRow.name == name)
        ).scalar_one_or_none()
        return m.row_to_repository(row, source_name) if row is not None else None

    def list_code_repositories(self, source_name: str | None = None) -> list[RepositoryEntity]:
        stmt = select(RepositoryRow, SourceRow.name).join(
            SourceRow, SourceRow.id == RepositoryRow.source_id
        )
        if source_name is not None:
            stmt = stmt.where(SourceRow.name == source_name)
        rows = self._s.execute(stmt.order_by(SourceRow.name, RepositoryRow.name)).all()
        return [m.row_to_repository(row, src_name) for row, src_name in rows]


class SqlMappingRepository:
    def __init__(self, session: Session) -> None:
        self._s = session

    def add(self, mapping: SourceMapping) -> None:
        sid = h.source_id(self._s, mapping.source_name)
        self._s.execute(insert(MappingRow).values(**m.mapping_to_values(mapping, sid)))

    def get(self, name: str, version: int | None = None) -> SourceMapping | None:
        stmt = select(MappingRow).where(MappingRow.name == name)
        if version is not None:
            stmt = stmt.where(MappingRow.version == version)
        else:
            stmt = stmt.where(MappingRow.is_active.is_(True)).order_by(MappingRow.version.desc())
        row = self._s.execute(stmt.limit(1)).scalar_one_or_none()
        if row is None:
            return None
        source_name = self._s.execute(
            select(SourceRow.name).where(SourceRow.id == row.source_id)
        ).scalar_one()
        return m.row_to_mapping(row, source_name)

    def list_for_source(self, source_name: str) -> list[SourceMapping]:
        sid = h.source_id_or_none(self._s, source_name)
        if sid is None:
            return []
        rows = (
            self._s.execute(
                select(MappingRow)
                .where(MappingRow.source_id == sid)
                .order_by(MappingRow.name, MappingRow.version)
            )
            .scalars()
            .all()
        )
        return [m.row_to_mapping(r, source_name) for r in rows]

    def list_all(self) -> list[SourceMapping]:
        rows = self._s.execute(
            select(MappingRow, SourceRow.name)
            .join(SourceRow, MappingRow.source_id == SourceRow.id)
            .order_by(SourceRow.name, MappingRow.name, MappingRow.version)
        ).all()
        return [m.row_to_mapping(row, source_name) for row, source_name in rows]


class SqlImportRepository:
    def __init__(self, session: Session) -> None:
        self._s = session

    def add(self, batch: ImportBatch) -> None:
        sid = h.source_id(self._s, batch.source_name)
        mapping_id = (
            h.latest_mapping_id(self._s, batch.mapping_name)
            if batch.mapping_name is not None
            else None
        )
        if mapping_id is None:
            raise UnknownReferenceError(
                f"mapping actif introuvable pour l'import : {batch.mapping_name!r}"
            )
        self._s.execute(
            insert(ImportBatchRow).values(**m.import_batch_to_values(batch, sid, mapping_id))
        )

    def update(self, batch: ImportBatch) -> None:
        sid = h.source_id(self._s, batch.source_name)
        self._s.execute(
            update(ImportBatchRow)
            .where(
                ImportBatchRow.source_id == sid,
                ImportBatchRow.file_sha256 == batch.file_sha256,
            )
            .values(**m.import_batch_update_values(batch))
        )

    def get_by_file(self, source_name: str, file_sha256: str) -> ImportBatch | None:
        sid = h.source_id_or_none(self._s, source_name)
        if sid is None:
            return None
        row = self._s.execute(
            select(ImportBatchRow).where(
                ImportBatchRow.source_id == sid,
                ImportBatchRow.file_sha256 == file_sha256,
            )
        ).scalar_one_or_none()
        if row is None:
            return None
        mapping_name = self._s.execute(
            select(MappingRow.name).where(MappingRow.id == row.mapping_id)
        ).scalar_one_or_none()
        return m.row_to_import_batch(row, source_name, mapping_name)

    def get_by_sha256(self, file_sha256: str) -> ImportBatch | None:
        row = self._s.execute(
            select(ImportBatchRow, SourceRow.name, MappingRow.name)
            .join(SourceRow, ImportBatchRow.source_id == SourceRow.id)
            .join(MappingRow, ImportBatchRow.mapping_id == MappingRow.id, isouter=True)
            .where(ImportBatchRow.file_sha256 == file_sha256)
            .order_by(ImportBatchRow.imported_at.desc(), ImportBatchRow.id.desc())
            .limit(1)
        ).first()
        if row is None:
            return None
        batch_row, source_name, mapping_name = row
        return m.row_to_import_batch(batch_row, source_name, mapping_name)

    def list_recent(self, limit: int, offset: int) -> list[ImportBatch]:
        rows = self._s.execute(
            select(ImportBatchRow, SourceRow.name, MappingRow.name)
            .join(SourceRow, ImportBatchRow.source_id == SourceRow.id)
            .join(MappingRow, ImportBatchRow.mapping_id == MappingRow.id, isouter=True)
            .order_by(ImportBatchRow.imported_at.desc(), ImportBatchRow.id.desc())
            .limit(limit)
            .offset(offset)
        ).all()
        return [
            m.row_to_import_batch(row, source_name, mapping_name)
            for row, source_name, mapping_name in rows
        ]

    def count(self) -> int:
        return h.count_rows(self._s, ImportBatchRow)


class SqlRawRecordRepository:
    def __init__(self, session: Session) -> None:
        self._s = session

    def upsert_many(self, batch: ImportBatch, records: Iterable[RawRecordEntity]) -> UpsertOutcome:
        records = list(records)
        if not records:
            return UpsertOutcome.empty()
        sid = h.source_id(self._s, batch.source_name)
        bid = h.import_batch_id(self._s, sid, batch.file_sha256)
        rows = [m.raw_record_to_values(r, bid) for r in records]
        return h.bulk_insert_ignore(
            self._s, RawRecordRow, rows, ["import_batch_id", "record_index"]
        )


class SqlSessionRepository:
    def __init__(self, session: Session) -> None:
        self._s = session

    def upsert_many(self, batch: ImportBatch, sessions: Iterable[SessionEntity]) -> UpsertOutcome:
        sessions = list(sessions)
        if not sessions:
            return UpsertOutcome.empty()
        sid = h.source_id(self._s, batch.source_name)
        bid = h.import_batch_id(self._s, sid, batch.file_sha256)
        raw_ids = h.raw_record_ids_by_index(self._s, bid)
        repo_ids = h.code_repository_ids_by_name(self._s, sid)
        rows = [
            m.session_to_values(
                s,
                source_id=sid,
                import_batch_id=bid,
                raw_record_id=raw_ids.get(s.provenance.record_index),
                repository_id=(
                    repo_ids.get(s.repository_name) if s.repository_name is not None else None
                ),
            )
            for s in sessions
        ]
        return h.bulk_insert_ignore(self._s, SessionRow, rows, ["source_id", "external_id"])


class SqlModelCallRepository:
    def __init__(self, session: Session) -> None:
        self._s = session

    def upsert_many(self, batch: ImportBatch, calls: Iterable[ModelCallEntity]) -> UpsertOutcome:
        calls = list(calls)
        if not calls:
            return UpsertOutcome.empty()
        sid = h.source_id(self._s, batch.source_name)
        bid = h.import_batch_id(self._s, sid, batch.file_sha256)
        session_ids = h.session_ids_by_external_id(self._s, sid)
        raw_ids = h.raw_record_ids_by_index(self._s, bid)
        rows = [
            m.model_call_to_values(
                c,
                session_id=_require_session(session_ids, c.session_external_id),
                import_batch_id=bid,
                raw_record_id=raw_ids.get(c.provenance.record_index),
            )
            for c in calls
        ]
        return h.bulk_insert_ignore(self._s, ModelCallRow, rows, ["session_id", "sequence"])


class SqlToolCallRepository:
    def __init__(self, session: Session) -> None:
        self._s = session

    def upsert_many(self, batch: ImportBatch, calls: Iterable[ToolCall]) -> UpsertOutcome:
        calls = list(calls)
        if not calls:
            return UpsertOutcome.empty()
        sid = h.source_id(self._s, batch.source_name)
        bid = h.import_batch_id(self._s, sid, batch.file_sha256)
        session_ids = h.session_ids_by_external_id(self._s, sid)
        raw_ids = h.raw_record_ids_by_index(self._s, bid)
        resolved = [(c, _require_session(session_ids, c.session_external_id)) for c in calls]
        model_call_ids = h.model_call_ids_by_key(
            self._s, [session_id for _, session_id in resolved]
        )
        rows = [
            m.tool_call_to_values(
                c,
                session_id=session_id,
                import_batch_id=bid,
                raw_record_id=raw_ids.get(c.provenance.record_index),
                model_call_id=(
                    model_call_ids.get((session_id, c.model_call_sequence))
                    if c.model_call_sequence is not None
                    else None
                ),
            )
            for c, session_id in resolved
        ]
        return h.bulk_insert_ignore(self._s, ToolCallRow, rows, ["session_id", "sequence"])


class SqlRejectRepository:
    def __init__(self, session: Session) -> None:
        self._s = session

    def add_many(self, batch: ImportBatch, rejects: Iterable[ImportReject]) -> int:
        rejects = list(rejects)
        if not rejects:
            return 0
        sid = h.source_id(self._s, batch.source_name)
        bid = h.import_batch_id(self._s, sid, batch.file_sha256)
        self._s.execute(
            insert(ImportRejectRow),
            [m.import_reject_to_values(r, bid) for r in rejects],
        )
        return len(rejects)

    def list_for_import(
        self, source_name: str, file_sha256: str, limit: int, offset: int
    ) -> list[ImportReject]:
        bid = self._batch_id_or_none(source_name, file_sha256)
        if bid is None:
            return []
        rows = (
            self._s.execute(
                select(ImportRejectRow)
                .where(ImportRejectRow.import_batch_id == bid)
                .order_by(ImportRejectRow.record_index, ImportRejectRow.id)
                .limit(limit)
                .offset(offset)
            )
            .scalars()
            .all()
        )
        return [m.row_to_import_reject(r) for r in rows]

    def count_for_import(self, source_name: str, file_sha256: str) -> int:
        bid = self._batch_id_or_none(source_name, file_sha256)
        if bid is None:
            return 0
        return self._s.execute(
            select(func.count())
            .select_from(ImportRejectRow)
            .where(ImportRejectRow.import_batch_id == bid)
        ).scalar_one()

    def _batch_id_or_none(self, source_name: str, file_sha256: str) -> int | None:
        sid = h.source_id_or_none(self._s, source_name)
        if sid is None:
            return None
        return self._s.execute(
            select(ImportBatchRow.id).where(
                ImportBatchRow.source_id == sid,
                ImportBatchRow.file_sha256 == file_sha256,
            )
        ).scalar_one_or_none()


class SqlFieldProfileRepository:
    def __init__(self, session: Session) -> None:
        self._s = session

    def upsert_many(
        self, batch: ImportBatch, profiles: Iterable[FieldProfileEntity]
    ) -> UpsertOutcome:
        profiles = list(profiles)
        if not profiles:
            return UpsertOutcome.empty()
        sid = h.source_id(self._s, batch.source_name)
        bid = h.import_batch_id(self._s, sid, batch.file_sha256)
        rows = [m.field_profile_to_values(p, bid) for p in profiles]
        return h.bulk_insert_ignore(self._s, FieldProfileRow, rows, ["import_batch_id", "path"])


def _require_session(session_ids: dict[str, int], external_id: str) -> int:
    try:
        return session_ids[external_id]
    except KeyError as exc:
        raise UnknownReferenceError(
            f"session parente absente : external_id={external_id!r} "
            "— insérer les sessions avant les appels"
        ) from exc
