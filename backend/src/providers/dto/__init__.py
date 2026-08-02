"""
Provider Data Transfer Objects (DTOs).

These are internal data structures that flow from providers (ESPN, Tapology, etc.)
through the sync engine to repositories. They are provider-agnostic: every provider
returns the same DTO shapes, so the sync engine never knows which provider the data
came from.

Key design decisions:
- Simple dataclasses, not Pydantic models (internal use only — no validation needed at this layer;
  validation happens at the API boundary with Pydantic schemas).
- All datetime fields are UTC-aware.
- Optional fields use `None` — we never fabricate data.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


# ── Promotion ──────────────────────────────────────────────────────────────────


@dataclass
class PromotionDTO:
    provider: str  # "espn", "tapology", etc.
    external_id: str
    name: str
    slug: str
    country: Optional[str] = None
    logo_url: Optional[str] = None
    season_year: Optional[int] = None


# ── Fighter ────────────────────────────────────────────────────────────────────


@dataclass
class FighterDTO:
    provider: str
    external_id: str
    first_name: str
    last_name: str
    nickname: Optional[str] = None
    short_name: Optional[str] = None
    record_wins: int = 0
    record_losses: int = 0
    record_draws: int = 0
    record_no_contests: int = 0
    height_cm: Optional[float] = None
    weight_kg: Optional[float] = None
    reach_cm: Optional[float] = None
    stance: Optional[str] = None
    nationality: Optional[str] = None
    birth_date: Optional[datetime] = None
    headshot_url: Optional[str] = None
    weight_class_external_id: Optional[str] = None  # resolved later by sync engine


# ── Weight Class ───────────────────────────────────────────────────────────────


@dataclass
class WeightClassDTO:
    provider: str
    external_id: str
    name: str
    abbreviation: str
    min_weight_kg: Optional[float] = None
    max_weight_kg: Optional[float] = None
    gender: Optional[str] = None


# ── Venue ──────────────────────────────────────────────────────────────────────


@dataclass
class VenueDTO:
    provider: str
    external_id: str
    name: str
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    capacity: Optional[int] = None


# ── Event ──────────────────────────────────────────────────────────────────────


@dataclass
class EventDTO:
    provider: str
    external_id: str
    name: str
    short_name: Optional[str] = None
    date: Optional[datetime] = None
    status: str = "SCHEDULED"  # SCHEDULED, FINAL, CANCELLED
    slug: Optional[str] = None
    promotion_external_id: Optional[str] = None
    venue_external_id: Optional[str] = None


# ── Broadcast ──────────────────────────────────────────────────────────────────


@dataclass
class BroadcastDTO:
    provider: str
    event_external_id: str
    network: str
    region: Optional[str] = None
    language: Optional[str] = None
    broadcast_type: str = "TV"  # TV, STREAMING, PPV


# ── Competition (Fight / Bout) ─────────────────────────────────────────────────


@dataclass
class CompetitionDTO:
    provider: str
    external_id: str
    event_external_id: str
    order_num: int = 0
    card_segment: Optional[str] = None  # "main-card", "prelims", "early-prelims"
    status: str = "SCHEDULED"
    is_main_event: bool = False
    is_title_fight: bool = False
    weight_class_external_id: Optional[str] = None
    result_method: Optional[str] = None
    result_detail: Optional[str] = None
    result_round: Optional[int] = None
    result_time: Optional[str] = None
    competitors: list["CompetitorDTO"] = field(default_factory=list)


# ── Competitor ─────────────────────────────────────────────────────────────────


@dataclass
class CompetitorDTO:
    fighter_external_id: str
    corner: str  # "RED" or "BLUE"
    outcome: Optional[str] = None  # "WIN", "LOSS", "DRAW", "NO_CONTEST", None (SCHEDULED)


# ── Ranking ────────────────────────────────────────────────────────────────────


@dataclass
class RankingDTO:
    provider: str
    fighter_external_id: str
    promotion_external_id: str
    category: str  # "pound-for-pound", "heavyweight", etc.
    rank: int
    trend: Optional[str] = None  # "UP", "DOWN", "STEADY"
    is_champion: bool = False
    weight_class_external_id: Optional[str] = None  # NULL for P4P


# ── Statistic ──────────────────────────────────────────────────────────────────


@dataclass
class StatisticDTO:
    fighter_external_id: str
    competition_external_id: str
    category: str  # "GENERAL", "STRIKING", "GRAPPLING"
    label: str
    value: float
    display_value: Optional[str] = None
