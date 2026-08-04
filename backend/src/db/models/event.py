"""Event, Competition, Competitor ORM models."""

from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.base import Base, SyncableMixin, TimestampMixin, new_uuid

if TYPE_CHECKING:
    from src.db.models.core import Broadcast, Promotion, Venue
    from src.db.models.fighter import Fighter


class Event(Base, SyncableMixin):
    __tablename__ = "events"
    __table_args__ = (
        Index("ix_events_promotion_id", "promotion_id"),
        {"comment": "MMA events — fight cards"},
    )

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=new_uuid)
    provider: Mapped[str] = mapped_column(String(20), nullable=False)
    external_id: Mapped[str] = mapped_column(String(50), nullable=False)

    name: Mapped[str] = mapped_column(String(300), nullable=False)
    short_name: Mapped[str | None] = mapped_column(String(100))
    slug: Mapped[str | None] = mapped_column(String(200))

    date_utc: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    time_utc: Mapped[str | None] = mapped_column(String(10))
    time_local: Mapped[str | None] = mapped_column(String(10))
    status: Mapped[str] = mapped_column(String(20), default="SCHEDULED")
    season: Mapped[str | None] = mapped_column(String(10))

    promotion_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("promotions.id"))
    venue_id: Mapped[str | None] = mapped_column(UUID(as_uuid=False), ForeignKey("venues.id"))

    venue_name_inline: Mapped[str | None] = mapped_column(String(200))
    city_inline: Mapped[str | None] = mapped_column(String(100))
    country_inline: Mapped[str | None] = mapped_column(String(100))

    # TSDB media
    poster_url: Mapped[str | None] = mapped_column(Text)
    square_url: Mapped[str | None] = mapped_column(Text)
    fanart_url: Mapped[str | None] = mapped_column(Text)
    thumbnail_url: Mapped[str | None] = mapped_column(Text)
    banner_url: Mapped[str | None] = mapped_column(Text)
    description: Mapped[str | None] = mapped_column(Text)
    spectators: Mapped[int | None] = mapped_column(Integer)

    # Relationships
    promotion: Mapped["Promotion"] = relationship(back_populates="events")
    venue: Mapped[Optional["Venue"]] = relationship(back_populates="events")
    competitions: Mapped[list["Competition"]] = relationship(back_populates="event")
    broadcasts: Mapped[list["Broadcast"]] = relationship(back_populates="event")


class Competition(Base, SyncableMixin):
    __tablename__ = "competitions"
    __table_args__ = (
        Index("ix_competitions_event_id", "event_id"),
        {"comment": "Individual fights within an event"},
    )

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=new_uuid)
    provider: Mapped[str] = mapped_column(String(20), nullable=False)
    external_id: Mapped[str] = mapped_column(String(50), nullable=False)

    event_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("events.id"))
    order_num: Mapped[int] = mapped_column(Integer, default=0)
    card_segment: Mapped[str | None] = mapped_column(String(30))
    status: Mapped[str] = mapped_column(String(20), default="SCHEDULED")
    is_main_event: Mapped[bool] = mapped_column(Boolean, default=False)
    is_title_fight: Mapped[bool] = mapped_column(Boolean, default=False)
    description: Mapped[str | None] = mapped_column(String(50))

    weight_class_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=False), ForeignKey("weight_classes.id"),
    )
    weight_class_name: Mapped[str | None] = mapped_column(String(50))

    # Result (FINAL only)
    result_method: Mapped[str | None] = mapped_column(String(30))
    result_detail: Mapped[str | None] = mapped_column(String(100))
    result_round: Mapped[int | None] = mapped_column(Integer)
    result_time: Mapped[str | None] = mapped_column(String(10))

    # Relationships
    event: Mapped["Event"] = relationship(back_populates="competitions")
    competitors: Mapped[list["Competitor"]] = relationship(back_populates="competition")


class Competitor(Base, TimestampMixin):
    __tablename__ = "competitors"
    __table_args__ = (
        Index("ix_competitors_competition_id", "competition_id"),
        Index("ix_competitors_fighter_id", "fighter_id"),
        {"comment": "Fighter in a competition — corner + outcome"},
    )

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=new_uuid)

    competition_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("competitions.id"), nullable=False,
    )
    fighter_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("fighters.id"), nullable=False,
    )

    corner: Mapped[str] = mapped_column(String(10), nullable=False)
    outcome: Mapped[str | None] = mapped_column(String(10))

    # Relationships
    competition: Mapped["Competition"] = relationship(back_populates="competitors")
    fighter: Mapped["Fighter"] = relationship()
