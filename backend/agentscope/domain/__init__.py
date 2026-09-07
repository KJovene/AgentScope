"""Couche domaine : entites et regles metier pures, sans dependance externe.

Point d'entree public du domaine — importer depuis ``agentscope.domain`` plutot
que des sous-modules.
"""

from agentscope.domain.entities import (
    FieldProfile,
    FieldProfileSet,
    ImportBatch,
    ImportReject,
    ModelCall,
    RawRecord,
    Repository,
    Session,
    Source,
    SourceMapping,
    ToolCall,
)
from agentscope.domain.errors import DomainError, InvalidMappingError, InvariantViolationError
from agentscope.domain.retention import RetentionMode, RetentionPolicy
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

__all__ = [
    # entités
    "Source",
    "Repository",
    "RawRecord",
    "ImportBatch",
    "ImportReject",
    "Session",
    "ModelCall",
    "ToolCall",
    "SourceMapping",
    "FieldProfile",
    "FieldProfileSet",
    # value objects
    "Provenance",
    "Interval",
    "TokenUsage",
    "FileFormat",
    "ImportStatus",
    "CallStatus",
    "ErrorType",
    "RejectReason",
    "is_error_status",
    # rétention
    "RetentionMode",
    "RetentionPolicy",
    # erreurs
    "DomainError",
    "InvariantViolationError",
    "InvalidMappingError",
]
