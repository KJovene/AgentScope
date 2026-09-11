"""Schémas transverses : pagination par offset et erreurs problem+json (contrat §5.3)."""

from __future__ import annotations

from typing import Any, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class Paginated[T](BaseModel):
    items: list[T]
    total: int
    limit: int
    offset: int


class ProblemDetail(BaseModel):
    """application/problem+json — cf. contrat §5.3."""

    type: str = "about:blank"
    title: str
    status: int
    detail: str | None = None
    errors: list[dict[str, Any]] = Field(default_factory=list)
