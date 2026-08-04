"""Auth tables — 8 tables from src/db/models/auth.py.

Omitted from 001/002/003. Every auth model (User, UserSession, UserPreference,
FighterFavorite, EventFavorite, WatchlistEvent, Notification, Device) now has a
matching migration.

Revision ID: 004
Revises: 003
Create Date: 2026-08-04
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "004"
down_revision: Union[str, None] = "003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _uuid_pk(name: str) -> sa.Column:
    return sa.Column(name, sa.Uuid(), primary_key=True, server_default=sa.text("gen_random_uuid()"))


def upgrade() -> None:
    # ── users ─────────────────────────────────────────────────────────────
    op.create_table(
        "users",
        _uuid_pk("id"),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("username", sa.String(50), nullable=False),
        sa.Column("display_name", sa.String(100), nullable=True),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("avatar_url", sa.Text(), nullable=True),
        sa.Column("country", sa.String(2), nullable=True),
        sa.Column("timezone", sa.String(50), nullable=False, server_default=sa.text("'UTC'")),
        sa.Column("language", sa.String(10), nullable=False, server_default=sa.text("'en'")),
        sa.Column("email_verified", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("email_verify_token", sa.String(128), nullable=True),
        sa.Column("password_reset_token", sa.String(128), nullable=True),
        sa.Column("password_reset_expires", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_admin", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("is_moderator", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("login_attempts", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("locked_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_login_ip", sa.String(45), nullable=True),
        sa.Column("google_id", sa.String(100), nullable=True),
        sa.Column("apple_id", sa.String(100), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.UniqueConstraint("email", name="uq_users_email"),
        sa.UniqueConstraint("username", name="uq_users_username"),
        sa.UniqueConstraint("google_id", name="uq_users_google_id"),
        sa.UniqueConstraint("apple_id", name="uq_users_apple_id"),
    )

    # ── user_sessions ──────────────────────────────────────────────────────
    op.create_table(
        "user_sessions",
        _uuid_pk("id"),
        sa.Column("user_id", sa.Uuid(), sa.ForeignKey("users.id", name="fk_user_sessions_user"), nullable=False),
        sa.Column("refresh_token_hash", sa.String(255), nullable=False),
        sa.Column("device", sa.String(50), nullable=True),
        sa.Column("browser", sa.String(200), nullable=True),
        sa.Column("ip_address", sa.String(45), nullable=True),
        sa.Column("country", sa.String(100), nullable=True),
        sa.Column("last_seen", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("ix_user_sessions_user_id", "user_sessions", ["user_id"])

    # ── user_preferences ───────────────────────────────────────────────────
    op.create_table(
        "user_preferences",
        _uuid_pk("id"),
        sa.Column("user_id", sa.Uuid(), sa.ForeignKey("users.id", name="fk_user_preferences_user"), nullable=False),
        sa.Column("theme", sa.String(20), nullable=False, server_default=sa.text("'system'")),
        sa.Column("default_homepage", sa.String(50), nullable=False, server_default=sa.text("'rankings'")),
        sa.Column("default_sort", sa.String(30), nullable=False, server_default=sa.text("'-date_utc'")),
        sa.Column("default_weight_classes", sa.JSON(), nullable=True),
        sa.Column("default_promotions", sa.JSON(), nullable=True),
        sa.Column("notify_upcoming_fight", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("notify_event_starting", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("notify_ranking_changed", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("notify_fight_cancelled", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("notify_new_main_event", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("notify_title_fight", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.UniqueConstraint("user_id", name="uq_user_preferences_user_id"),
    )

    # ── favorite_fighters ──────────────────────────────────────────────────
    op.create_table(
        "favorite_fighters",
        _uuid_pk("id"),
        sa.Column("user_id", sa.Uuid(), sa.ForeignKey("users.id", name="fk_fav_fighters_user", ondelete="CASCADE"), nullable=False),
        sa.Column("fighter_id", sa.Uuid(), nullable=False),
        sa.Column("followed_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.UniqueConstraint("user_id", "fighter_id", name="uq_fav_fighters_user_fighter"),
        sa.Index("ix_fav_fighters_user", "user_id"),
    )

    # ── favorite_events ────────────────────────────────────────────────────
    op.create_table(
        "favorite_events",
        _uuid_pk("id"),
        sa.Column("user_id", sa.Uuid(), sa.ForeignKey("users.id", name="fk_fav_events_user", ondelete="CASCADE"), nullable=False),
        sa.Column("event_id", sa.Uuid(), nullable=False),
        sa.Column("followed_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.UniqueConstraint("user_id", "event_id", name="uq_fav_events_user_event"),
        sa.Index("ix_fav_events_user", "user_id"),
    )

    # ── watchlist_events ───────────────────────────────────────────────────
    op.create_table(
        "watchlist_events",
        _uuid_pk("id"),
        sa.Column("user_id", sa.Uuid(), sa.ForeignKey("users.id", name="fk_watchlist_user", ondelete="CASCADE"), nullable=False),
        sa.Column("event_id", sa.Uuid(), nullable=False),
        sa.Column("added_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.UniqueConstraint("user_id", "event_id", name="uq_watchlist_user_event"),
        sa.Index("ix_watchlist_user", "user_id"),
    )

    # ── notifications ──────────────────────────────────────────────────────
    op.create_table(
        "notifications",
        _uuid_pk("id"),
        sa.Column("user_id", sa.Uuid(), sa.ForeignKey("users.id", name="fk_notifications_user"), nullable=False),
        sa.Column("ntype", sa.String(30), nullable=False),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("message", sa.Text(), nullable=True),
        sa.Column("payload", sa.JSON(), nullable=True),
        sa.Column("read", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("read_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("ix_notifications_user_id", "notifications", ["user_id"])

    # ── devices ────────────────────────────────────────────────────────────
    op.create_table(
        "devices",
        _uuid_pk("id"),
        sa.Column("user_id", sa.Uuid(), sa.ForeignKey("users.id", name="fk_devices_user"), nullable=False),
        sa.Column("platform", sa.String(10), nullable=False),
        sa.Column("device_token", sa.String(500), nullable=False),
        sa.Column("device_name", sa.String(100), nullable=True),
        sa.Column("last_seen", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("ix_devices_user_id", "devices", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_devices_user_id", table_name="devices")
    op.drop_table("devices")
    op.drop_index("ix_notifications_user_id", table_name="notifications")
    op.drop_table("notifications")
    op.drop_index("ix_watchlist_user", table_name="watchlist_events")
    op.drop_table("watchlist_events")
    op.drop_index("ix_fav_events_user", table_name="favorite_events")
    op.drop_table("favorite_events")
    op.drop_index("ix_fav_fighters_user", table_name="favorite_fighters")
    op.drop_table("favorite_fighters")
    op.drop_table("user_preferences")
    op.drop_index("ix_user_sessions_user_id", table_name="user_sessions")
    op.drop_table("user_sessions")
    op.drop_table("users")