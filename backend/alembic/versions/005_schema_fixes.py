"""Schema fixes — align migrations with ORM models.

Resolves verified model↔migration drift (fresh-DB + runtime problems):

1. rankings missing SyncableMixin columns (002 loop no longer covers rankings —
   001 //-created rankings.synced_at; source_provider + version add here):
   adds source_provider, version, updated_at.
2. statistics missing updated_at (TimestampMixin; 001 created only synced_at+created_at).
3. broadcasts missing updated_at (SyncableMixin requires created_at + updated_at).
4. competitors missing updated_at (TimestampMixin).
5. external_ids missing updated_at + matched_by (TimestampMixin + model column).
6. sync_runs missing updated_at (TimestampMixin).
7. sync_jobs missing updated_at (TimestampMixin).
8. dead_letters missing updated_at (TimestampMixin).
9. promotions.first_event_date Date → String(20) (model is String(20)).
10. promotions.fanart_urls JSON → Text (model is Text; parser never populates it).
11. events.time_utc Time → String(10) (model is String(10)).

Revision ID: 005
Revises: 004
Create Date: 2026-08-04
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "005"
down_revision: Union[str, None] = "004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _add_updated_at(table: str) -> None:
    op.add_column(
        table,
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )


def upgrade() -> None:
    # ── rankings — SyncableMixin columns (synced_at created in 001) ────────
    op.add_column(
        "rankings",
        sa.Column("source_provider", sa.String(20), nullable=False, server_default=sa.text("'espn'")),
    )
    op.add_column(
        "rankings",
        sa.Column("version", sa.Integer(), nullable=False, server_default=sa.text("1")),
    )
    _add_updated_at("rankings")

    # ── missing TimestampMixin.updated_at on 001 tables ────────────────────
    _add_updated_at("statistics")
    _add_updated_at("broadcasts")
    _add_updated_at("competitors")
    _add_updated_at("external_ids")
    _add_updated_at("sync_runs")
    _add_updated_at("sync_jobs")
    _add_updated_at("dead_letters")

    # ── external_ids.matched_by (model column, missing from 001) ───────────
    op.add_column("external_ids", sa.Column("matched_by", sa.String(30), nullable=True))

    # ── type alignment: migrations → model types ───────────────────────────
    op.alter_column("promotions", "first_event_date", existing_type=sa.Date(), type_=sa.String(20))
    op.alter_column("promotions", "fanart_urls", existing_type=sa.JSON(), type_=sa.Text())
    op.alter_column("events", "time_utc", existing_type=sa.Time(), type_=sa.String(10))


def downgrade() -> None:
    op.alter_column("events", "time_utc", existing_type=sa.String(10), type_=sa.Time())
    op.alter_column("promotions", "fanart_urls", existing_type=sa.Text(), type_=sa.JSON())
    op.alter_column("promotions", "first_event_date", existing_type=sa.String(20), type_=sa.Date())

    op.drop_column("external_ids", "matched_by")
    _drop_updated_at("dead_letters")
    _drop_updated_at("sync_jobs")
    _drop_updated_at("sync_runs")
    _drop_updated_at("external_ids")
    _drop_updated_at("competitors")
    _drop_updated_at("broadcasts")
    _drop_updated_at("statistics")
    op.drop_column("rankings", "version")
    op.drop_column("rankings", "source_provider")
    _drop_updated_at("rankings")


def _drop_updated_at(table: str) -> None:
    op.drop_column(table, "updated_at")