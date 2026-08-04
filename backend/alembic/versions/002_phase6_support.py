"""Phase 6 support tables + syncable columns — 4 new tables, missing metrics columns.

Adds tables omitted from 001_initial_schema:
- fighter_records — expanded KO/sub/title breakdown
- provider_conflicts — audit trail for provider disagreements
- provider_payloads — raw JSON archive for debugging + replay
- sync_checkpoints — resume checkpoint persistence

Adds missing metric columns on sync_runs:
- total_inserted, total_updated, total_skipped, total_errors
- api_calls, duration_ms

Adds SyncableMixin columns on entity tables:
- synced_at, source_provider, version

Note: fighter_images intentionally omitted — images are stored as URL columns
(headshot_url, cutout_url, render_url) directly on fighters table.
See OPERATIONAL_READINESS.md for rationale.

Revision ID: 002
Revises: 001
Create Date: 2026-08-01
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ══════════════════════════════════════════════════════════════════════════
    # 1. fighter_records — expanded record breakdown
    # ══════════════════════════════════════════════════════════════════════════
    op.create_table(
        "fighter_records",
        sa.Column("id", sa.Uuid(), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("fighter_id", sa.Uuid(), sa.ForeignKey("fighters.id"), nullable=False),
        # Basic
        sa.Column("wins", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("losses", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("draws", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("no_contests", sa.Integer(), nullable=False, server_default=sa.text("0")),
        # Method breakdown
        sa.Column("ko_tko_wins", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("ko_tko_losses", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("submission_wins", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("submission_losses", sa.Integer(), nullable=False, server_default=sa.text("0")),
        # Title fights
        sa.Column("title_wins", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("title_losses", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("title_draws", sa.Integer(), nullable=False, server_default=sa.text("0")),
        # Computed
        sa.Column("total_fights", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("win_percentage", sa.Float(), nullable=False, server_default=sa.text("0")),
        sa.Column("finish_rate", sa.Float(), nullable=False, server_default=sa.text("0")),
        # Display
        sa.Column("record_summary", sa.String(20), nullable=True),
        # Timestamps
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.UniqueConstraint("fighter_id", name="uq_fighter_records_fighter_id"),
        sa.ForeignKeyConstraint(["fighter_id"], ["fighters.id"], name="fk_fighter_records_fighter"),
    )

    # ══════════════════════════════════════════════════════════════════════════
    # 2. provider_conflicts — disagreement audit trail
    # ══════════════════════════════════════════════════════════════════════════
    op.create_table(
        "provider_conflicts",
        sa.Column("id", sa.Uuid(), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("entity_type", sa.String(30), nullable=False),
        sa.Column("entity_id", sa.Uuid(), nullable=False),
        sa.Column("field", sa.String(100), nullable=False),
        sa.Column("provider_a", sa.String(20), nullable=False),
        sa.Column("provider_b", sa.String(20), nullable=False),
        sa.Column("value_a", sa.Text(), nullable=True),
        sa.Column("value_b", sa.Text(), nullable=True),
        sa.Column("chosen_authority", sa.String(20), nullable=False),
        sa.Column("chosen_value", sa.Text(), nullable=True),
        sa.Column("resolution", sa.String(30), nullable=False, server_default=sa.text("'AUTHORITY'")),
        sa.Column("resolved", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )

    # ══════════════════════════════════════════════════════════════════════════
    # 3. provider_payloads — raw JSON archive
    # ══════════════════════════════════════════════════════════════════════════
    op.create_table(
        "provider_payloads",
        sa.Column("id", sa.Uuid(), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("provider", sa.String(20), nullable=False),
        sa.Column("endpoint", sa.String(200), nullable=False),
        sa.Column("entity_type", sa.String(30), nullable=False),
        sa.Column("external_id", sa.String(50), nullable=True),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("fetched_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )

    # ══════════════════════════════════════════════════════════════════════════
    # 4. sync_checkpoints — resume checkpoint persistence
    # ══════════════════════════════════════════════════════════════════════════
    op.create_table(
        "sync_checkpoints",
        sa.Column("id", sa.Uuid(), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("entity_type", sa.String(30), nullable=False),
        sa.Column("provider", sa.String(20), nullable=False),
        sa.Column("last_offset", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("last_page", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("total_records", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("status", sa.String(20), nullable=False, server_default=sa.text("'IN_PROGRESS'")),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("completed", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.UniqueConstraint("entity_type", "provider", name="uq_sync_checkpoints_entity_provider"),
    )

    # ══════════════════════════════════════════════════════════════════════════
    # 5. Missing columns on sync_runs — phase 6 metrics
    # ══════════════════════════════════════════════════════════════════════════
    op.add_column("sync_runs", sa.Column("total_inserted", sa.Integer(), nullable=False, server_default=sa.text("0")))
    op.add_column("sync_runs", sa.Column("total_updated", sa.Integer(), nullable=False, server_default=sa.text("0")))
    op.add_column("sync_runs", sa.Column("total_skipped", sa.Integer(), nullable=False, server_default=sa.text("0")))
    op.add_column("sync_runs", sa.Column("total_errors", sa.Integer(), nullable=False, server_default=sa.text("0")))
    op.add_column("sync_runs", sa.Column("api_calls", sa.Integer(), nullable=False, server_default=sa.text("0")))
    op.add_column("sync_runs", sa.Column("duration_ms", sa.Float(), nullable=False, server_default=sa.text("0")))

    # ══════════════════════════════════════════════════════════════════════════
    # 6. SyncableMixin columns on entity tables
    # ══════════════════════════════════════════════════════════════════════════
    def _make_syncable_columns():
        """Fresh columns per table — Alembic mutates column objects on add."""
        return [
            sa.Column("synced_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("source_provider", sa.String(20), nullable=False, server_default=sa.text("'espn'")),
            sa.Column("version", sa.Integer(), nullable=False, server_default=sa.text("1")),
        ]

    # NOTE: "rankings" intentionally excluded — 001_initial_schema already creates
    # rankings.synced_at (line 219). Re-adding it here raises DuplicateColumnError
    # on a fresh database. rankings.source_provider + version are added in 005.
    for table in ["fighters", "events", "competitions", "promotions", "venues",
                   "broadcasts", "weight_classes"]:
        for col in _make_syncable_columns():
            op.add_column(table, col)

    # ══════════════════════════════════════════════════════════════════════════
    # 7. Indexes on new tables
    # ══════════════════════════════════════════════════════════════════════════
    op.create_index("ix_provider_payloads_provider_entity", "provider_payloads",
                    ["provider", "entity_type", "external_id"])
    op.create_index("ix_provider_conflicts_entity", "provider_conflicts",
                    ["entity_type", "entity_id"])
    op.create_index("ix_sync_checkpoints_status", "sync_checkpoints", ["completed"])


def downgrade() -> None:
    # Remove syncable columns from entity tables
    # NOTE: "rankings" intentionally excluded — matches upgrade() (001 already
    # creates rankings.synced_at; rankings.source_provider/version come from 005).
    for table in ["fighters", "events", "competitions", "promotions", "venues",
                   "broadcasts", "weight_classes"]:
        for col_name in ["synced_at", "source_provider", "version"]:
            op.drop_column(table, col_name)

    # Remove metrics columns from sync_runs
    for col_name in ["total_inserted", "total_updated", "total_skipped",
                      "total_errors", "api_calls", "duration_ms"]:
        op.drop_column("sync_runs", col_name)

    # Drop Phase 6 tables
    op.drop_table("sync_checkpoints")
    op.drop_table("provider_payloads")
    op.drop_table("provider_conflicts")
    op.drop_table("fighter_records")
