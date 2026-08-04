"""Fighter ORM model."""

from datetime import date
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, Date, Float, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.base import Base, SyncableMixin, TimestampMixin, new_uuid

if TYPE_CHECKING:
    from src.db.models.core import Ranking, WeightClass


class Fighter(Base, SyncableMixin):
    __tablename__ = "fighters"
    __table_args__ = (
        Index("ix_fighters_weight_class_name", "weight_class_name"),
        Index("ix_fighters_nationality", "nationality"),
        Index("ix_fighters_full_name", "full_name"),
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
    full_name: Mapped[str | None] = mapped_column(String(200))
    short_name: Mapped[str | None] = mapped_column(String(50))
    nickname: Mapped[str | None] = mapped_column(String(100))
    slug: Mapped[str | None] = mapped_column(String(200))

    # Physical
    weight_kg: Mapped[float | None] = mapped_column(Float)
    height_cm: Mapped[float | None] = mapped_column(Float)
    reach_cm: Mapped[float | None] = mapped_column(Float)
    leg_reach_cm: Mapped[float | None] = mapped_column(Float)
    stance: Mapped[str | None] = mapped_column(String(20))

    # Classification
    weight_class_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=False), ForeignKey("weight_classes.id"),
    )
    weight_class_name: Mapped[str | None] = mapped_column(String(50))

    # Personal
    nationality: Mapped[str | None] = mapped_column(String(100))
    birth_date: Mapped[date | None] = mapped_column(Date)
    birth_location: Mapped[str | None] = mapped_column(String(200))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Media
    headshot_url: Mapped[str | None] = mapped_column(Text)
    cutout_url: Mapped[str | None] = mapped_column(Text)
    render_url: Mapped[str | None] = mapped_column(Text)

    # Bio
    biography: Mapped[str | None] = mapped_column(Text)
    ethnicity: Mapped[str | None] = mapped_column(String(50))
    trains_at: Mapped[str | None] = mapped_column(String(200))
    fighting_style: Mapped[str | None] = mapped_column(String(50))
    debut_date: Mapped[date | None] = mapped_column(Date)

    # Record (summary — breakdown in FighterRecord)
    record_wins: Mapped[int] = mapped_column(Integer, default=0)
    record_losses: Mapped[int] = mapped_column(Integer, default=0)
    record_draws: Mapped[int] = mapped_column(Integer, default=0)
    record_no_contests: Mapped[int] = mapped_column(Integer, default=0)

    # Social
    facebook_url: Mapped[str | None] = mapped_column(Text)
    instagram_url: Mapped[str | None] = mapped_column(Text)
    twitter_url: Mapped[str | None] = mapped_column(Text)
    wikidata_id: Mapped[str | None] = mapped_column(String(20))

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
    record_summary: Mapped[str | None] = mapped_column(String(20))

    # Relationships
    fighter: Mapped["Fighter"] = relationship(back_populates="record_breakdown")
