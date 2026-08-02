"""Database base — shared columns for all models.

Every table gets: UUID PK, created_at, updated_at, synced_at, source_provider, version.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class TimestampMixin:
    """Shared timestamp columns for all tables."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )


class SyncableMixin(TimestampMixin):
    """Columns for syncable entities — track last sync + provider.

    NOTE: fighter_images table is intentionally NOT created.
    Images are stored as URL columns directly on the fighters table:
    - headshot_url (Espn CDN + Octagon UFC render)
    - cutout_url (TheSportsDB transparent PNG)
    - render_url (TheSportsDB 3D render)
    A separate images table would add unnecessary JOIN overhead.
    See OPERATIONAL_READINESS.md for full rationale.
    """

    synced_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=True,
    )
    source_provider: Mapped[str] = mapped_column(
        String(20),
        default="espn",
        nullable=False,
    )
    version: Mapped[int] = mapped_column(
        Integer,
        default=1,
        nullable=False,
    )


def new_uuid() -> str:
    return str(uuid.uuid4())
