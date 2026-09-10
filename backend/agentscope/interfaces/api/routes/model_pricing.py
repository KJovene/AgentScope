"""Route ``/model-pricing`` — grille tarifaire par modèle (USD / million de tokens).

Donnée de référence, éditable. Sert à estimer ``model_call.cost_usd`` quand la
source ne le déclare pas (``docs/data/indicators.md`` §3.4). Un coût déclaré par
la source prime toujours.
"""

from __future__ import annotations

from fastapi import APIRouter

from agentscope.application.ports.pricing_registry import ModelPrice
from agentscope.interfaces.api.dependencies import PricingRegistryServiceDep
from agentscope.interfaces.api.schemas.sources import (
    ModelPriceInput,
    ModelPriceResponse,
    PricingUpsertResult,
)

router = APIRouter(tags=["pricing"])


@router.get("/model-pricing", response_model=list[ModelPriceResponse])
async def list_model_pricing(
    service: PricingRegistryServiceDep,
) -> list[ModelPriceResponse]:
    return [
        ModelPriceResponse(
            model_name=p.model_name,
            input_usd_per_mtok=p.input_usd_per_mtok,
            output_usd_per_mtok=p.output_usd_per_mtok,
            cached_usd_per_mtok=p.cached_usd_per_mtok,
        )
        for p in service.list()
    ]


@router.post(
    "/model-pricing", response_model=PricingUpsertResult, status_code=201
)
async def upsert_model_pricing(
    prices: list[ModelPriceInput], service: PricingRegistryServiceDep
) -> PricingUpsertResult:
    """Crée ou met à jour (idempotent) les tarifs par modèle."""
    outcome = service.upsert(
        [
            ModelPrice(
                model_name=p.model_name,
                input_usd_per_mtok=p.input_usd_per_mtok,
                output_usd_per_mtok=p.output_usd_per_mtok,
                cached_usd_per_mtok=p.cached_usd_per_mtok,
            )
            for p in prices
        ]
    )
    return PricingUpsertResult(upserted=outcome.upserted)
