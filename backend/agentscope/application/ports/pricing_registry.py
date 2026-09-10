"""Port d'écriture de la grille tarifaire par modèle.

Sert à **estimer** ``model_call.cost_usd`` quand la source ne le déclare pas
(``docs/data/indicators.md`` §3.4). Données de référence, éditables : peuplées
par ``scripts/seed_pricing.py`` depuis ``docs/data/model-pricing.json``.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable


@dataclass(frozen=True, slots=True)
class ModelPrice:
    model_name: str
    input_usd_per_mtok: float
    output_usd_per_mtok: float
    cached_usd_per_mtok: float | None = None


@dataclass(frozen=True, slots=True)
class PricingOutcome:
    upserted: int


@runtime_checkable
class PricingRegistryService(Protocol):
    def list(self) -> list[ModelPrice]: ...

    def upsert(self, prices: list[ModelPrice]) -> PricingOutcome:
        """Crée ou met à jour les tarifs (un tarif change dans le temps)."""
        ...
