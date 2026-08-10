"""Align sync_checkpoints.data with the model's JSONB mapping.

Migration 007 created `sync_checkpoints.data` as sa.JSON() (plain JSON on
Postgres), while the SQLAlchemy model maps the column through `JSONType` =
JSON().with_variant(JSONB(), "postgresql"). Functional today (Postgres accepts
JSONB values into JSON columns), but `alembic autogenerate` would report a
permanent diff and JSONB-only features (GIN indexes, @> operators) would be
unavailable. This migration alters the column to native JSONB, keeping the
local DB, a fresh DB, and the ORM model identical.

Non-destructive: JSON → JSONB is a lossless in-place cast (USING data::jsonb).

Revision ID: 008
Revises: 007
Create Date: 2026-08-10
"""

from collections.abc import Sequence

from alembic import op

revision: str = "008"
down_revision: str | None = "007"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Only meaningful on Postgres; on SQLite (dev/tests) JSONType maps to JSON
    # and this would be a no-op alter. Guard so the migration is portable.
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute(
            "ALTER TABLE sync_checkpoints "
            "ALTER COLUMN data TYPE jsonb USING data::jsonb"
        )


def downgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute(
            "ALTER TABLE sync_checkpoints "
            "ALTER COLUMN data TYPE json USING data::json"
        )
