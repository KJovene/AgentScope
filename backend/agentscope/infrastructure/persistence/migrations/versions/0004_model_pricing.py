"""Table `model_pricing` + coût estimé dans les vues (docs/data/indicators.md §3.4).

Revision ID: 0004_model_pricing
Revises: 0003_session_metrics_repository
Create Date: 2026-09-10

Ajoute la grille tarifaire par modèle et recrée les vues : `v_session_metrics`
expose désormais `cost_usd` = coût déclaré par la source, **sinon** estimé
`tokens × tarif`. Sans ligne de tarif, l'estimation reste NULL.
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

from agentscope.infrastructure.persistence.orm_models import ModelPricingRow
from agentscope.infrastructure.persistence.views import create_all_views, drop_all_views

revision: str = "0004_model_pricing"
down_revision: str | None = "0003_session_metrics_repository"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    bind = op.get_bind()
    # `checkfirst` : sur une base neuve, 0001 (schéma dérivé de la metadata) a déjà
    # créé la table ; sur une base antérieure à cette révision, on la crée ici.
    ModelPricingRow.__table__.create(bind=bind, checkfirst=True)
    drop_all_views(bind)
    create_all_views(bind)


def downgrade() -> None:
    bind = op.get_bind()
    drop_all_views(bind)
    ModelPricingRow.__table__.drop(bind=bind, checkfirst=True)
    create_all_views(bind)
