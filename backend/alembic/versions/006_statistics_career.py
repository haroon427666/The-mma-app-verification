"""Make statistics.competitor_id nullable — career stats support.

Career statistics (/athletes/{id}/statistics) are fighter-scoped and have no
competition → competitor_id is NULL. Per-fight statistics keep a competitor_id.

1. statistics.competitor_id: NOT NULL → NULL
2. Partial unique index for career rows: (fighter_id, category, label) where
   competitor_id IS NULL — prevents duplicate career rows without affecting
   per-fight rows (which keep the original uq_statistics_comp_cat_label).

Revision ID: 006
Revises: 005
Create Date: 2026-08-09
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "006"
down_revision: Union[str, None] = "005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column(
        "statistics",
        "competitor_id",
        existing_type=sa.Uuid(),
        nullable=True,
    )
    op.create_index(
        "uq_statistics_career_fighter_cat_label",
        "statistics",
        ["fighter_id", "category", "label"],
        unique=True,
        postgresql_where=sa.text("competitor_id IS NULL"),
    )


def downgrade() -> None:
    op.drop_index(
        "uq_statistics_career_fighter_cat_label",
        table_name="statistics",
        postgresql_where=sa.text("competitor_id IS NULL"),
    )
    op.alter_column(
        "statistics",
        "competitor_id",
        existing_type=sa.Uuid(),
        nullable=False,
    )
