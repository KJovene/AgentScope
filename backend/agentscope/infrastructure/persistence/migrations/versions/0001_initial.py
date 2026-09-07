"""Schéma initial v1 (10 tables + contraintes d'unicité pour l'idempotence).

Revision ID: 0001_initial
Revises:
Create Date: 2026-09-07

Le schéma est créé à partir de ``Base.metadata`` : la migration ne peut pas diverger
des modèles ORM. Les migrations suivantes seront des diffs classiques (autogenerate).
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

from agentscope.infrastructure.persistence import orm_models  # noqa: F401  (peuple la metadata)
from agentscope.infrastructure.persistence.database import Base

revision: str = "0001_initial"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    Base.metadata.create_all(bind=op.get_bind())


def downgrade() -> None:
    Base.metadata.drop_all(bind=op.get_bind())
