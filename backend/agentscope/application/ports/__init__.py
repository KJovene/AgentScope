"""Ports : interfaces abstraites implementees par l'infrastructure.

API publique de la couche application côté persistance. Les implémentations
concrètes (SQLAlchemy) vivent dans ``agentscope.infrastructure`` et sont câblées
dans le conteneur de composition.
"""

from agentscope.application.ports.metrics import (
    Granularity,
    Indicators,
    MetricFilter,
    MetricsQueryService,
    Page,
    Paginated,
    SessionDetail,
    SessionListItem,
    TimelineEntry,
    TimeseriesMetric,
    TimeseriesPoint,
)
from agentscope.application.ports.provenance import ProvenanceRepository
from agentscope.application.ports.repositories import (
    FieldProfileRepository,
    ImportRepository,
    MappingRepository,
    ModelCallRepository,
    RawRecordRepository,
    ReferenceRepository,
    RejectRepository,
    SessionRepository,
    ToolCallRepository,
    UpsertOutcome,
)
from agentscope.application.ports.unit_of_work import UnitOfWork

__all__ = [
    "UpsertOutcome",
    "ReferenceRepository",
    "MappingRepository",
    "ImportRepository",
    "RawRecordRepository",
    "SessionRepository",
    "ModelCallRepository",
    "ToolCallRepository",
    "RejectRepository",
    "FieldProfileRepository",
    "ProvenanceRepository",
    "UnitOfWork",
    # lecture dashboard (I1.9)
    "MetricsQueryService",
    "MetricFilter",
    "Page",
    "Paginated",
    "Indicators",
    "TimeseriesPoint",
    "TimeseriesMetric",
    "Granularity",
    "SessionListItem",
    "SessionDetail",
    "TimelineEntry",
]
