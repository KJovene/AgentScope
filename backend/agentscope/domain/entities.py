"""Entités du domaine AgentScope.

Dataclasses **pures** : aucune dépendance à un framework, un ORM, HTTP ou un SDK IA
(règle vérifiée par ``import-linter`` et ``tests/unit/domain/test_purity.py``).

Les entités sont immuables et **identifiées par leur clé naturelle**, pas par une
clé de substitution : la persistance (couche infrastructure) fait la correspondance
avec les colonnes ``id`` techniques. Ce que représente chaque entité et ses clés
sont documentés dans ``docs/data/relational-model.md`` (issue I1.2).

Relations exprimées par les clés naturelles :
- ``ModelCall`` / ``ToolCall`` -> ``Session`` via ``(source_name, session_external_id)``
- ``ToolCall`` -> ``ModelCall`` via ``model_call_sequence`` (optionnel)
- ``Session`` -> ``Repository`` via ``repository_name`` (optionnel)
- tout enregistrement normalisé -> import d'origine via ``provenance``
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from agentscope.domain._invariants import ensure, ensure_non_empty, ensure_non_negative
from agentscope.domain.errors import InvariantViolationError
from agentscope.domain.value_objects import (
    CallStatus,
    ErrorType,
    FileFormat,
    ImportStatus,
    Interval,
    Provenance,
    RejectReason,
    TokenUsage,
    is_error_status,
)

# ---------------------------------------------------------------------------
# Référentiel
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class Source:
    """Un projet source de traces (TraceLab, SWE-chat, ...). Clé : ``name``."""

    name: str
    display_name: str | None = None
    homepage_url: str | None = None

    def __post_init__(self) -> None:
        ensure_non_empty(self.name, "Source.name")


@dataclass(frozen=True, slots=True)
class Repository:
    """Un dépôt de code référencé par des sessions. Clé : ``(source_name, name)``."""

    source_name: str
    name: str
    url: str | None = None
    language: str | None = None

    def __post_init__(self) -> None:
        ensure_non_empty(self.source_name, "Repository.source_name")
        ensure_non_empty(self.name, "Repository.name")


# ---------------------------------------------------------------------------
# Ingestion & provenance
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class RawRecord:
    """Un enregistrement source tel que lu, avant toute transformation."""

    index: int
    payload: dict[str, Any]
    sha256: str
    parse_error: str | None = None

    def __post_init__(self) -> None:
        ensure(self.index >= 0, "RawRecord.index doit être >= 0")
        ensure_non_empty(self.sha256, "RawRecord.sha256")


@dataclass(frozen=True, slots=True)
class ImportBatch:
    """Un import : une exécution d'ingestion d'un fichier.

    Idempotence : clé naturelle ``(source_name, file_sha256)``.
    """

    source_name: str
    original_filename: str
    file_sha256: str
    file_format: FileFormat
    imported_at: datetime
    status: ImportStatus = ImportStatus.PENDING
    mapping_name: str | None = None
    imported_count: int = 0
    duplicate_count: int = 0
    rejected_count: int = 0
    missing_info_count: int = 0

    def __post_init__(self) -> None:
        ensure_non_empty(self.source_name, "ImportBatch.source_name")
        ensure_non_empty(self.original_filename, "ImportBatch.original_filename")
        ensure_non_empty(self.file_sha256, "ImportBatch.file_sha256")
        if self.imported_at.tzinfo is None:
            raise ValueError("ImportBatch.imported_at doit être timezone-aware (UTC)")
        for name in (
            "imported_count",
            "duplicate_count",
            "rejected_count",
            "missing_info_count",
        ):
            ensure_non_negative(getattr(self, name), f"ImportBatch.{name}")

    @property
    def total_processed(self) -> int:
        return self.imported_count + self.duplicate_count + self.rejected_count


@dataclass(frozen=True, slots=True)
class ImportReject:
    """Un enregistrement rejeté lors d'un import, avec une raison consultable."""

    record_index: int
    reason: RejectReason
    detail: str
    payload: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        ensure(self.record_index >= 0, "ImportReject.record_index doit être >= 0")
        ensure_non_empty(self.detail, "ImportReject.detail")


# ---------------------------------------------------------------------------
# Cœur des traces
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class Session:
    """Une session d'agent. Clé naturelle : ``(source_name, external_id)``."""

    source_name: str
    external_id: str
    provenance: Provenance
    agent_name: str | None = None
    interval: Interval = field(default_factory=Interval)
    repository_name: str | None = None

    def __post_init__(self) -> None:
        ensure_non_empty(self.source_name, "Session.source_name")
        ensure_non_empty(self.external_id, "Session.external_id")

    @property
    def duration_ms(self) -> int | None:
        return self.interval.duration_ms


@dataclass(frozen=True, slots=True)
class ModelCall:
    """Un appel à un modèle dans une session.

    Clé naturelle : ``(source_name, session_external_id, sequence)``.
    """

    source_name: str
    session_external_id: str
    sequence: int
    model_name: str
    provenance: Provenance
    provider: str | None = None
    tokens: TokenUsage = field(default_factory=TokenUsage)
    cost_usd: float | None = None
    interval: Interval = field(default_factory=Interval)
    status: CallStatus = CallStatus.UNKNOWN
    error_type: ErrorType | None = None

    def __post_init__(self) -> None:
        ensure_non_empty(self.source_name, "ModelCall.source_name")
        ensure_non_empty(self.session_external_id, "ModelCall.session_external_id")
        ensure_non_empty(self.model_name, "ModelCall.model_name")
        ensure(self.sequence >= 0, "ModelCall.sequence doit être >= 0")
        ensure_non_negative(self.cost_usd, "ModelCall.cost_usd")
        _check_status_consistency("ModelCall", self.status, self.error_type)

    @property
    def total_tokens(self) -> int | None:
        return self.tokens.total_tokens

    @property
    def is_error(self) -> bool:
        return is_error_status(self.status)


@dataclass(frozen=True, slots=True)
class ToolCall:
    """Un appel d'outil dans une session.

    Clé naturelle : ``(source_name, session_external_id, sequence)``.
    """

    source_name: str
    session_external_id: str
    sequence: int
    tool_name: str
    provenance: Provenance
    model_call_sequence: int | None = None
    interval: Interval = field(default_factory=Interval)
    status: CallStatus = CallStatus.UNKNOWN
    error_type: ErrorType | None = None
    input_bytes: int | None = None
    output_bytes: int | None = None

    def __post_init__(self) -> None:
        ensure_non_empty(self.source_name, "ToolCall.source_name")
        ensure_non_empty(self.session_external_id, "ToolCall.session_external_id")
        ensure_non_empty(self.tool_name, "ToolCall.tool_name")
        ensure(self.sequence >= 0, "ToolCall.sequence doit être >= 0")
        if self.model_call_sequence is not None:
            ensure(
                self.model_call_sequence >= 0,
                "ToolCall.model_call_sequence doit être >= 0",
            )
        ensure_non_negative(self.input_bytes, "ToolCall.input_bytes")
        ensure_non_negative(self.output_bytes, "ToolCall.output_bytes")
        _check_status_consistency("ToolCall", self.status, self.error_type)

    @property
    def is_error(self) -> bool:
        return is_error_status(self.status)


# ---------------------------------------------------------------------------
# Mapping (configuration d'import réutilisable)
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class SourceMapping:
    """Une configuration de mapping enregistrée. Clé : ``(name, version)``.

    ``definition`` porte le document du contrat de mapping (docs/PLAN.md §5.1) ;
    sa validation vit dans ``application/mapping`` (issue I2.13), pas ici.
    """

    name: str
    version: int
    source_name: str
    source_format: FileFormat
    definition: dict[str, Any]
    created_at: datetime
    is_active: bool = True
    created_by: str | None = None

    def __post_init__(self) -> None:
        ensure_non_empty(self.name, "SourceMapping.name")
        ensure_non_empty(self.source_name, "SourceMapping.source_name")
        ensure(self.version >= 1, "SourceMapping.version doit être >= 1")
        ensure(bool(self.definition), "SourceMapping.definition ne peut pas être vide")
        if self.created_at.tzinfo is None:
            raise ValueError("SourceMapping.created_at doit être timezone-aware (UTC)")


# ---------------------------------------------------------------------------
# Profilage de champs (analyse d'un fichier inconnu)
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class FieldProfile:
    """Profil statistique d'un champ source, calculé par le programme (jamais par l'IA)."""

    path: str
    inferred_type: str
    null_ratio: float
    distinct_count: int
    sample_values: tuple[Any, ...] = ()

    def __post_init__(self) -> None:
        ensure_non_empty(self.path, "FieldProfile.path")
        ensure_non_empty(self.inferred_type, "FieldProfile.inferred_type")
        ensure(
            0.0 <= self.null_ratio <= 1.0,
            "FieldProfile.null_ratio doit être dans [0, 1]",
        )
        ensure(self.distinct_count >= 0, "FieldProfile.distinct_count doit être >= 0")


@dataclass(frozen=True, slots=True)
class FieldProfileSet:
    """Profil complet d'un fichier : nombre d'enregistrements + profil par champ."""

    record_count: int
    fields: tuple[FieldProfile, ...]

    def __post_init__(self) -> None:
        ensure(self.record_count >= 0, "FieldProfileSet.record_count doit être >= 0")

    def by_path(self, path: str) -> FieldProfile | None:
        return next((f for f in self.fields if f.path == path), None)


# ---------------------------------------------------------------------------

def _check_status_consistency(
    entity: str, status: CallStatus, error_type: ErrorType | None
) -> None:
    if status is CallStatus.SUCCESS and error_type is not None:
        raise InvariantViolationError(
            f"{entity} : error_type doit être absent quand status == success"
        )
    if status is CallStatus.ERROR and error_type is None:
        raise InvariantViolationError(f"{entity} : error_type est requis quand status == error")
