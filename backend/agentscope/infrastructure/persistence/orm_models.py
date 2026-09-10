"""Modèles ORM SQLAlchemy — couche infrastructure.

Traduction fidèle de ``docs/data/relational-model.md`` (schéma v1). Ce sont des
objets de persistance, **distincts** des entités du domaine ; les repositories
(I1.5) font la correspondance dans les deux sens.

Les vocabulaires contrôlés (``CHECK ... IN (...)``) sont dérivés des énumérations
du domaine, qui restent la source de vérité.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from sqlalchemy import (
    JSON,
    Boolean,
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    Text,
    UniqueConstraint,
    text,
    true,
)
from sqlalchemy.orm import Mapped, mapped_column

from agentscope.domain.value_objects import (
    CallStatus,
    ErrorType,
    FileFormat,
    ImportStatus,
    RejectReason,
)
from agentscope.infrastructure.persistence.database import Base


def _in(column: str, enum_cls: type[Enum]) -> str:
    values = ", ".join(f"'{member.value}'" for member in enum_cls)
    return f"{column} IN ({values})"


_TS = DateTime(timezone=True)
# `none_as_null` : un payload Python `None` devient SQL NULL (et non le JSON `null`),
# pour que la rétention `minimal` (I1.7) et les filtres `IS NULL` fonctionnent.
_JSON = JSON(none_as_null=True)


class SourceRow(Base):
    __tablename__ = "source"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    display_name: Mapped[str | None] = mapped_column(Text)
    homepage_url: Mapped[str | None] = mapped_column(Text)


class RepositoryRow(Base):
    __tablename__ = "repository"
    __table_args__ = (UniqueConstraint("source_id", "name"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    source_id: Mapped[int] = mapped_column(ForeignKey("source.id"), nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    url: Mapped[str | None] = mapped_column(Text)
    language: Mapped[str | None] = mapped_column(Text)


class MappingRow(Base):
    __tablename__ = "mapping"
    __table_args__ = (
        UniqueConstraint("name", "version"),
        CheckConstraint("version >= 1", name="version_positive"),
        CheckConstraint(_in("source_format", FileFormat), name="source_format_vocab"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    source_id: Mapped[int] = mapped_column(ForeignKey("source.id"), nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    source_format: Mapped[str] = mapped_column(Text, nullable=False)
    definition_json: Mapped[dict[str, Any]] = mapped_column(_JSON, nullable=False)
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default=true()
    )
    created_at: Mapped[datetime] = mapped_column(_TS, nullable=False)
    created_by: Mapped[str | None] = mapped_column(Text)


class ImportBatchRow(Base):
    __tablename__ = "import_batch"
    __table_args__ = (
        UniqueConstraint("source_id", "file_sha256"),  # -> idempotence niveau fichier
        CheckConstraint(_in("status", ImportStatus), name="status_vocab"),
        CheckConstraint(_in("file_format", FileFormat), name="file_format_vocab"),
        CheckConstraint(
            "imported_count >= 0 AND duplicate_count >= 0 "
            "AND rejected_count >= 0 AND missing_info_count >= 0",
            name="counts_non_negative",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    source_id: Mapped[int] = mapped_column(ForeignKey("source.id"), nullable=False)
    mapping_id: Mapped[int] = mapped_column(ForeignKey("mapping.id"), nullable=False)
    original_filename: Mapped[str] = mapped_column(Text, nullable=False)
    file_sha256: Mapped[str] = mapped_column(Text, nullable=False)
    file_format: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        default=ImportStatus.PENDING.value,
        server_default=text(f"'{ImportStatus.PENDING.value}'"),
    )
    imported_at: Mapped[datetime] = mapped_column(_TS, nullable=False)
    record_count: Mapped[int | None] = mapped_column(Integer)
    imported_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default=text("0")
    )
    duplicate_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default=text("0")
    )
    rejected_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default=text("0")
    )
    missing_info_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default=text("0")
    )


class RawRecordRow(Base):
    __tablename__ = "raw_record"
    __table_args__ = (UniqueConstraint("import_batch_id", "record_index"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    import_batch_id: Mapped[int] = mapped_column(
        ForeignKey("import_batch.id", ondelete="CASCADE"), nullable=False
    )
    record_index: Mapped[int] = mapped_column(Integer, nullable=False)
    record_sha256: Mapped[str] = mapped_column(Text, nullable=False)
    payload_json: Mapped[dict[str, Any] | None] = mapped_column(_JSON)


class SessionRow(Base):
    __tablename__ = "session"
    __table_args__ = (
        UniqueConstraint("source_id", "external_id"),  # -> idempotence niveau session
        CheckConstraint(
            "ended_at IS NULL OR started_at IS NULL OR ended_at >= started_at",
            name="interval_ordered",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    source_id: Mapped[int] = mapped_column(ForeignKey("source.id"), nullable=False)
    import_batch_id: Mapped[int] = mapped_column(ForeignKey("import_batch.id"), nullable=False)
    raw_record_id: Mapped[int | None] = mapped_column(
        ForeignKey("raw_record.id", ondelete="SET NULL")
    )
    repository_id: Mapped[int | None] = mapped_column(ForeignKey("repository.id"))
    external_id: Mapped[str] = mapped_column(Text, nullable=False)
    agent_name: Mapped[str | None] = mapped_column(Text)
    started_at: Mapped[datetime | None] = mapped_column(_TS)
    ended_at: Mapped[datetime | None] = mapped_column(_TS)


class ModelCallRow(Base):
    __tablename__ = "model_call"
    __table_args__ = (
        UniqueConstraint("session_id", "sequence"),
        CheckConstraint("sequence >= 0", name="sequence_non_negative"),
        CheckConstraint(_in("status", CallStatus), name="status_vocab"),
        CheckConstraint(
            f"error_type IS NULL OR {_in('error_type', ErrorType)}",
            name="error_type_vocab",
        ),
        CheckConstraint(
            "cached_tokens IS NULL OR prompt_tokens IS NULL "
            "OR cached_tokens <= prompt_tokens",
            name="cached_le_prompt",
        ),
        CheckConstraint(
            "status <> 'success' OR error_type IS NULL",
            name="success_has_no_error_type",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    session_id: Mapped[int] = mapped_column(
        ForeignKey("session.id", ondelete="CASCADE"), nullable=False
    )
    import_batch_id: Mapped[int] = mapped_column(ForeignKey("import_batch.id"), nullable=False)
    raw_record_id: Mapped[int | None] = mapped_column(
        ForeignKey("raw_record.id", ondelete="SET NULL")
    )
    sequence: Mapped[int] = mapped_column(Integer, nullable=False)
    model_name: Mapped[str] = mapped_column(Text, nullable=False)
    provider: Mapped[str | None] = mapped_column(Text)
    prompt_tokens: Mapped[int | None] = mapped_column(Integer)
    completion_tokens: Mapped[int | None] = mapped_column(Integer)
    cached_tokens: Mapped[int | None] = mapped_column(Integer)
    total_tokens: Mapped[int | None] = mapped_column(Integer)  # dérivé (voir doc §7)
    cost_usd: Mapped[float | None] = mapped_column(Float)  # unité : USD
    started_at: Mapped[datetime | None] = mapped_column(_TS)
    ended_at: Mapped[datetime | None] = mapped_column(_TS)
    status: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        default=CallStatus.UNKNOWN.value,
        server_default=text(f"'{CallStatus.UNKNOWN.value}'"),
    )
    error_type: Mapped[str | None] = mapped_column(Text)


class ToolCallRow(Base):
    __tablename__ = "tool_call"
    __table_args__ = (
        UniqueConstraint("session_id", "sequence"),
        CheckConstraint("sequence >= 0", name="sequence_non_negative"),
        CheckConstraint(_in("status", CallStatus), name="status_vocab"),
        CheckConstraint(
            f"error_type IS NULL OR {_in('error_type', ErrorType)}",
            name="error_type_vocab",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    session_id: Mapped[int] = mapped_column(
        ForeignKey("session.id", ondelete="CASCADE"), nullable=False
    )
    model_call_id: Mapped[int | None] = mapped_column(
        ForeignKey("model_call.id", ondelete="SET NULL")
    )
    import_batch_id: Mapped[int] = mapped_column(ForeignKey("import_batch.id"), nullable=False)
    raw_record_id: Mapped[int | None] = mapped_column(
        ForeignKey("raw_record.id", ondelete="SET NULL")
    )
    sequence: Mapped[int] = mapped_column(Integer, nullable=False)
    tool_name: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        default=CallStatus.UNKNOWN.value,
        server_default=text(f"'{CallStatus.UNKNOWN.value}'"),
    )
    error_type: Mapped[str | None] = mapped_column(Text)
    started_at: Mapped[datetime | None] = mapped_column(_TS)
    ended_at: Mapped[datetime | None] = mapped_column(_TS)
    input_bytes: Mapped[int | None] = mapped_column(Integer)
    output_bytes: Mapped[int | None] = mapped_column(Integer)


class ImportRejectRow(Base):
    __tablename__ = "import_reject"
    __table_args__ = (
        Index("ix_import_reject_batch_record", "import_batch_id", "record_index"),
        CheckConstraint(_in("reason_code", RejectReason), name="reason_code_vocab"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    import_batch_id: Mapped[int] = mapped_column(
        ForeignKey("import_batch.id", ondelete="CASCADE"), nullable=False
    )
    record_index: Mapped[int] = mapped_column(Integer, nullable=False)
    target_entity: Mapped[str | None] = mapped_column(Text)
    reason_code: Mapped[str] = mapped_column(Text, nullable=False)
    reason_detail: Mapped[str] = mapped_column(Text, nullable=False)
    payload_json: Mapped[dict[str, Any] | None] = mapped_column(_JSON)


class FieldProfileRow(Base):
    __tablename__ = "field_profile"
    __table_args__ = (
        UniqueConstraint("import_batch_id", "path"),
        CheckConstraint("null_ratio >= 0 AND null_ratio <= 1", name="null_ratio_bounds"),
        CheckConstraint("distinct_count >= 0", name="distinct_count_non_negative"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    import_batch_id: Mapped[int] = mapped_column(
        ForeignKey("import_batch.id", ondelete="CASCADE"), nullable=False
    )
    path: Mapped[str] = mapped_column(Text, nullable=False)
    inferred_type: Mapped[str] = mapped_column(Text, nullable=False)
    null_ratio: Mapped[float] = mapped_column(Float, nullable=False)
    distinct_count: Mapped[int] = mapped_column(Integer, nullable=False)
    sample_values_json: Mapped[list[Any]] = mapped_column(
        _JSON, nullable=False, default=list, server_default=text("'[]'")
    )


class ModelPricingRow(Base):
    """Grille tarifaire par modèle (USD par million de tokens).

    Donnée de référence, éditable : sert à **estimer** ``cost_usd`` quand la
    source ne le fournit pas (cf. ``docs/data/indicators.md`` §3.4). Un coût
    déclaré par la source prime toujours sur l'estimation.
    """

    __tablename__ = "model_pricing"
    __table_args__ = (
        CheckConstraint("input_usd_per_mtok >= 0", name="input_price_non_negative"),
        CheckConstraint("output_usd_per_mtok >= 0", name="output_price_non_negative"),
        CheckConstraint(
            "cached_usd_per_mtok IS NULL OR cached_usd_per_mtok >= 0",
            name="cached_price_non_negative",
        ),
    )

    model_name: Mapped[str] = mapped_column(Text, primary_key=True)
    input_usd_per_mtok: Mapped[float] = mapped_column(Float, nullable=False)
    output_usd_per_mtok: Mapped[float] = mapped_column(Float, nullable=False)
    cached_usd_per_mtok: Mapped[float | None] = mapped_column(Float)


ALL_TABLES = (
    SourceRow,
    RepositoryRow,
    MappingRow,
    ImportBatchRow,
    RawRecordRow,
    SessionRow,
    ModelCallRow,
    ToolCallRow,
    ImportRejectRow,
    FieldProfileRow,
    ModelPricingRow,
)
