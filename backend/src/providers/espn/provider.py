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
from typing import TYPE_CHECKING, Any

import httpx

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
from src.providers.espn.client import ESPNClient
from src.providers.espn.config import ENDPOINTS, ESPNClientConfig, sync_league_slugs
from src.providers.espn.parsers.broadcast import parse_broadcast_list
from src.providers.espn.parsers.competition import (
    parse_competition,
    parse_competition_status,
)
from src.providers.espn.parsers.event import extract_competitions_from_event, parse_event
from src.providers.espn.parsers.fighter import parse_fighter
from src.providers.espn.parsers.promotion import parse_promotion
from src.providers.espn.parsers.ranking import parse_ranking_category
from src.providers.espn.reference import RefResolver, extract_id_from_ref
from src.sync.types import RecordFetchOutcome

if TYPE_CHECKING:
    from src.providers.espn.parsers.records import FighterRecord
    from src.providers.espn.parsers.statistics import FighterStatistics

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

    @staticmethod
    def _item_id(item: dict[str, Any]) -> str | None:
        """Extract an athlete ID from a list item (either $ref or inline id)."""
        if not isinstance(item, dict):
            return None
        if "$ref" in item:
            return extract_id_from_ref(str(item["$ref"]))
        raw_id = item.get("id")
        return str(raw_id) if raw_id is not None else None

    async def fetch_athlete_ids(
        self,
        league_slugs: list[str] | None = None,
        include_global: bool = True,
        limit: int = 1000,
    ) -> set[str]:
        """Discover the deduplicated ESPN athlete ID universe.

        Sources (research P0 discovery):
        1. Global flat listing: /athletes (~38,006 IDs) — never alone;
           hidden profiles are only reachable via other refs.
        2. League rosters: /leagues/{slug}/athletes for the configured set
           (default active majors; ESPN_SYNC_LEAGUES overrides).

        Returns a deduplicated set of ESPN athlete IDs (no profile resolution —
        this is the cheap enumeration pass; profiles are resolved separately
        with bounded concurrency). Resumable via SyncState checkpoint.
        """
        await self._ensure_started()

        slugs = league_slugs or list(sync_league_slugs())
        ids: set[str] = set()

        # 1. Global flat listing
        if include_global:
            try:
                async for page in self._client.paginate(
                    ENDPOINTS["global_athletes"],
                    params={"limit": limit},
                ):
                    for item in page.get("items", []):
                        item_id = self._item_id(item)
                        if item_id:
                            ids.add(item_id)
            except Exception as e:
                logger.error(f"Global athlete listing failed: {e}")

        # 2. League rosters
        for slug in slugs:
            try:
                async for page in self._client.paginate(
                    ENDPOINTS["athletes"].format(league_slug=slug),
                    params={"limit": limit},
                ):
                    for item in page.get("items", []):
                        item_id = self._item_id(item)
                        if item_id:
                            ids.add(item_id)
            except Exception as e:
                logger.warning(f"League roster failed ({slug}): {e}")

        logger.info(
            f"Athlete discovery: {len(ids)} unique IDs "
            f"(global={include_global}, leagues={slugs})"
        )
        return ids

    async def fetch_fighters(
        self,
        promotion_external_id: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[FighterDTO]:
        """League-scoped fighter fetch (backward-compatible single-league path)."""
        await self._ensure_started()

        league_slug = promotion_external_id or "ufc"
        path = ENDPOINTS["athletes"].format(league_slug=league_slug)
        params: dict[str, Any] = {"limit": limit, "page": offset // limit + 1}

        resolved = await self._resolve_paginated(path, params=params)
        fighters = [parse_fighter(item) for item in resolved]
        logger.info(f"Fetched {len(fighters)} fighters from ESPN ({league_slug})")
        return fighters

    async def fetch_fighters_by_ids(
        self,
        athlete_ids: list[str],
        max_concurrency: int | None = None,
    ) -> list[FighterDTO]:
        """Resolve athlete profiles by ESPN ID with bounded concurrency.

        The discovery ID set may include IDs not present on any listing
        (hidden profiles reachable only via ranking/event refs). Each ID is
        fetched exactly once (client response cache + in-flight dedup handle
        duplicates and parallel fan-out).
        """
        import asyncio

        await self._ensure_started()

        sem = asyncio.Semaphore(
            max_concurrency or self._config.max_concurrency
        )

        async def fetch_one(athlete_id: str) -> FighterDTO | None:
            async with sem:
                try:
                    data = await self._client.get_json(
                        ENDPOINTS["athlete"].format(athlete_id=athlete_id)
                    )
                    return parse_fighter(data)
                except Exception as e:
                    logger.warning(f"Athlete profile failed ({athlete_id}): {e}")
                    return None

        # Bound coroutine creation on large censuses (~38k IDs): gather in
        # chunks so the full ID set is never materialized as tasks at once.
        BATCH = 1000
        fighters: list[FighterDTO] = []
        for start in range(0, len(athlete_ids), BATCH):
            chunk = athlete_ids[start : start + BATCH]
            results = await asyncio.gather(*(fetch_one(i) for i in chunk))
            fighters.extend(f for f in results if f is not None)

        logger.info(
            f"Resolved {len(fighters)}/{len(athlete_ids)} athlete profiles "
            f"(concurrency={max_concurrency or self._config.max_concurrency})"
        )
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
        """Fetch fighter W/L/D/NC record from /athletes/{id}/records.

        Backward-compatible wrapper returning the simple W/L/D/NC dict.
        Prefer ``fetch_fighter_record`` for the full breakdown.
        """
        record = await self.fetch_fighter_record(external_id)
        if record is None:
            return {"wins": 0, "losses": 0, "draws": 0, "no_contests": 0}
        return {
            "wins": record.wins,
            "losses": record.losses,
            "draws": record.draws,
            "no_contests": record.no_contests,
        }

    async def fetch_fighter_record(self, external_id: str) -> "FighterRecord | None":
        """Fetch the full fighter record breakdown from /athletes/{id}/records.

        Returns None when the endpoint is unavailable/empty — callers must NOT
        reset stored records in that case (research GAP: records used to
        persist as 0-0-0-0 because the flow was never invoked).
        """
        record, _outcome, _status = await self.fetch_fighter_record_with_outcome(
            external_id
        )
        return record

    async def fetch_fighter_record_with_outcome(
        self, external_id: str
    ) -> tuple["FighterRecord | None", RecordFetchOutcome, int | None]:
        """Fetch the full record breakdown + tri-state outcome (Phase D).

        Returns (record, outcome, http_status):
        - AVAILABLE — a real payload was parsed (http_status 200);
        - EMPTY     — the provider served no usable payload: a 200 response
          with no record data, or a content-dependent 404 (NORMAL provider
          behavior — the client never retries 4xx and never trips the
          breaker for it);
        - FAILED    — a transient failure (429/5xx/network/breaker-open).

        Only EMPTY may ever become CONFIRMED_ABSENT; FAILED is retryable and
        is never absence evidence. Callers keep the existing None-on-unavailable
        semantics (records are never reset, never fabricated).
        """
        from src.providers.espn.parsers.records import parse_fighter_records as parse_full

        await self._ensure_started()
        try:
            data = await self._client.get_json(
                ENDPOINTS["athlete_records"].format(athlete_id=external_id)
            )
            record = parse_full(data)
            # A "real" record has a summary or counts; empty responses mean
            # unavailable (e.g. non-MMA or content-dependent athletes).
            if not record.record_summary and record.total_fights == 0:
                logger.debug(f"Records empty for fighter {external_id} — skipping")
                return None, RecordFetchOutcome.EMPTY, 200
            return record, RecordFetchOutcome.AVAILABLE, 200
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                # Content-dependent absence — same semantics as an empty 200.
                return None, RecordFetchOutcome.EMPTY, 404
            logger.warning(
                f"Failed to fetch records for fighter {external_id}: "
                f"HTTP {e.response.status_code}"
            )
            return None, RecordFetchOutcome.FAILED, e.response.status_code
        except Exception as e:
            logger.warning(f"Failed to fetch records for fighter {external_id}: {e}")
            return None, RecordFetchOutcome.FAILED, None

    async def fetch_fighter_statistics(
        self, fighter_external_id: str
    ) -> "FighterStatistics | list[StatisticDTO]":
        """Fetch career statistics from /athletes/{id}/statistics.

        Returns the parsed FighterStatistics (use .raw_dtos for storage);
        empty FighterStatistics when the endpoint is unavailable or the
        athlete has no stats (content-dependent — never fabricate).
        """
        from src.providers.espn.parsers.statistics import (
            parse_statistics as parse_stats,
        )

        await self._ensure_started()
        try:
            data = await self._client.get_json(
                ENDPOINTS["athlete_statistics"].format(athlete_id=fighter_external_id)
            )
            return parse_stats(data, fighter_external_id)
        except Exception as e:
            logger.warning(
                f"Failed to fetch statistics for fighter {fighter_external_id}: {e}"
            )
            from src.providers.espn.parsers.statistics import FighterStatistics

            return FighterStatistics(fighter_external_id=fighter_external_id)

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
        params: dict[str, Any] = {"limit": limit, "page": offset // limit + 1}

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

    # ── Historical event discovery (winningFight hooks) ────────────────────

    async def fetch_eventlog_hooks(
        self, athlete_ids: list[str] | None = None
    ) -> list[dict[str, Any]]:
        """Fetch athlete eventlogs (bounded) — returns raw eventlog payloads.

        Eventlog is CONTENT_DEPENDENT (P0): athletes without logged fights
        return empty/unavailable payloads; those are skipped. The caller
        (historical job) extracts event refs from each payload.

        Bounded by ESPN_EVENTLOG_MAX_FIGHTERS (default 50) to keep the
        request budget inside the research envelope.
        """
        import os

        await self._ensure_started()

        if athlete_ids is None:
            # Caller must supply IDs; without a DB hook we default to none.
            return []

        try:
            limit = int(os.environ.get("ESPN_EVENTLOG_MAX_FIGHTERS", "50") or 50)
        except ValueError:
            limit = 50
        try:
            max_pages = int(os.environ.get("ESPN_EVENTLOG_MAX_PAGES", "5") or 5)
        except ValueError:
            max_pages = 5

        ids = list(athlete_ids)[:limit]
        payloads: list[dict[str, Any]] = []

        for athlete_id in ids:
            try:
                # Eventlog is page-paginated (pageSize 25). Veterans with
                # long careers span multiple pages (live-verified: DJ has
                # 30 fights → 2 pages) — fetch them all (bounded by cap).
                merged: dict[str, Any] | None = None
                page = 1
                while page <= max_pages:
                    data = await self._client.get_json(
                        ENDPOINTS["athlete_eventlog"].format(athlete_id=athlete_id),
                        params={"page": page, "limit": 25},
                    )
                    events = data.get("events", {}) or {}
                    items = events.get("items", []) or []
                    if merged is None:
                        merged = data
                    else:
                        merged.setdefault("events", {}).setdefault("items", []).extend(items)
                    if not items:
                        break
                    page_count = 0
                    try:
                        page_count = int(events.get("pageCount") or 0)
                    except (TypeError, ValueError):
                        pass
                    if page_count and page >= page_count:
                        break
                    page += 1

                if merged and ((merged.get("events", {}) or {}).get("items", []) or []):
                    payloads.append(merged)
            except Exception as e:
                logger.warning(f"Eventlog failed for athlete {athlete_id}: {e}")

        logger.info(
            f"Eventlog hooks: {len(payloads)}/{len(ids)} athletes had logged fights"
        )
        return payloads

    async def fetch_winning_fight_refs(
        self, promotion_external_id: str
    ) -> list[str]:
        """Collect winningFight $refs from all ranking categories of a league.

        Research: every rank entry carries a winningFight ref pointing at the
        fighter's last competition (legacy 400/600-series event ids). This is
        THE historical-event discovery hook — /leagues/{slug}/events is
        upcoming-only and must never be used for history.
        """
        await self._ensure_started()
        assert self._resolver is not None

        from src.providers.espn.parsers.ranking import extract_winning_fight_refs

        refs: list[str] = []
        try:
            path = ENDPOINTS["rankings"].format(league_slug=promotion_external_id)
            categories_data = await self._client.get_json(path)
            category_refs = categories_data.get("items", [])

            resolved_categories = await self._resolver.resolve_all(category_refs)
            for cat_data in resolved_categories:
                refs.extend(extract_winning_fight_refs(cat_data))
        except Exception as e:
            logger.warning(
                f"WinningFight refs failed for {promotion_external_id}: {e}"
            )

        unique = sorted(set(refs))
        logger.info(
            f"WinningFight hooks for {promotion_external_id}: {len(unique)}"
        )
        return unique

    # ── Health ─────────────────────────────────────────────────────────────

    async def health_check(self) -> bool:
        if self._client._http is None:
            await self._client.start()
        return await self._client.health_check()

    async def close(self) -> None:
        if self._client._http is not None:
            await self._client.close()
