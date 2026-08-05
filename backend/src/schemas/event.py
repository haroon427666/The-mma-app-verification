"""Event + Fight Pydantic schemas."""

from datetime import datetime

from pydantic import BaseModel

# ── Event List Item ───────────────────────────────────────────────────────

class EventListItem(BaseModel):
    id: str
    name: str
    short_name: str | None = None
    date: datetime | None = None
    status: str
    promotion: str | None = None
    venue_name: str | None = None
    city: str | None = None
    country: str | None = None
    poster_url: str | None = None
    thumbnail_url: str | None = None
    fight_count: int = 0  # Number of fights on the card

    model_config = {"from_attributes": True}


# ── Broadcast ─────────────────────────────────────────────────────────────

class BroadcastResponse(BaseModel):
    network: str
    region: str | None = None
    broadcast_type: str = "TV"
    language: str | None = None


# ── Fight Detail (within event) ───────────────────────────────────────────

class FightListItem(BaseModel):
    id: str
    order: int
    card_segment: str | None = None
    status: str
    is_main_event: bool = False
    is_title_fight: bool = False
    weight_class: str | None = None

    # Fighters
    fighter_a_name: str | None = None
    fighter_a_id: str | None = None
    fighter_a_record: str | None = None
    fighter_b_name: str | None = None
    fighter_b_id: str | None = None
    fighter_b_record: str | None = None

    # Result (FINAL only)
    winner: str | None = None
    method: str | None = None
    round: int | None = None
    time: str | None = None

    model_config = {"from_attributes": True}


# ── Event Detail ──────────────────────────────────────────────────────────

class EventDetailResponse(BaseModel):
    id: str
    name: str
    short_name: str | None = None
    slug: str | None = None

    date: datetime | None = None
    time_local: str | None = None
    status: str
    season: str | None = None

    promotion: str | None = None
    promotion_id: str | None = None

    # Venue
    venue_name: str | None = None
    venue_id: str | None = None
    city: str | None = None
    country: str | None = None
    venue_capacity: int | None = None

    # Media
    poster_url: str | None = None
    banner_url: str | None = None
    thumbnail_url: str | None = None
    square_url: str | None = None

    # Content
    description: str | None = None
    fights: list[FightListItem] = []
    broadcasts: list[BroadcastResponse] = []
    spectators: int | None = None

    model_config = {"from_attributes": True}


# ── Event Statistics ───────────────────────────────────────────────────────

class EventStatisticsResponse(BaseModel):
    total_fights: int = 0
    title_fights: int = 0
    decisions: int = 0
    finishes: int = 0
    ko_tko: int = 0
    submissions: int = 0
    countries_represented: int = 0
    weight_classes: list[str] = []


# ── Fight Detail ──────────────────────────────────────────────────────────

class FighterCornerResponse(BaseModel):
    fighter_id: str
    name: str
    corner: str
    outcome: str | None = None
    record: str | None = None


class FightDetailResponse(BaseModel):
    id: str
    event_id: str
    event_name: str | None = None
    event_date: datetime | None = None
    order: int
    card_segment: str | None = None
    status: str
    is_main_event: bool = False
    is_title_fight: bool = False
    weight_class: str | None = None
    description: str | None = None  # "5 Rnd (5-5-5-5-5)"

    # Competitors
    fighters: list[FighterCornerResponse] = []

    # Result
    winner: str | None = None
    method: str | None = None
    method_detail: str | None = None
    round: int | None = None
    time: str | None = None

    # Broadcast
    broadcasts: list[BroadcastResponse] = []

    model_config = {"from_attributes": True}
