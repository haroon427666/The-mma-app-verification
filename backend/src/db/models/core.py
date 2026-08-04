"""Ranking, Promotion, Venue, Broadcast, WeightClass, Statistic ORM models."""

from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.base import Base, SyncableMixin, TimestampMixin, new_uuid

if TYPE_CHECKING:
    from src.db.models.event import Event
    from src.db.models.fighter import Fighter


class Promotion(Base, SyncableMixin):
    __tablename__ = "promotions"
    __table_args__ = ({"comment": "MMA promotions/leagues"},)

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=new_uuid)
    provider: Mapped[str] = mapped_column(String(20), nullable=False)
    external_id: Mapped[str] = mapped_column(String(50), nullable=False)

    name: Mapped[str] = mapped_column(String(200), nullable=False)
    abbreviation: Mapped[str | None] = mapped_column(String(10))
    short_name: Mapped[str | None] = mapped_column(String(50))
    slug: Mapped[str | None] = mapped_column(String(100))

    country: Mapped[str | None] = mapped_column(String(100))
    founded_year: Mapped[int | None] = mapped_column(Integer)
    first_event_date: Mapped[str | None] = mapped_column(String(20))
    gender: Mapped[str | None] = mapped_column(String(10))
    season_year: Mapped[int | None] = mapped_column(Integer)

    # TSDB media
    logo_url: Mapped[str | None] = mapped_column(Text)
    poster_url: Mapped[str | None] = mapped_column(Text)
    banner_url: Mapped[str | None] = mapped_column(Text)
    trophy_url: Mapped[str | None] = mapped_column(Text)
    fanart_urls: Mapped[dict[str, Any] | None] = mapped_column(Text)  # JSON

    website: Mapped[str | None] = mapped_column(Text)
    facebook_url: Mapped[str | None] = mapped_column(Text)
    instagram_url: Mapped[str | None] = mapped_column(Text)
    twitter_url: Mapped[str | None] = mapped_column(Text)
    youtube_url: Mapped[str | None] = mapped_column(Text)
    description: Mapped[str | None] = mapped_column(Text)
    tv_rights: Mapped[str | None] = mapped_column(Text)

    events: Mapped[list["Event"]] = relationship(back_populates="promotion")
    rankings: Mapped[list["Ranking"]] = relationship(back_populates="promotion")


class Venue(Base, SyncableMixin):
    __tablename__ = "venues"
    __table_args__ = ({"comment": "Event venues/arenas"},)

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=new_uuid)
    provider: Mapped[str] = mapped_column(String(20), nullable=False)
    external_id: Mapped[str] = mapped_column(String(20), nullable=False)

    name: Mapped[str] = mapped_column(String(200), nullable=False)
    city: Mapped[str | None] = mapped_column(String(100))
    state: Mapped[str | None] = mapped_column(String(100))
    country: Mapped[str | None] = mapped_column(String(100))
    latitude: Mapped[float | None] = mapped_column(Float)
    longitude: Mapped[float | None] = mapped_column(Float)
    capacity: Mapped[int | None] = mapped_column(Integer)
    indoor: Mapped[bool | None] = mapped_column(Boolean)

    events: Mapped[list["Event"]] = relationship(back_populates="venue")


class WeightClass(Base, SyncableMixin):
    __tablename__ = "weight_classes"
    __table_args__ = ({"comment": "Weight divisions"},)

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=new_uuid)
    provider: Mapped[str] = mapped_column(String(20), nullable=False)
    external_id: Mapped[str] = mapped_column(String(20), nullable=False)

    name: Mapped[str] = mapped_column(String(50), nullable=False)
    abbreviation: Mapped[str | None] = mapped_column(String(30))
    min_weight_kg: Mapped[float | None] = mapped_column(Float)
    max_weight_kg: Mapped[float | None] = mapped_column(Float)
    gender: Mapped[str | None] = mapped_column(String(10))

    fighters: Mapped[list["Fighter"]] = relationship(back_populates="weight_class")


class Ranking(Base, SyncableMixin):
    __tablename__ = "rankings"
    __table_args__ = (
        Index("ix_rankings_fighter_id", "fighter_id"),
        Index("ix_rankings_category_name", "category_name"),
        {"comment": "Fighter rankings per category"},
    )

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=new_uuid)
    provider: Mapped[str] = mapped_column(String(20), nullable=False)

    fighter_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("fighters.id"))
    promotion_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("promotions.id"))

    category_name: Mapped[str] = mapped_column(String(100), nullable=False)
    category_type: Mapped[str | None] = mapped_column(String(30))
    rank: Mapped[int] = mapped_column(Integer, nullable=False)
    trend: Mapped[str | None] = mapped_column(String(5))
    is_champion: Mapped[bool] = mapped_column(Boolean, default=False)
    title_defenses: Mapped[int | None] = mapped_column(Integer)
    weight_class_id: Mapped[str | None] = mapped_column(UUID(as_uuid=False), ForeignKey("weight_classes.id"))
    gender: Mapped[str | None] = mapped_column(String(10))

    fighter: Mapped["Fighter"] = relationship(back_populates="rankings")
    promotion: Mapped["Promotion"] = relationship(back_populates="rankings")


class Statistic(Base, TimestampMixin):
    __tablename__ = "statistics"
    __table_args__ = (
        Index("ix_statistics_fighter_id", "fighter_id"),
        Index("ix_statistics_competitor_id", "competitor_id"),
        {"comment": "Fighter statistics — career + per-fight"},
    )

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=new_uuid)
    competitor_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("competitors.id"))
    fighter_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("fighters.id"))

    category: Mapped[str] = mapped_column(String(30), nullable=False)
    label: Mapped[str] = mapped_column(String(100), nullable=False)
    value: Mapped[float] = mapped_column(Float, nullable=False)
    display_value: Mapped[str | None] = mapped_column(String(20))

    synced_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
    )


class Broadcast(Base, SyncableMixin):
    __tablename__ = "broadcasts"
    __table_args__ = (
        Index("ix_broadcasts_event_id", "event_id"),
        {"comment": "Event broadcast details"},
    )

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=new_uuid)
    provider: Mapped[str] = mapped_column(String(20), nullable=False)

    event_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("events.id"))
    network: Mapped[str] = mapped_column(String(100), nullable=False)
    region: Mapped[str | None] = mapped_column(String(50))
    language: Mapped[str | None] = mapped_column(String(10))
    broadcast_type: Mapped[str] = mapped_column(String(20), default="TV")

    event: Mapped["Event"] = relationship(back_populates="broadcasts")
