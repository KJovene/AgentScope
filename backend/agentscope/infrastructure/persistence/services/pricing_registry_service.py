"""Implémentation de ``PricingRegistryService`` — upsert de la grille tarifaire."""

from __future__ import annotations

import builtins

from sqlalchemy import select
from sqlalchemy.orm import Session

from agentscope.application.ports.pricing_registry import ModelPrice, PricingOutcome
from agentscope.infrastructure.persistence.orm_models import ModelPricingRow
from agentscope.infrastructure.persistence.repositories._helpers import _dialect_insert


class SqlPricingRegistryService:
    def __init__(self, session: Session) -> None:
        self._s = session

    def list(self) -> builtins.list[ModelPrice]:
        rows = (
            self._s.execute(select(ModelPricingRow).order_by(ModelPricingRow.model_name))
            .scalars()
            .all()
        )
        return [
            ModelPrice(
                model_name=r.model_name,
                input_usd_per_mtok=r.input_usd_per_mtok,
                output_usd_per_mtok=r.output_usd_per_mtok,
                cached_usd_per_mtok=r.cached_usd_per_mtok,
            )
            for r in rows
        ]

    def upsert(self, prices: builtins.list[ModelPrice]) -> PricingOutcome:
        if not prices:
            return PricingOutcome(upserted=0)
        insert = _dialect_insert(self._s)
        rows = [
            {
                "model_name": p.model_name,
                "input_usd_per_mtok": p.input_usd_per_mtok,
                "output_usd_per_mtok": p.output_usd_per_mtok,
                "cached_usd_per_mtok": p.cached_usd_per_mtok,
            }
            for p in prices
        ]
        stmt = insert(ModelPricingRow).values(rows)
        stmt = stmt.on_conflict_do_update(
            index_elements=["model_name"],
            set_={
                "input_usd_per_mtok": stmt.excluded.input_usd_per_mtok,
                "output_usd_per_mtok": stmt.excluded.output_usd_per_mtok,
                "cached_usd_per_mtok": stmt.excluded.cached_usd_per_mtok,
            },
        )
        self._s.execute(stmt)
        self._s.commit()
        return PricingOutcome(upserted=len(rows))
