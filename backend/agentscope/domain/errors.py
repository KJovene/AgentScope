"""Erreurs du domaine. Aucune dépendance externe."""

from __future__ import annotations


class DomainError(Exception):
    """Base de toutes les erreurs métier."""


class InvariantViolationError(DomainError):
    """Un invariant d'entité ou de value object n'est pas respecté."""


class InvalidMappingError(DomainError):
    """Un mapping ne respecte pas le contrat attendu (détail applicatif ailleurs)."""
