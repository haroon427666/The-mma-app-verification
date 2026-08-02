"""Ranking, Promotion, Venue Pydantic schemas."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel


# ── Ranking ────────────────────────────────────────────────────────────────

class RankingEntry(BaseModel):
    rank: int
    fighter_id: str
    fighter_name: str
    fighter_nickname: str | None = None
    record: str | None = None
    trend: str | None = None
    is_champion: bool = False
    title_defenses: int | None = None
    headshot_url: str | None = None


class RankingCategory(BaseModel):
    category_name: str
    category_type: str | None = None
    gender: str | None = None
    weight_class: str | None = None
    champion: RankingEntry | None = None
    rankings: list[RankingEntry] = []


class RankingsResponse(BaseModel):
    categories: list[RankingCategory] = []
    synced_at: datetime | None = None


# ── Promotion ──────────────────────────────────────────────────────────────

class PromotionListItem(BaseModel):
    id: str
    name: str
    abbreviation: str | None = None
    slug: str | None = None
    country: str | None = None
    founded_year: int | None = None
    logo_url: str | None = None
    fighter_count: int = 0
    event_count: int = 0
    current_season: int | None = None

    model_config = {"from_attributes": True}


class PromotionDetailResponse(BaseModel):
    id: str
    name: str
    abbreviation: str | None = None
    short_name: str | None = None
    slug: str | None = None
    country: str | None = None
    founded_year: int | None = None
    first_event_date: str | None = None
    gender: str | None = None
    current_season: int | None = None

    # Branding
    logo_url: str | None = None
    badge_url: str | None = None
    banner_url: str | None = None
    poster_url: str | None = None

    # Content
    description: str | None = None
    tv_rights: str | None = None

    # Links
    website: str | None = None
    facebook_url: str | None = None
    instagram_url: str | None = None
    twitter_url: str | None = None

    # Stats
    fighter_count: int = 0
    event_count: int = 0
    ranking_categories: int = 0

    model_config = {"from_attributes": True}


# ── Venue ──────────────────────────────────────────────────────────────────

class VenueListItem(BaseModel):
    id: str
    name: str
    city: str | None = None
    country: str | None = None
    capacity: int | None = None
    event_count: int = 0

    model_config = {"from_attributes": True}


class VenueDetailResponse(BaseModel):
    id: str
    name: str
    city: str | None = None
    state: str | None = None
    country: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    capacity: int | None = None
    indoor: bool | None = None
    event_count: int = 0
    last_event_date: datetime | None = None

    model_config = {"from_attributes": True}


# ── Search ─────────────────────────────────────────────────────────────────

class SearchResultItem(BaseModel):
    id: str
    type: str  # fighter, event, venue, promotion
    name: str
    subtitle: str | None = None
    image_url: str | None = None
    relevance: float = 1.0


class SearchResponse(BaseModel):
    query: str
    total: int
    results: list[SearchResultItem] = []
