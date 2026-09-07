"""Erreurs de la couche persistance."""

from __future__ import annotations


class PersistenceError(RuntimeError):
    """Base des erreurs d'infrastructure de persistance."""


class UnknownReferenceError(PersistenceError, LookupError):
    """Une clé naturelle attendue (source, import, session parente) est absente.

    Signale un ordre d'écriture incorrect ou un enregistrement normalisé orphelin.
    """
