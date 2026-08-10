"""Durable discovery registry + resumable discovery checkpoints.

Production window phases (discovery ordering + resume):

1. sync_checkpoints.data — JSONB payload carrying SyncState fields that have
   no dedicated column (checkpoint dict, timestamps, cursors). This is what
   makes DatabaseSyncStateStore work over the EXISTING checkpoint table.

2. sync_discovered_athletes — deduplicated athlete-ID registry. Every
   discovery surface (global listing walk, roster walks, ranking injection,
   competition/eventlog refs) converges here; unique (provider, external_id).
   consumed=false rows are the fighter window's queue.

3. sync_discovery_checkpoints — per-source resumable walk state (page/offset/
   discovered count/last athlete id/completion). A COMPLETED source is never
   re-walked unless ESPN_DISCOVERY_FORCE=1.

4. Backfill: existing synced fighters (external_ids rows) are seeded into the
   registry as consumed so the first post-deploy window advances to NEW ids —
   no repeated prefix scanning of the already-synced census.

Revision ID: 007
Revises: 006
Create Date: 2026-08-10
"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "007"
down_revision: str | None = "006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 1. SyncState payload on the existing checkpoint table
    op.add_column(
        "sync_checkpoints",
        sa.Column("data", sa.JSON(), nullable=True),
    )

    # 2. Deduplicated athlete-ID registry (discovery convergence point)
    op.create_table(
        "sync_discovered_athletes",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("provider", sa.String(20), nullable=False),
        sa.Column("external_id", sa.String(50), nullable=False),
        sa.Column("source", sa.String(50), nullable=False),
        sa.Column("run_id", sa.Uuid(), nullable=True),
        sa.Column("consumed", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.UniqueConstraint("provider", "external_id", name="uq_sync_discovered_athletes_provider_external"),
    )
    # Window query: next N unconsumed ids per provider
    op.create_index(
        "ix_sync_discovered_athletes_window",
        "sync_discovered_athletes",
        ["provider", "consumed"],
    )

    # 3. Per-source resumable discovery-walk checkpoints
    op.create_table(
        "sync_discovery_checkpoints",
        sa.Column("id", sa.Uuid(), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("provider", sa.String(20), nullable=False),
        sa.Column("source", sa.String(50), nullable=False),
        sa.Column("league_slug", sa.String(30), nullable=False, server_default=sa.text("''")),
        sa.Column("page", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("offset", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("discovered_count", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("last_athlete_id", sa.String(50), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default=sa.text("'IN_PROGRESS'")),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("completed", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("run_id", sa.Uuid(), nullable=True),
        sa.Column("last_processed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.UniqueConstraint("provider", "source", "league_slug", name="uq_sync_discovery_checkpoints_source"),
    )
    op.create_index(
        "ix_sync_discovery_checkpoints_status",
        "sync_discovery_checkpoints",
        ["provider", "completed"],
    )

    # 4. Seed already-synced fighters as consumed (idempotent, provenance 'backfill')
    op.execute(
        sa.text(
            """
            INSERT INTO sync_discovered_athletes
                (provider, external_id, source, consumed, created_at, updated_at)
            SELECT DISTINCT provider, external_id, 'backfill', true, now(), now()
            FROM external_ids
            WHERE entity_type = 'fighter'
            ON CONFLICT (provider, external_id) DO NOTHING
            """
        )
    )


def downgrade() -> None:
    op.drop_index("ix_sync_discovery_checkpoints_status", table_name="sync_discovery_checkpoints")
    op.drop_table("sync_discovery_checkpoints")
    op.drop_index("ix_sync_discovered_athletes_window", table_name="sync_discovered_athletes")
    op.drop_table("sync_discovered_athletes")
    op.drop_column("sync_checkpoints", "data")
