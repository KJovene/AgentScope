"""Value objects et énumérations du domaine.

Immuables (``frozen=True``), sans identité propre : deux instances de mêmes
valeurs sont équivalentes. Aucune dépendance externe.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

from agentscope.domain._invariants import ensure, ensure_non_negative

# ---------------------------------------------------------------------------
# Énumérations — vocabulaires contrôlés (cf. docs/PLAN.md §5.4)
# ---------------------------------------------------------------------------


class FileFormat(StrEnum):
    JSONL = "jsonl"
    CSV = "csv"
    PARQUET = "parquet"


class ImportStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


class CallStatus(StrEnum):
    SUCCESS = "success"
    ERROR = "error"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"
    UNKNOWN = "unknown"


class ErrorType(StrEnum):
    RATE_LIMIT = "rate_limit"
    TIMEOUT = "timeout"
    TOOL_ERROR = "tool_error"
    MODEL_ERROR = "model_error"
    VALIDATION = "validation"
    OTHER = "other"


class RejectReason(StrEnum):
    UNPARSEABLE_RECORD = "unparseable_record"
    MISSING_REQUIRED_FIELD = "missing_required_field"
    TRANSFORM_FAILED = "transform_failed"
    UNKNOWN_TARGET_FIELD = "unknown_target_field"
    DUPLICATE_IN_FILE = "duplicate_in_file"
    SCHEMA_VIOLATION = "schema_violation"


_ERROR_STATUSES = frozenset({CallStatus.ERROR, CallStatus.TIMEOUT})


# ---------------------------------------------------------------------------
# Value objects
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class Provenance:
    """Rattache un enregistrement normalisé à sa ligne d'origine dans un import."""

    record_index: int
    record_sha256: str

    def __post_init__(self) -> None:
        ensure(self.record_index >= 0, "Provenance.record_index doit être >= 0")
        ensure(bool(self.record_sha256.strip()), "Provenance.record_sha256 est requis")


@dataclass(frozen=True, slots=True)
class Interval:
    """Bornes temporelles d'une session ou d'un appel. Instants attendus en UTC."""

    started_at: datetime | None = None
    ended_at: datetime | None = None

    def __post_init__(self) -> None:
        for label, moment in (("started_at", self.started_at), ("ended_at", self.ended_at)):
            if moment is not None and moment.tzinfo is None:
                raise ValueError(f"Interval.{label} doit être timezone-aware (UTC)")
        if self.started_at is not None and self.ended_at is not None:
            ensure(
                self.ended_at >= self.started_at,
                "Interval : ended_at ne peut pas précéder started_at",
            )

    @property
    def duration_ms(self) -> int | None:
        """Durée en millisecondes, ou ``None`` si une borne manque (jamais 0 par défaut)."""
        if self.started_at is None or self.ended_at is None:
            return None
        return int((self.ended_at - self.started_at).total_seconds() * 1000)


@dataclass(frozen=True, slots=True)
class TokenUsage:
    """Consommation de tokens d'un appel modèle. ``None`` = non fourni par la source."""

    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    cached_tokens: int | None = None

    def __post_init__(self) -> None:
        ensure_non_negative(self.prompt_tokens, "TokenUsage.prompt_tokens")
        ensure_non_negative(self.completion_tokens, "TokenUsage.completion_tokens")
        ensure_non_negative(self.cached_tokens, "TokenUsage.cached_tokens")
        if self.cached_tokens is not None and self.prompt_tokens is not None:
            ensure(
                self.cached_tokens <= self.prompt_tokens,
                "TokenUsage : cached_tokens ne peut pas dépasser prompt_tokens",
            )

    @property
    def total_tokens(self) -> int | None:
        """Somme prompt + completion. ``None`` si les deux sont absents."""
        if self.prompt_tokens is None and self.completion_tokens is None:
            return None
        return (self.prompt_tokens or 0) + (self.completion_tokens or 0)

    @property
    def cache_hit_ratio(self) -> float | None:
        """cached / prompt, dans [0, 1]. ``None`` si non calculable."""
        if not self.prompt_tokens or self.cached_tokens is None:
            return None
        return self.cached_tokens / self.prompt_tokens


def is_error_status(status: CallStatus) -> bool:
    return status in _ERROR_STATUSES
