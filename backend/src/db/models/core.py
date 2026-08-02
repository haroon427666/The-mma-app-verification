"""Ranking, Promotion, Venue, Broadcast, WeightClass, Statistic ORM models."""

from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, Float, Integer, String, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.base import Base, SyncableMixin, TimestampMixin, new_uuid


class Promotion(Base, SyncableMixin):
    __tablename__ = "promotions"
    __table_args__ = ({"comment": "MMA promotions/leagues"},)

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=new_uuid)
    provider: Mapped[str] = mapped_column(String(20), nullable=False)
    external_id: Mapped[str] = mapped_column(String(50), nullable=False)

    name: Mapped[str] = mapped_column(String(200), nullable=False)
    abbreviation: Mapped[Optional[str]] = mapped_column(String(10))
    short_name: Mapped[Optional[str]] = mapped_column(String(50))
    slug: Mapped[Optional[str]] = mapped_column(String(100))

    country: Mapped[Optional[str]] = mapped_column(String(100))
    founded_year: Mapped[Optional[int]] = mapped_column(Integer)
    first_event_date: Mapped[Optional[str]] = mapped_column(String(20))
    gender: Mapped[Optional[str]] = mapped_column(String(10))
    season_year: Mapped[Optional[int]] = mapped_column(Integer)

    # TSDB media
    logo_url: Mapped[Optional[str]] = mapped_column(Text)
    poster_url: Mapped[Optional[str]] = mapped_column(Text)
    banner_url: Mapped[Optional[str]] = mapped_column(Text)
    trophy_url: Mapped[Optional[str]] = mapped_column(Text)
    fanart_urls: Mapped[Optional[dict]] = mapped_column(Text)  # JSON

    website: Mapped[Optional[str]] = mapped_column(Text)
    facebook_url: Mapped[Optional[str]] = mapped_column(Text)
    instagram_url: Mapped[Optional[str]] = mapped_column(Text)
    twitter_url: Mapped[Optional[str]] = mapped_column(Text)
    youtube_url: Mapped[Optional[str]] = mapped_column(Text)
    description: Mapped[Optional[str]] = mapped_column(Text)
    tv_rights: Mapped[Optional[str]] = mapped_column(Text)

    events: Mapped[list["Event"]] = relationship(back_populates="promotion")
    rankings: Mapped[list["Ranking"]] = relationship(back_populates="promotion")


class Venue(Base, SyncableMixin):
    __tablename__ = "venues"
    __table_args__ = ({"comment": "Event venues/arenas"},)

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=new_uuid)
    provider: Mapped[str] = mapped_column(String(20), nullable=False)
    external_id: Mapped[str] = mapped_column(String(20), nullable=False)

    name: Mapped[str] = mapped_column(String(200), nullable=False)
    city: Mapped[Optional[str]] = mapped_column(String(100))
    state: Mapped[Optional[str]] = mapped_column(String(100))
    country: Mapped[Optional[str]] = mapped_column(String(100))
    latitude: Mapped[Optional[float]] = mapped_column(Float)
    longitude: Mapped[Optional[float]] = mapped_column(Float)
    capacity: Mapped[Optional[int]] = mapped_column(Integer)
    indoor: Mapped[Optional[bool]] = mapped_column(Boolean)

    events: Mapped[list["Event"]] = relationship(back_populates="venue")


class WeightClass(Base, SyncableMixin):
    __tablename__ = "weight_classes"
    __table_args__ = ({"comment": "Weight divisions"},)

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=new_uuid)
    provider: Mapped[str] = mapped_column(String(20), nullable=False)
    external_id: Mapped[str] = mapped_column(String(20), nullable=False)

    name: Mapped[str] = mapped_column(String(50), nullable=False)
    abbreviation: Mapped[Optional[str]] = mapped_column(String(30))
    min_weight_kg: Mapped[Optional[float]] = mapped_column(Float)
    max_weight_kg: Mapped[Optional[float]] = mapped_column(Float)
    gender: Mapped[Optional[str]] = mapped_column(String(10))

    fighters: Mapped[list["Fighter"]] = relationship(back_populates="weight_class")


class Ranking(Base, SyncableMixin):
    __tablename__ = "rankings"
    __table_args__ = ({"comment": "Fighter rankings per category"},)

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=new_uuid)
    provider: Mapped[str] = mapped_column(String(20), nullable=False)

    fighter_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("fighters.id"))
    promotion_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("promotions.id"))

    category_name: Mapped[str] = mapped_column(String(100), nullable=False)
    category_type: Mapped[Optional[str]] = mapped_column(String(30))
    rank: Mapped[int] = mapped_column(Integer, nullable=False)
    trend: Mapped[Optional[str]] = mapped_column(String(5))
    is_champion: Mapped[bool] = mapped_column(Boolean, default=False)
    title_defenses: Mapped[Optional[int]] = mapped_column(Integer)
    weight_class_id: Mapped[Optional[str]] = mapped_column(UUID(as_uuid=False), ForeignKey("weight_classes.id"))
    gender: Mapped[Optional[str]] = mapped_column(String(10))

    fighter: Mapped["Fighter"] = relationship(back_populates="rankings")
    promotion: Mapped["Promotion"] = relationship(back_populates="rankings")


class Statistic(Base, TimestampMixin):
    __tablename__ = "statistics"
    __table_args__ = ({"comment": "Fighter statistics — career + per-fight"},)

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=new_uuid)
    competitor_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("competitors.id"))
    fighter_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("fighters.id"))

    category: Mapped[str] = mapped_column(String(30), nullable=False)
    label: Mapped[str] = mapped_column(String(100), nullable=False)
    value: Mapped[float] = mapped_column(Float, nullable=False)
    display_value: Mapped[Optional[str]] = mapped_column(String(20))

    synced_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(),
    )


class Broadcast(Base, SyncableMixin):
    __tablename__ = "broadcasts"
    __table_args__ = ({"comment": "Event broadcast details"},)

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=new_uuid)
    provider: Mapped[str] = mapped_column(String(20), nullable=False)

    event_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("events.id"))
    network: Mapped[str] = mapped_column(String(100), nullable=False)
    region: Mapped[Optional[str]] = mapped_column(String(50))
    language: Mapped[Optional[str]] = mapped_column(String(10))
    broadcast_type: Mapped[str] = mapped_column(String(20), default="TV")

    event: Mapped["Event"] = relationship(back_populates="broadcasts")
