"""Petits garde-fous partagés par les entités. Interne au domaine."""

from __future__ import annotations

from agentscope.domain.errors import InvariantViolationError


def ensure(condition: bool, message: str) -> None:
    if not condition:
        raise InvariantViolationError(message)


def ensure_non_empty(value: str, field_name: str) -> None:
    if not value or not value.strip():
        raise InvariantViolationError(f"{field_name} ne peut pas être vide")


def ensure_non_negative(value: float | None, field_name: str) -> None:
    if value is not None and value < 0:
        raise InvariantViolationError(f"{field_name} ne peut pas être négatif (reçu : {value})")
