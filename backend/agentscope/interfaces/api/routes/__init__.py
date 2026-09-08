"""Routes HTTP (une par ressource)."""
from __future__ import annotations

from agentscope.interfaces.api.routes import (
    analyze,
    chat,
    data_quality,
    imports,
    mappings,
    metrics,
    sessions,
    sources,
)

__all__ = [
    "analyze",
    "chat",
    "data_quality",
    "imports",
    "mappings",
    "metrics",
    "sessions",
    "sources",
]
