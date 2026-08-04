"""Fighter Pydantic schemas — API response models, never ORM.

These are what the frontend receives. Never expose SQLAlchemy objects.
"""

from datetime import date, datetime

from pydantic import BaseModel

# ── List Item (for /fighters listing) ───────────────────────────────────────

class FighterListItem(BaseModel):
    id: str
    first_name: str
    last_name: str
    full_name: str | None = None
    nickname: str | None = None
    weight_class: str | None = None
    record: str  # "21-5-0"
    record_wins: int
    record_losses: int
    record_draws: int
    nationality: str | None = None
    headshot_url: str | None = None
    is_active: bool
    stance: str | None = None
    fighting_style: str | None = None
    latest_rank: int | None = None
    latest_rank_category: str | None = None

    model_config = {"extra": "forbid"}


# ── Record ──────────────────────────────────────────────────────────────────

class FighterRecordResponse(BaseModel):
    wins: int = 0
    losses: int = 0
    draws: int = 0
    no_contests: int = 0
    ko_tko_wins: int = 0
    ko_tko_losses: int = 0
    submission_wins: int = 0
    submission_losses: int = 0
    title_wins: int = 0
    title_losses: int = 0
    title_draws: int = 0
    total_fights: int = 0
    win_percentage: float = 0.0
    finish_rate: float = 0.0
    record_summary: str | None = None


# ── Statistics ──────────────────────────────────────────────────────────────

class StatValue(BaseModel):
    label: str
    value: float
    display_value: str
    category: str


class FighterStatsResponse(BaseModel):
    # Striking
    sig_strikes_landed_per_min: float | None = None
    sig_strikes_accuracy: float | None = None
    sig_strikes_absorbed_per_min: float | None = None
    sig_strikes_defense: float | None = None
    # Grappling
    takedown_avg_per_15min: float | None = None
    takedown_accuracy: float | None = None
    takedown_defense: float | None = None
    submission_avg_per_15min: float | None = None
    # General
    knockdowns: float | None = None
    avg_fight_time_sec: float | None = None
    control_time_sec: float | None = None
    # Raw stats
    all_stats: list[StatValue] = []


# ── Ranking ─────────────────────────────────────────────────────────────────

class FighterRankingEntry(BaseModel):
    category_name: str
    rank: int
    trend: str | None = None
    is_champion: bool = False
    title_defenses: int | None = None


# ── Fight History ────────────────────────────────────────────────────────────

class FighterFightEntry(BaseModel):
    event_name: str
    event_date: date | None = None
    opponent_name: str | None = None
    opponent_id: str | None = None
    outcome: str | None = None
    method: str | None = None
    round: int | None = None
    time: str | None = None
    weight_class: str | None = None
    is_title_fight: bool = False


# ── Opponent ────────────────────────────────────────────────────────────────

class FighterOpponent(BaseModel):
    fighter_id: str
    name: str
    record: str | None = None
    headshot_url: str | None = None
    nationality: str | None = None
    fights: int = 0  # How many times they fought
    outcomes: list[str] = []  # ["WIN", "LOSS"]


# ── Media ───────────────────────────────────────────────────────────────────

class FighterMediaResponse(BaseModel):
    headshot_url: str | None = None
    cutout_url: str | None = None
    render_url: str | None = None
    cdn_url: str | None = None


# ── Profile (for /fighters/{id}) ────────────────────────────────────────────

class FighterProfileResponse(BaseModel):
    id: str
    first_name: str
    last_name: str
    full_name: str | None = None
    short_name: str | None = None
    nickname: str | None = None
    slug: str | None = None

    # Physical
    weight_kg: float | None = None
    height_cm: float | None = None
    reach_cm: float | None = None
    leg_reach_cm: float | None = None
    stance: str | None = None

    # Classification
    weight_class: str | None = None
    nationality: str | None = None
    birth_date: date | None = None
    birth_location: str | None = None
    age: int | None = None

    # Status
    is_active: bool
    debut_date: date | None = None

    # Career
    record: FighterRecordResponse | None = None
    statistics: FighterStatsResponse | None = None
    rankings: list[FighterRankingEntry] = []
    recent_fights: list[FighterFightEntry] = []
    upcoming_fight: FighterFightEntry | None = None

    # Background
    trains_at: str | None = None
    fighting_style: str | None = None
    biography: str | None = None

    # Media
    media: FighterMediaResponse | None = None

    # Social
    instagram_url: str | None = None
    twitter_url: str | None = None

    # Meta
    source_provider: str | None = None
    synced_at: datetime | None = None

    model_config = {"from_attributes": True}
