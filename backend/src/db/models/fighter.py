"""Fighter ORM model."""

import uuid
from datetime import date, datetime, timezone
from typing import Optional

from sqlalchemy import Boolean, Date, DateTime, Float, Integer, String, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.base import Base, SyncableMixin, new_uuid


class Fighter(Base, SyncableMixin):
    __tablename__ = "fighters"
    __table_args__ = (
        {"comment": "MMA fighters — ESPN primary, TSDB/Octagon enrichment"},
    )

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=new_uuid,
    )
    provider: Mapped[str] = mapped_column(String(20), nullable=False)
    external_id: Mapped[str] = mapped_column(String(50), nullable=False)

    # Identity
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    full_name: Mapped[Optional[str]] = mapped_column(String(200))
    short_name: Mapped[Optional[str]] = mapped_column(String(50))
    nickname: Mapped[Optional[str]] = mapped_column(String(100))
    slug: Mapped[Optional[str]] = mapped_column(String(200))

    # Physical
    weight_kg: Mapped[Optional[float]] = mapped_column(Float)
    height_cm: Mapped[Optional[float]] = mapped_column(Float)
    reach_cm: Mapped[Optional[float]] = mapped_column(Float)
    leg_reach_cm: Mapped[Optional[float]] = mapped_column(Float)
    stance: Mapped[Optional[str]] = mapped_column(String(20))

    # Classification
    weight_class_id: Mapped[Optional[str]] = mapped_column(
        UUID(as_uuid=False), ForeignKey("weight_classes.id"),
    )
    weight_class_name: Mapped[Optional[str]] = mapped_column(String(50))

    # Personal
    nationality: Mapped[Optional[str]] = mapped_column(String(100))
    birth_date: Mapped[Optional[date]] = mapped_column(Date)
    birth_location: Mapped[Optional[str]] = mapped_column(String(200))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Media
    headshot_url: Mapped[Optional[str]] = mapped_column(Text)
    cutout_url: Mapped[Optional[str]] = mapped_column(Text)
    render_url: Mapped[Optional[str]] = mapped_column(Text)

    # Bio
    biography: Mapped[Optional[str]] = mapped_column(Text)
    ethnicity: Mapped[Optional[str]] = mapped_column(String(50))
    trains_at: Mapped[Optional[str]] = mapped_column(String(200))
    fighting_style: Mapped[Optional[str]] = mapped_column(String(50))
    debut_date: Mapped[Optional[date]] = mapped_column(Date)

    # Record (summary — breakdown in FighterRecord)
    record_wins: Mapped[int] = mapped_column(Integer, default=0)
    record_losses: Mapped[int] = mapped_column(Integer, default=0)
    record_draws: Mapped[int] = mapped_column(Integer, default=0)
    record_no_contests: Mapped[int] = mapped_column(Integer, default=0)

    # Social
    facebook_url: Mapped[Optional[str]] = mapped_column(Text)
    instagram_url: Mapped[Optional[str]] = mapped_column(Text)
    twitter_url: Mapped[Optional[str]] = mapped_column(Text)
    wikidata_id: Mapped[Optional[str]] = mapped_column(String(20))

    # Relationships
    weight_class: Mapped[Optional["WeightClass"]] = relationship(back_populates="fighters")
    rankings: Mapped[list["Ranking"]] = relationship(back_populates="fighter")
    record_breakdown: Mapped[Optional["FighterRecord"]] = relationship(
        back_populates="fighter", uselist=False,
    )

    def __repr__(self) -> str:
        return f"<Fighter {self.full_name or self.external_id}>"


class FighterRecord(Base, TimestampMixin):
    """Expanded record breakdown — one row per fighter."""

    __tablename__ = "fighter_records"
    __table_args__ = (
        {"comment": "Expanded fighter record — KO/sub/title breakdowns"},
    )

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=new_uuid,
    )
    fighter_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("fighters.id"),
        unique=True, nullable=False,
    )

    # Basic
    wins: Mapped[int] = mapped_column(Integer, default=0)
    losses: Mapped[int] = mapped_column(Integer, default=0)
    draws: Mapped[int] = mapped_column(Integer, default=0)
    no_contests: Mapped[int] = mapped_column(Integer, default=0)

    # Method breakdown
    ko_tko_wins: Mapped[int] = mapped_column(Integer, default=0)
    ko_tko_losses: Mapped[int] = mapped_column(Integer, default=0)
    submission_wins: Mapped[int] = mapped_column(Integer, default=0)
    submission_losses: Mapped[int] = mapped_column(Integer, default=0)

    # Title fights
    title_wins: Mapped[int] = mapped_column(Integer, default=0)
    title_losses: Mapped[int] = mapped_column(Integer, default=0)
    title_draws: Mapped[int] = mapped_column(Integer, default=0)

    # Computed
    total_fights: Mapped[int] = mapped_column(Integer, default=0)
    win_percentage: Mapped[float] = mapped_column(Float, default=0.0)
    finish_rate: Mapped[float] = mapped_column(Float, default=0.0)

    # Display
    record_summary: Mapped[Optional[str]] = mapped_column(String(20))

    # Relationships
    fighter: Mapped["Fighter"] = relationship(back_populates="record_breakdown")
