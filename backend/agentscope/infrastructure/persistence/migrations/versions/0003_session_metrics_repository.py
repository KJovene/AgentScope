"""v_session_metrics : ajout de `repository_name` (dimension SWE-chat, issue I1.10).

Revision ID: 0003_session_metrics_repository
Revises: 0002_dashboard_views
Create Date: 2026-09-07

Les vues sont dérivées : on les recrée toutes depuis
``agentscope.infrastructure.persistence.views``. Un downgrade recrée l'état
courant du module (les migrations de vues ne sont pas des reverts exacts).
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

from agentscope.infrastructure.persistence.views import create_all_views, drop_all_views

revision: str = "0003_session_metrics_repository"
down_revision: str | None = "0002_dashboard_views"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    drop_all_views(op.get_bind())
    create_all_views(op.get_bind())


def downgrade() -> None:
    drop_all_views(op.get_bind())
    create_all_views(op.get_bind())
