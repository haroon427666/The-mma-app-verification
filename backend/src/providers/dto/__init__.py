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

# ── Promotion ──────────────────────────────────────────────────────────────────


@dataclass
class PromotionDTO:
    provider: str  # "espn", "tapology", etc.
    external_id: str
    name: str
    slug: str
    country: str | None = None
    logo_url: str | None = None
    season_year: int | None = None


# ── Fighter ────────────────────────────────────────────────────────────────────


@dataclass
class FighterDTO:
    provider: str
    external_id: str
    first_name: str
    last_name: str
    nickname: str | None = None
    short_name: str | None = None
    record_wins: int = 0
    record_losses: int = 0
    record_draws: int = 0
    record_no_contests: int = 0
    height_cm: float | None = None
    weight_kg: float | None = None
    reach_cm: float | None = None
    stance: str | None = None
    nationality: str | None = None
    birth_location: str | None = None
    birth_date: datetime | None = None
    headshot_url: str | None = None
    is_active: bool = True
    weight_class_external_id: str | None = None  # resolved later by sync engine


# ── Weight Class ───────────────────────────────────────────────────────────────


@dataclass
class WeightClassDTO:
    provider: str
    external_id: str
    name: str
    abbreviation: str
    min_weight_kg: float | None = None
    max_weight_kg: float | None = None
    gender: str | None = None


# ── Venue ──────────────────────────────────────────────────────────────────────


@dataclass
class VenueDTO:
    provider: str
    external_id: str
    name: str
    city: str | None = None
    state: str | None = None
    country: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    capacity: int | None = None


# ── Event ──────────────────────────────────────────────────────────────────────


@dataclass
class EventDTO:
    provider: str
    external_id: str
    name: str
    short_name: str | None = None
    date: datetime | None = None
    status: str = "SCHEDULED"  # SCHEDULED, FINAL, CANCELLED
    season: str | None = None
    slug: str | None = None
    promotion_external_id: str | None = None
    venue_external_id: str | None = None


# ── Broadcast ──────────────────────────────────────────────────────────────────


@dataclass
class BroadcastDTO:
    provider: str
    event_external_id: str
    network: str
    region: str | None = None
    language: str | None = None
    broadcast_type: str = "TV"  # TV, STREAMING, PPV


# ── Competition (Fight / Bout) ─────────────────────────────────────────────────


@dataclass
class CompetitionDTO:
    provider: str
    external_id: str
    event_external_id: str
    order_num: int = 0
    card_segment: str | None = None  # "main-card", "prelims", "early-prelims"
    status: str = "SCHEDULED"
    is_main_event: bool = False
    is_title_fight: bool = False
    weight_class_external_id: str | None = None
    result_method: str | None = None
    result_detail: str | None = None
    result_round: int | None = None
    result_time: str | None = None
    competitors: list["CompetitorDTO"] = field(default_factory=list)


# ── Competitor ─────────────────────────────────────────────────────────────────


@dataclass
class CompetitorDTO:
    fighter_external_id: str
    corner: str  # "RED" or "BLUE"
    outcome: str | None = None  # "WIN", "LOSS", "DRAW", "NO_CONTEST", None (SCHEDULED)


# ── Ranking ────────────────────────────────────────────────────────────────────


@dataclass
class RankingDTO:
    provider: str
    fighter_external_id: str
    promotion_external_id: str
    category: str  # "pound-for-pound", "heavyweight", etc.
    rank: int
    trend: str | None = None  # "UP", "DOWN", "STEADY"
    is_champion: bool = False
    weight_class_external_id: str | None = None  # NULL for P4P


# ── Statistic ──────────────────────────────────────────────────────────────────


@dataclass
class StatisticDTO:
    fighter_external_id: str
    competition_external_id: str
    category: str  # "GENERAL", "STRIKING", "GRAPPLING"
    label: str
    value: float
    display_value: str | None = None
