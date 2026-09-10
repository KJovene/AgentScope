"""Port de lecture du dashboard (issue I1.9) — côté requête (CQRS).

Lit les vues agrégées (`v_session_metrics`, …) et compose des DTO de présentation.
Aucune écriture. Les identifiants techniques `id` circulent ici (contrairement aux
repositories côté écriture, qui parlent clés naturelles).

Règle « valeur absente = `None`, jamais `0` » : un indicateur non calculable
(aucune donnée de tokens, aucune session chronométrée) revient `None`.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from typing import Any, Protocol, runtime_checkable


class TimeseriesMetric(StrEnum):
    SESSIONS = "sessions"
    TOKENS = "tokens"
    MODEL_CALLS = "model_calls"
    TOOL_CALLS = "tool_calls"
    COST = "cost"
    ERRORS = "errors"


class Granularity(StrEnum):
    DAY = "day"


@dataclass(frozen=True, slots=True)
class MetricFilter:
    """Filtres du dashboard. Tuples vides / `None` = pas de filtre sur cette dimension."""

    sources: tuple[str, ...] = ()
    agents: tuple[str, ...] = ()
    models: tuple[str, ...] = ()
    repositories: tuple[str, ...] = ()  # dépôts de code (SWE-chat)
    date_from: datetime | None = None
    date_to: datetime | None = None  # borne haute exclue


@dataclass(frozen=True, slots=True)
class Page:
    limit: int = 50
    offset: int = 0


@dataclass(frozen=True, slots=True)
class Paginated[T]:
    items: tuple[T, ...]
    total: int
    limit: int
    offset: int


@dataclass(frozen=True, slots=True)
class Indicators:
    session_count: int
    model_call_count: int
    tool_call_count: int
    error_count: int
    total_tokens: int | None
    prompt_tokens: int | None
    completion_tokens: int | None
    cached_tokens: int | None
    total_cost_usd: float | None
    cost_is_estimated: bool  # un coût du périmètre a été estimé (pas déclaré par la source)
    error_rate: float | None
    cache_hit_ratio: float | None
    median_session_duration_ms: float | None


@dataclass(frozen=True, slots=True)
class FilterDimensions:
    """Valeurs distinctes réellement présentes en base, pour alimenter les menus
    déroulants du dashboard. Sans portée : la liste reste complète quels que
    soient les filtres actifs, sinon une valeur sélectionnée pourrait disparaître
    de son propre menu."""

    agents: tuple[str, ...] = ()
    models: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class TimeseriesPoint:
    period: str  # 'YYYY-MM-DD' pour granularity=day
    value: float | None


@dataclass(frozen=True, slots=True)
class SessionListItem:
    session_id: int
    source_name: str
    agent_name: str | None
    repository_name: str | None
    started_at: datetime | None
    duration_ms: int | None
    model_call_count: int
    tool_call_count: int
    total_tokens: int | None
    total_cost_usd: float | None
    error_count: int


@dataclass(frozen=True, slots=True)
class TimelineEntry:
    kind: str  # "model_call" | "tool_call"
    sequence: int
    name: str  # model_name ou tool_name
    status: str
    error_type: str | None
    started_at: datetime | None
    ended_at: datetime | None
    duration_ms: int | None
    prompt_tokens: int | None
    completion_tokens: int | None
    total_tokens: int | None
    cost_usd: float | None


@dataclass(frozen=True, slots=True)
class SessionDetail:
    session_id: int
    source_name: str
    external_id: str
    agent_name: str | None
    repository_name: str | None
    started_at: datetime | None
    ended_at: datetime | None
    duration_ms: int | None
    total_tokens: int | None
    total_cost_usd: float | None
    error_count: int
    has_raw_record: bool  # provenance disponible (lien vers raw_record)
    timeline: tuple[TimelineEntry, ...] = field(default_factory=tuple)


@runtime_checkable
class MetricsQueryService(Protocol):
    def indicators(self, filters: MetricFilter) -> Indicators: ...

    def timeseries(
        self,
        filters: MetricFilter,
        metric: TimeseriesMetric,
        granularity: Granularity = Granularity.DAY,
    ) -> list[TimeseriesPoint]: ...

    def sessions(
        self, filters: MetricFilter, page: Page
    ) -> Paginated[SessionListItem]: ...

    def session_detail(self, session_id: int) -> SessionDetail | None: ...

    def tool_usage(self, f: MetricFilter) -> list[dict[str, Any]]:
        ...

    def dimensions(self) -> FilterDimensions: ...
