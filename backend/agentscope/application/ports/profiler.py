"""Ports applicatifs pour le profilage des fichiers source."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Protocol

from agentscope.domain import FieldProfileSet, RawRecord


class FieldProfiler(Protocol):
    """Calcule un profil statistique sans modifier les enregistrements."""

    def profile(self, records: Iterable[RawRecord], sample_size: int) -> FieldProfileSet:
        """Profile les champs plats et imbriqués d'un flux d'enregistrements."""


class SensitiveFilter(Protocol):
    """Masque une valeur avant son exposition dans un échantillon."""

    def scrub(self, value: object) -> object:
        """Retourne une valeur sûre à exposer à un autre composant."""
