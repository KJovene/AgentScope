"""Vues agrégées du dashboard (issue I1.6).

Revision ID: 0002_dashboard_views
Revises: 0001_initial
Create Date: 2026-09-07

Crée v_session_metrics / v_daily_activity / v_tool_usage / v_data_quality.
Le SQL dialecte-dépendant vit dans ``agentscope.infrastructure.persistence.views``.
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

from agentscope.infrastructure.persistence.views import create_all_views, drop_all_views

revision: str = "0002_dashboard_views"
down_revision: str | None = "0001_initial"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    create_all_views(op.get_bind())


def downgrade() -> None:
    drop_all_views(op.get_bind())
