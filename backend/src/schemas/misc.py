"""Ranking, Promotion, Venue Pydantic schemas."""

from datetime import datetime

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


# ── Champion ────────────────────────────────────────────────────────────────

class ChampionFighter(BaseModel):
    id: str
    full_name: str | None = None
    nickname: str | None = None
    headshot_url: str | None = None
    record: str | None = None  # "21-5-0"


class ChampionEntry(BaseModel):
    """A current champion (rankings row with is_champion=true) + fighter info."""

    category_name: str
    category_type: str | None = None
    gender: str | None = None
    weight_class: str | None = None
    rank: int = 1
    trend: str | None = None
    title_defenses: int | None = None
    fighter: ChampionFighter

    model_config = {"extra": "forbid"}


# ── Ranking extras ────────────────────────────────────────────────────────────

class FighterBrief(BaseModel):
    id: str
    full_name: str | None = None
    nickname: str | None = None
    record: str | None = None
    headshot_url: str | None = None
    wins: int = 0
    losses: int = 0
    draws: int = 0


class RankingMovementEntry(BaseModel):
    fighter: FighterBrief
    division: str
    from_rank: int | None = None
    to_rank: int
    change: int | None = None
    reason: str | None = None


class GOATEntry(BaseModel):
    rank: int
    fighter: FighterBrief
    composite_score: float
    title_defenses: int | None = None
    title_wins: int | None = None
    finish_rate: float | None = None
    divisions: list[str] = []
    era: str | None = None


class ProspectEntry(BaseModel):
    fighter: FighterBrief
    age: int | None = None
    finish_rate: float | None = None
    trajectory: str = "unknown"
    potential: float | None = None
    division: str
    comparable: str | None = None


class StreakEntry(BaseModel):
    fighter: FighterBrief
    streak: int
    type: str
    best_rank: int | None = None
    last_fight: str | None = None


class TitleDefenseEntry(BaseModel):
    fighter: FighterBrief
    defenses: int
    division: str


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


# ── Weight Class ─────────────────────────────────────────────────────────────

class WeightClassListItem(BaseModel):
    id: str
    name: str
    abbreviation: str | None = None
    gender: str | None = None
    fighter_count: int = 0

    model_config = {"from_attributes": True}


class WeightClassDetailResponse(BaseModel):
    id: str
    name: str
    abbreviation: str | None = None
    min_weight_kg: float | None = None
    max_weight_kg: float | None = None
    gender: str | None = None
    fighter_count: int = 0

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
