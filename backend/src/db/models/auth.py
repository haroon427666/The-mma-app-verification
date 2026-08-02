"""Auth ORM models — User, Session, Preference, Favorite, Notification, Device.

All auth tables. Separate from core MMA data tables.
Supports: JWT auth, OAuth, email verification, RBAC, sessions, push devices.
"""

import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import Boolean, DateTime, Integer, String, Text, ForeignKey, JSON, Index, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.base import Base, TimestampMixin, new_uuid


# ── User ───────────────────────────────────────────────────────────────────

class User(Base, TimestampMixin):
    __tablename__ = "users"
    __table_args__ = ({"comment": "Platform users"},)

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=new_uuid)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    display_name: Mapped[Optional[str]] = mapped_column(String(100))
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    avatar_url: Mapped[Optional[str]] = mapped_column(Text)

    # Profile
    country: Mapped[Optional[str]] = mapped_column(String(2))  # ISO 3166-1 alpha-2
    timezone: Mapped[str] = mapped_column(String(50), default="UTC")
    language: Mapped[str] = mapped_column(String(10), default="en")

    # Verification
    email_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    email_verify_token: Mapped[Optional[str]] = mapped_column(String(128))
    password_reset_token: Mapped[Optional[str]] = mapped_column(String(128))
    password_reset_expires: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    # Role-based access
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False)
    is_moderator: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Security
    login_attempts: Mapped[int] = mapped_column(Integer, default=0)
    locked_until: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    last_login_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    last_login_ip: Mapped[Optional[str]] = mapped_column(String(45))

    # OAuth
    google_id: Mapped[Optional[str]] = mapped_column(String(100), unique=True)
    apple_id: Mapped[Optional[str]] = mapped_column(String(100), unique=True)

    # Relationships
    preferences: Mapped[Optional["UserPreference"]] = relationship(back_populates="user", uselist=False)
    sessions: Mapped[list["UserSession"]] = relationship(back_populates="user")
    notifications: Mapped[list["Notification"]] = relationship(back_populates="user")
    devices: Mapped[list["Device"]] = relationship(back_populates="user")

    @property
    def role(self) -> str:
        if self.is_admin: return "admin"
        if self.is_moderator: return "moderator"
        return "user"

    def __repr__(self) -> str:
        return f"<User {self.email}>"


# ── Session ────────────────────────────────────────────────────────────────

class UserSession(Base, TimestampMixin):
    __tablename__ = "user_sessions"
    __table_args__ = ({"comment": "Active user sessions — for logout-everywhere"},)

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=new_uuid)
    user_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("users.id"), nullable=False)

    refresh_token_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    device: Mapped[Optional[str]] = mapped_column(String(50))
    browser: Mapped[Optional[str]] = mapped_column(String(200))
    ip_address: Mapped[Optional[str]] = mapped_column(String(45))
    country: Mapped[Optional[str]] = mapped_column(String(100))

    last_seen: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc),
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked: Mapped[bool] = mapped_column(Boolean, default=False)

    user: Mapped["User"] = relationship(back_populates="sessions")


# ── Preferences ────────────────────────────────────────────────────────────

class UserPreference(Base, TimestampMixin):
    __tablename__ = "user_preferences"
    __table_args__ = ({"comment": "User display + notification preferences"},)

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=new_uuid)
    user_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("users.id"),
                                          unique=True, nullable=False)

    # Display
    theme: Mapped[str] = mapped_column(String(20), default="system")
    default_homepage: Mapped[str] = mapped_column(String(50), default="rankings")
    default_sort: Mapped[str] = mapped_column(String(30), default="-date_utc")

    # Filters
    default_weight_classes: Mapped[Optional[list]] = mapped_column(JSON)  # ["Lightweight", ...]
    default_promotions: Mapped[Optional[list]] = mapped_column(JSON)  # ["ufc", ...]

    # Notifications
    notify_upcoming_fight: Mapped[bool] = mapped_column(Boolean, default=True)
    notify_event_starting: Mapped[bool] = mapped_column(Boolean, default=True)
    notify_ranking_changed: Mapped[bool] = mapped_column(Boolean, default=False)
    notify_fight_cancelled: Mapped[bool] = mapped_column(Boolean, default=True)
    notify_new_main_event: Mapped[bool] = mapped_column(Boolean, default=True)
    notify_title_fight: Mapped[bool] = mapped_column(Boolean, default=True)

    user: Mapped["User"] = relationship(back_populates="preferences")


# ── Favorites ──────────────────────────────────────────────────────────────

class FighterFavorite(Base, TimestampMixin):
    __tablename__ = "favorite_fighters"
    __table_args__ = (
        {"comment": "Users can follow fighters"},
        UniqueConstraint("user_id", "fighter_id", name="uq_fav_fighters_user_fighter"),
        Index("ix_fav_fighters_user", "user_id"),
    )

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=new_uuid)
    user_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    fighter_id: Mapped[str] = mapped_column(UUID(as_uuid=False), nullable=False)  # FK to fighters.id
    followed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc),
    )


class EventFavorite(Base, TimestampMixin):
    __tablename__ = "favorite_events"
    __table_args__ = (
        {"comment": "Users can follow events"},
        UniqueConstraint("user_id", "event_id", name="uq_fav_events_user_event"),
        Index("ix_fav_events_user", "user_id"),
    )

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=new_uuid)
    user_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    event_id: Mapped[str] = mapped_column(UUID(as_uuid=False), nullable=False)
    followed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc),
    )


# ── Watchlist ──────────────────────────────────────────────────────────────

class WatchlistEvent(Base, TimestampMixin):
    __tablename__ = "watchlist_events"
    __table_args__ = (
        {"comment": "\"I don't want to miss this\" events"},
        UniqueConstraint("user_id", "event_id", name="uq_watchlist_user_event"),
        Index("ix_watchlist_user", "user_id"),
    )

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=new_uuid)
    user_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    event_id: Mapped[str] = mapped_column(UUID(as_uuid=False), nullable=False)
    added_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc),
    )


# ── Notifications ──────────────────────────────────────────────────────────

class Notification(Base, TimestampMixin):
    __tablename__ = "notifications"
    __table_args__ = ({"comment": "User notifications — event alerts, ranking changes"},)

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=new_uuid)
    user_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("users.id"), nullable=False)

    ntype: Mapped[str] = mapped_column(String(30), nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    message: Mapped[Optional[str]] = mapped_column(Text)
    payload: Mapped[Optional[dict]] = mapped_column(JSON)  # event_id, fighter_id, etc.
    read: Mapped[bool] = mapped_column(Boolean, default=False)
    read_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    user: Mapped["User"] = relationship(back_populates="notifications")


# ── Device ─────────────────────────────────────────────────────────────────

class Device(Base, TimestampMixin):
    __tablename__ = "devices"
    __table_args__ = ({"comment": "Push notification device tokens"},)

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=new_uuid)
    user_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("users.id"), nullable=False)

    platform: Mapped[str] = mapped_column(String(10), nullable=False)  # ios, android, web
    device_token: Mapped[str] = mapped_column(String(500), nullable=False)
    device_name: Mapped[Optional[str]] = mapped_column(String(100))
    last_seen: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc),
    )
    active: Mapped[bool] = mapped_column(Boolean, default=True)

    user: Mapped["User"] = relationship(back_populates="devices")
