"""
ESPN Data Provider — VERIFIED against live API 2026-08-01.

Complete BaseDataProvider implementation using league-scoped URL patterns
and embedded competition data. All endpoints confirmed working.

Key architectural decisions:
- List endpoints return $ref URLs → resolved one-by-one via RefResolver (cached)
- Competitions are EMBEDDED in event responses → no separate competition fetch needed
- Fighter records are separate $ref → resolved in sync engine
- Weight classes extracted from inline data in athletes and competitions
- Venues extracted from embedded data in competitions
"""

import logging
from typing import Any

from src.providers.base import BaseDataProvider
from src.providers.dto import (
    BroadcastDTO,
    CompetitionDTO,
    FighterDTO,
    PromotionDTO,
    RankingDTO,
    StatisticDTO,
    VenueDTO,
    WeightClassDTO,
    EventDTO,
)
from src.providers.espn.client import ESPNClient
from src.providers.espn.config import ESPNClientConfig, ENDPOINTS
from src.providers.espn.reference import RefResolver
from src.providers.espn.parsers.promotion import parse_promotion
from src.providers.espn.parsers.fighter import parse_fighter, parse_fighter_records
from src.providers.espn.parsers.weight_class import parse_weight_class
from src.providers.espn.parsers.venue import parse_venue
from src.providers.espn.parsers.event import parse_event, extract_competitions_from_event
from src.providers.espn.parsers.competition import (
    parse_competition,
    parse_competition_status,
    extract_weight_class_from_comp,
)
from src.providers.espn.parsers.ranking import parse_ranking_category
from src.providers.espn.parsers.broadcast import parse_broadcast_list
from src.providers.espn.parsers.statistics import parse_statistics

logger = logging.getLogger(__name__)


class ESPNProvider:
    """ESPN API data provider implementing BaseDataProvider."""

    def __init__(self, config: ESPNClientConfig | None = None) -> None:
        self._config = config or ESPNClientConfig()
        self._client = ESPNClient(config=self._config)
        self._resolver: RefResolver | None = None

    @property
    def name(self) -> str:
        return "ESPN"

    @property
    def provider_slug(self) -> str:
        return "espn"

    async def _ensure_started(self) -> None:
        if self._client._http is None:
            await self._client.start()
        if self._resolver is None:
            self._resolver = RefResolver(self._client)

    # ── Shared helper: resolve paginated $ref list ─────────────────────────

    async def _resolve_paginated(
        self, path: str, params: dict[str, Any] | None = None, limit: int | None = None
    ) -> list[dict[str, Any]]:
        """Fetch all items from a paginated $ref list endpoint.

        Each page returns items as $ref URLs. We resolve each one.
        Results are cached within the sync run via RefResolver.
        """
        assert self._resolver is not None
        all_items: list[dict[str, Any]] = []

        async for page in self._client.paginate(path, params=params, limit=limit):
            items = page.get("items", [])
            resolved = await self._resolver.resolve_all(items)
            all_items.extend(resolved)

        return all_items

    # ── Promotions ─────────────────────────────────────────────────────────

    async def fetch_promotions(self) -> list[PromotionDTO]:
        await self._ensure_started()
        resolved = await self._resolve_paginated(ENDPOINTS["leagues"])
        promotions = [parse_promotion(item) for item in resolved]
        logger.info(f"Fetched {len(promotions)} promotions from ESPN")
        return promotions

    async def fetch_promotion(self, external_id: str) -> PromotionDTO | None:
        """Fetch by league slug (e.g. 'ufc'), not numeric ID."""
        await self._ensure_started()
        try:
            data = await self._client.get_json(
                ENDPOINTS["league"].format(league_slug=external_id)
            )
            return parse_promotion(data)
        except Exception as e:
            logger.error(f"Failed to fetch ESPN promotion {external_id}: {e}")
            return None

    # ── Fighters ───────────────────────────────────────────────────────────

    async def fetch_fighters(
        self,
        promotion_external_id: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[FighterDTO]:
        await self._ensure_started()

        league_slug = promotion_external_id or "ufc"
        path = ENDPOINTS["athletes"].format(league_slug=league_slug)
        params: dict[str, Any] = {"limit": limit, "offset": offset}

        resolved = await self._resolve_paginated(path, params=params)
        fighters = [parse_fighter(item) for item in resolved]
        logger.info(f"Fetched {len(fighters)} fighters from ESPN ({league_slug})")
        return fighters

    async def fetch_fighter(self, external_id: str) -> FighterDTO | None:
        await self._ensure_started()
        try:
            data = await self._client.get_json(
                ENDPOINTS["athlete"].format(athlete_id=external_id)
            )
            return parse_fighter(data)
        except Exception as e:
            logger.error(f"Failed to fetch ESPN fighter {external_id}: {e}")
            return None

    async def fetch_fighter_records(self, external_id: str) -> dict[str, int]:
        """Fetch fighter W/L/D/NC record from /athletes/{id}/records."""
        await self._ensure_started()
        try:
            data = await self._client.get_json(
                ENDPOINTS["athlete_records"].format(athlete_id=external_id)
            )
            return parse_fighter_records(data)
        except Exception as e:
            logger.error(f"Failed to fetch records for fighter {external_id}: {e}")
            return {"wins": 0, "losses": 0, "draws": 0, "no_contests": 0}

    async def fetch_fighter_statistics(
        self, fighter_external_id: str
    ) -> list[StatisticDTO]:
        await self._ensure_started()
        try:
            data = await self._client.get_json(
                ENDPOINTS["athlete_statistics"].format(athlete_id=fighter_external_id)
            )
            return parse_statistics(data, fighter_external_id)
        except Exception as e:
            logger.error(f"Failed to fetch statistics for fighter {fighter_external_id}: {e}")
            return []

    # ── Weight Classes ─────────────────────────────────────────────────────

    async def fetch_weight_classes(self) -> list[WeightClassDTO]:
        """Weight classes are extracted from inline data in athlete/competition responses.

        This method returns an empty list — the sync engine collects weight classes
        from parsed competition and athlete data during event/fighter sync.
        """
        logger.info("Weight classes extracted from inline data; no dedicated endpoint")
        return []

    # ── Venues ─────────────────────────────────────────────────────────────

    async def fetch_venues(self) -> list[VenueDTO]:
        """Venues are extracted from embedded data in competition responses.

        This method returns an empty list — the sync engine collects venues
        from parsed competition data during event sync.
        """
        logger.info("Venues extracted from embedded competition data; no bulk endpoint")
        return []

    # ── Events ─────────────────────────────────────────────────────────────

    async def fetch_events(
        self,
        promotion_external_id: str | None = None,
        status: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[EventDTO]:
        await self._ensure_started()

        league_slug = promotion_external_id or "ufc"
        path = ENDPOINTS["events"].format(league_slug=league_slug)
        params: dict[str, Any] = {"limit": limit, "offset": offset}

        resolved = await self._resolve_paginated(path, params=params)
        events = [parse_event(item) for item in resolved]

        if status:
            events = [e for e in events if e.status == status]

        logger.info(f"Fetched {len(events)} events from ESPN ({league_slug})")
        return events

    async def fetch_event(self, external_id: str, league_slug: str = "ufc") -> EventDTO | None:
        await self._ensure_started()
        try:
            data = await self._client.get_json(
                ENDPOINTS["event"].format(league_slug=league_slug, event_id=external_id)
            )
            return parse_event(data)
        except Exception as e:
            logger.error(f"Failed to fetch ESPN event {external_id}: {e}")
            return None

    # ── Competitions (EMBEDDED in event, not fetched separately) ────────────

    async def fetch_competitions(
        self, event_external_id: str, league_slug: str = "ufc"
    ) -> list[CompetitionDTO]:
        """Fetch competitions from an event.

        Competitions are EMBEDDED in the event resource — we fetch the event
        and extract the competitions array. This is a single HTTP call, not N+1.

        For FINAL events, we also resolve competition status to get result details.
        """
        await self._ensure_started()

        try:
            event_data = await self._client.get_json(
                ENDPOINTS["event"].format(league_slug=league_slug, event_id=event_external_id)
            )

            comps_raw = extract_competitions_from_event(event_data)
            competitions: list[CompetitionDTO] = []

            for comp_raw in comps_raw:
                if not isinstance(comp_raw, dict):
                    continue

                comp_dto = parse_competition(
                    comp_raw,
                    event_external_id=event_external_id,
                    league_slug=league_slug,
                )

                # For FINAL events, resolve competition status for result details
                if comp_dto.status == "FINAL":
                    try:
                        status_data = await self._client.get_json(
                            ENDPOINTS["competition_status"].format(
                                league_slug=league_slug,
                                event_id=event_external_id,
                                competition_id=comp_dto.external_id,
                            )
                        )
                        comp_dto = parse_competition_status(status_data, comp_dto)
                    except Exception:
                        # Status resolution is best-effort for results
                        pass

                competitions.append(comp_dto)

            logger.info(
                f"Fetched {len(competitions)} competitions for event {event_external_id}"
            )
            return competitions

        except Exception as e:
            logger.error(f"Failed to fetch competitions for event {event_external_id}: {e}")
            return []

    # ── Broadcasts ─────────────────────────────────────────────────────────

    async def fetch_broadcasts(
        self, event_external_id: str, league_slug: str = "ufc"
    ) -> list[BroadcastDTO]:
        """Fetch broadcast info for all competitions in an event.

        Broadcasts are at the competition level. We fetch from each competition
        and deduplicate at the event level.
        """
        await self._ensure_started()

        broadcasts: list[BroadcastDTO] = []
        seen: set[tuple[str, str]] = set()

        try:
            event_data = await self._client.get_json(
                ENDPOINTS["event"].format(league_slug=league_slug, event_id=event_external_id)
            )
            comps_raw = extract_competitions_from_event(event_data)

            for comp_raw in comps_raw:
                if not isinstance(comp_raw, dict):
                    continue
                comp_id = str(comp_raw.get("id", ""))
                if not comp_id:
                    continue

                try:
                    data = await self._client.get_json(
                        ENDPOINTS["competition_broadcasts"].format(
                            league_slug=league_slug,
                            event_id=event_external_id,
                            competition_id=comp_id,
                        )
                    )
                    comp_broadcasts = parse_broadcast_list(data, event_external_id)
                    for b in comp_broadcasts:
                        key = (b.network, b.region or "")
                        if key not in seen:
                            seen.add(key)
                            broadcasts.append(b)
                except Exception:
                    continue

            logger.info(f"Fetched {len(broadcasts)} unique broadcasts for event {event_external_id}")
            return broadcasts

        except Exception as e:
            logger.error(f"Failed to fetch broadcasts for event {event_external_id}: {e}")
            return []

    # ── Rankings ───────────────────────────────────────────────────────────

    async def fetch_rankings(
        self,
        promotion_external_id: str,
        category: str | None = None,
    ) -> list[RankingDTO]:
        await self._ensure_started()
        assert self._resolver is not None

        try:
            path = ENDPOINTS["rankings"].format(league_slug=promotion_external_id)

            # Get ranking categories as $ref URLs
            categories_data = await self._client.get_json(path)
            category_refs = categories_data.get("items", [])

            # If filtering by category, find the matching $ref
            if category:
                category_refs = [
                    ref for ref in category_refs
                    if isinstance(ref, dict)
                    and category.lower() in (ref.get("$ref", "") or "").lower()
                ]

            # Resolve all categories
            resolved_categories = await self._resolver.resolve_all(category_refs)

            rankings: list[RankingDTO] = []
            for cat_data in resolved_categories:
                rankings.extend(parse_ranking_category(cat_data, promotion_external_id))

            logger.info(
                f"Fetched {len(rankings)} rankings for promotion {promotion_external_id}"
            )
            return rankings

        except Exception as e:
            logger.error(f"Failed to fetch rankings for {promotion_external_id}: {e}")
            return []

    # ── Health ─────────────────────────────────────────────────────────────

    async def health_check(self) -> bool:
        if self._client._http is None:
            await self._client.start()
        return await self._client.health_check()

    async def close(self) -> None:
        if self._client._http is not None:
            await self._client.close()
