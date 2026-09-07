"""Résolution de clés étrangères et insertion en masse idempotente."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from agentscope.application.ports import UpsertOutcome
from agentscope.infrastructure.persistence.orm_models import (
    ImportBatchRow,
    MappingRow,
    ModelCallRow,
    RawRecordRow,
    RepositoryRow,
    SessionRow,
    SourceRow,
)
from agentscope.infrastructure.persistence.repositories.errors import UnknownReferenceError


def source_id(session: Session, name: str) -> int:
    value = session.execute(
        select(SourceRow.id).where(SourceRow.name == name)
    ).scalar_one_or_none()
    if value is None:
        raise UnknownReferenceError(f"source inconnue : {name!r}")
    return value


def source_id_or_none(session: Session, name: str) -> int | None:
    return session.execute(
        select(SourceRow.id).where(SourceRow.name == name)
    ).scalar_one_or_none()


def latest_mapping_id(session: Session, name: str) -> int | None:
    return session.execute(
        select(MappingRow.id)
        .where(MappingRow.name == name, MappingRow.is_active.is_(True))
        .order_by(MappingRow.version.desc())
        .limit(1)
    ).scalar_one_or_none()


def import_batch_id(session: Session, source_id_: int, file_sha256: str) -> int:
    value = session.execute(
        select(ImportBatchRow.id).where(
            ImportBatchRow.source_id == source_id_,
            ImportBatchRow.file_sha256 == file_sha256,
        )
    ).scalar_one_or_none()
    if value is None:
        raise UnknownReferenceError(
            f"import absent pour (source={source_id_}, sha256={file_sha256!r}) "
            "— insérer l'ImportBatch avant ses enfants"
        )
    return value


def raw_record_ids_by_index(session: Session, batch_id: int) -> dict[int, int]:
    rows = session.execute(
        select(RawRecordRow.record_index, RawRecordRow.id).where(
            RawRecordRow.import_batch_id == batch_id
        )
    ).all()
    return {index: rid for index, rid in rows}


def code_repository_ids_by_name(session: Session, source_id_: int) -> dict[str, int]:
    rows = session.execute(
        select(RepositoryRow.name, RepositoryRow.id).where(
            RepositoryRow.source_id == source_id_
        )
    ).all()
    return {name: rid for name, rid in rows}


def session_ids_by_external_id(session: Session, source_id_: int) -> dict[str, int]:
    rows = session.execute(
        select(SessionRow.external_id, SessionRow.id).where(
            SessionRow.source_id == source_id_
        )
    ).all()
    return {external_id: sid for external_id, sid in rows}


def model_call_ids_by_key(
    session: Session, session_ids: Sequence[int]
) -> dict[tuple[int, int], int]:
    if not session_ids:
        return {}
    rows = session.execute(
        select(ModelCallRow.session_id, ModelCallRow.sequence, ModelCallRow.id).where(
            ModelCallRow.session_id.in_(session_ids)
        )
    ).all()
    return {(sid, seq): mid for sid, seq, mid in rows}


def count_rows(session: Session, model: type) -> int:
    return session.execute(select(func.count()).select_from(model)).scalar_one()


def _dialect_insert(session: Session) -> Any:
    name = session.get_bind().dialect.name
    if name == "postgresql":
        from sqlalchemy.dialects.postgresql import insert as pg_insert

        return pg_insert
    if name == "sqlite":
        from sqlalchemy.dialects.sqlite import insert as sqlite_insert

        return sqlite_insert
    raise RuntimeError(f"dialecte sans upsert supporté : {name!r}")


def bulk_insert_ignore(
    session: Session,
    model: Any,
    rows: list[dict[str, Any]],
    conflict_columns: list[str],
) -> UpsertOutcome:
    """INSERT ... ON CONFLICT DO NOTHING. `inserted` = lignes réellement écrites,
    `skipped` = conflits ignorés (doublons)."""
    if not rows:
        return UpsertOutcome.empty()
    insert = _dialect_insert(session)
    stmt = (
        insert(model)
        .values(rows)
        .on_conflict_do_nothing(index_elements=conflict_columns)
        .returning(model.id)
    )
    inserted = len(session.execute(stmt).scalars().all())
    return UpsertOutcome(inserted=inserted, skipped=len(rows) - inserted)
