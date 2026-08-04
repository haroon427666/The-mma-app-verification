"""
BaseDataProvider Protocol.

Every data source (ESPN, Tapology, ONE Championship official API, etc.)
implements this Protocol. The sync engine and services interact with providers
ONLY through this interface — never through provider-specific classes.

Adding a new provider means:
1. Create a new package under providers/ (e.g. providers/tapology/)
2. Implement every method in this Protocol
3. Register it in ProviderRegistry with its promotion slug(s)
4. Done. Zero changes to sync engine, services, repositories, or API.

Each method returns a list of DTOs. The caller (sync engine) handles upsert logic.
"""

from typing import Protocol, runtime_checkable

from src.providers.dto import (
    BroadcastDTO,
    CompetitionDTO,
    EventDTO,
    FighterDTO,
    PromotionDTO,
    RankingDTO,
    StatisticDTO,
    VenueDTO,
    WeightClassDTO,
)


@runtime_checkable
class BaseDataProvider(Protocol):
    """Protocol that every data provider must implement."""

    # ── Provider metadata ──────────────────────────────────────────────────────

    @property
    def name(self) -> str:
        """Human-readable provider name, e.g. 'ESPN', 'Tapology'."""
        ...

    @property
    def provider_slug(self) -> str:
        """Machine identifier, e.g. 'espn', 'tapology'."""
        ...

    # ── Promotions (Organizations) ─────────────────────────────────────────────

    async def fetch_promotions(self) -> list[PromotionDTO]:
        """Fetch all known promotions/organizations from this provider."""
        ...

    async def fetch_promotion(self, external_id: str) -> PromotionDTO | None:
        """Fetch a single promotion by its provider-specific ID."""
        ...

    # ── Fighters ───────────────────────────────────────────────────────────────

    async def fetch_fighters(
        self, promotion_external_id: str | None = None, limit: int = 100, offset: int = 0
    ) -> list[FighterDTO]:
        """Fetch fighters, optionally scoped to a promotion."""
        ...

    async def fetch_fighter(self, external_id: str) -> FighterDTO | None:
        """Fetch a single fighter by provider ID."""
        ...

    async def fetch_fighter_statistics(
        self, fighter_external_id: str
    ) -> list[StatisticDTO]:
        """Fetch career statistics for a fighter."""
        ...

    # ── Weight Classes ─────────────────────────────────────────────────────────

    async def fetch_weight_classes(self) -> list[WeightClassDTO]:
        """Fetch all weight classes."""
        ...

    # ── Venues ─────────────────────────────────────────────────────────────────

    async def fetch_venues(self) -> list[VenueDTO]:
        """Fetch all venues (or those relevant to synced events)."""
        ...

    # ── Events ─────────────────────────────────────────────────────────────────

    async def fetch_events(
        self,
        promotion_external_id: str | None = None,
        status: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[EventDTO]:
        """Fetch events, optionally filtered by promotion and status."""
        ...

    async def fetch_event(self, external_id: str) -> EventDTO | None:
        """Fetch a single event with full detail."""
        ...

    # ── Competitions (Fights / Bouts) ──────────────────────────────────────────

    async def fetch_competitions(
        self, event_external_id: str
    ) -> list[CompetitionDTO]:
        """Fetch all competitions (fights) for an event, with competitors."""
        ...

    # ── Broadcasts ─────────────────────────────────────────────────────────────

    async def fetch_broadcasts(
        self, event_external_id: str
    ) -> list[BroadcastDTO]:
        """Fetch broadcast information for an event."""
        ...

    # ── Rankings ───────────────────────────────────────────────────────────────

    async def fetch_rankings(
        self,
        promotion_external_id: str,
        category: str | None = None,
    ) -> list[RankingDTO]:
        """Fetch rankings for a promotion, optionally filtered by category."""
        ...

    # ── Health ─────────────────────────────────────────────────────────────────

    async def health_check(self) -> bool:
        """Check if the provider's API is reachable. Returns True if healthy."""
        ...
