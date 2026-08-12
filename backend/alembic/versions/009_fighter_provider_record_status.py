"""Phase D — per-provider fighter-record fetch-outcome status table.

Sparse evidence that a fighter was checked against a provider's /records
surface and no usable payload exists (CONFIRMED_ABSENT), or the fetch failed
transiently (FETCH_FAILED) / permanently (PERMANENT_FAILURE).

Semantics (enforced by the sync layer, not the schema):
- fighter_records row present  ⇔ HAS_RECORD — canonical signal; no status row
  is kept for available records.
- status row present           ⇔ CONFIRMED_ABSENT | FETCH_FAILED |
                                 PERMANENT_FAILURE (per provider).
- no row                       ⇔ NOT_CHECKED.

A persisted absence NEVER blocks record insertion: persisting a real record
deletes the status row (FighterUpsert._delete_record_status).

Revision ID: 009
Revises: 008
Create Date: 2026-08-12
"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "009"
down_revision: str | None = "008"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "fighter_provider_record_status",
        sa.Column("fighter_id", sa.Uuid(), nullable=False),
        sa.Column("provider", sa.String(20), nullable=False),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column(
            "last_checked_at", sa.DateTime(timezone=True), nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("last_http_status", sa.Integer(), nullable=True),
        sa.Column("result_detail", sa.Text(), nullable=True),
        sa.Column(
            "retry_count", sa.Integer(), nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column("last_run_id", sa.Uuid(), nullable=True),
        sa.Column("provenance", sa.String(30), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.PrimaryKeyConstraint("fighter_id", "provider"),
        sa.ForeignKeyConstraint(["fighter_id"], ["fighters.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["last_run_id"], ["sync_runs.id"]),
    )
    op.create_index(
        "ix_fighter_provider_record_status_provider_status",
        "fighter_provider_record_status",
        ["provider", "status"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_fighter_provider_record_status_provider_status",
        table_name="fighter_provider_record_status",
    )
    op.drop_table("fighter_provider_record_status")
