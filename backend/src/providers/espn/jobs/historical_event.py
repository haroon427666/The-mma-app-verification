"""ESPN Historical Event sync job — the historical-event discovery chain.

Research (frozen, authoritative): /leagues/{slug}/events is UPCOMING-ONLY
(count=1 for every league). Historical events are reached via:

    rankings → ranks[].winningFight $ref (competition ref)
            → event_id + competition_id + league extracted from the ref URL
            → fetch /events/{event_id} (embedded competitions)
            → competitions → competitors → athletes

    and (config-gated) athlete eventlogs:
            athletes/{id}/eventlog → items[].event $ref → events/{id}

Each ref carries its own league slug (ufc, bellator, mvp, k1...) — the job
uses it instead of assuming "ufc".

This job:
1. Collects winningFight refs from every configured league's rankings
   (+ eventlog refs when ESPN_EVENTLOG_ENABLED=1).
2. Extracts (league, event_id) from each ref, deduplicated.
3. Fetches each historical event detail (EventDTO) + its competitions
   (CompetitionDTO with nested CompetitorDTOs) under the ref's league.
4. Upserts events and competitions through the existing EventUpsert /
   CompetitionUpsert (idempotent — no duplicates, no overwrite of newer data).

Bounded: ESPN_MAX_HISTORICAL_EVENTS caps events per run (default 200);
ESPN_HISTORICAL_EVENTS=1 is required to enable the chain at all.
"""

import asyncio
import logging
import os
from typing import Any

from src.providers.dto import CompetitionDTO, EventDTO
from src.providers.espn.config import sync_league_slugs
from src.providers.espn.parsers.eventlog import parse_eventlog_refs
from src.providers.espn.parsers.ranking import parse_winning_fight_ref
from src.sync.job import SyncJob
from src.sync.types import EntityType

logger = logging.getLogger(__name__)


def _enabled() -> bool:
    return os.environ.get("ESPN_HISTORICAL_EVENTS", "1") == "1"


def _eventlog_enabled() -> bool:
    return os.environ.get("ESPN_EVENTLOG_ENABLED", "0") == "1"


def _max_events() -> int:
    try:
        return int(os.environ.get("ESPN_MAX_HISTORICAL_EVENTS", "200") or 200)
    except ValueError:
        return 200


def _max_eventlog_fighters() -> int:
    try:
        return int(os.environ.get("ESPN_EVENTLOG_MAX_FIGHTERS", "50") or 50)
    except ValueError:
        return 50


class ESPN_HistoricalEventSyncJob(SyncJob):
    entity_type = EntityType.HISTORICAL_EVENT
    depends_on = [
        EntityType.RANKING,
        EntityType.FIGHTER,
        EntityType.PROMOTION,
        EntityType.VENUE,
        EntityType.WEIGHT_CLASS,
    ]
    critical = False
    batch_size = 25
    supports_incremental = False

    async def _fetch(self, ctx: Any, state: Any) -> list[Any]:
        if not _enabled():
            logger.info("Historical event discovery disabled (ESPN_HISTORICAL_EVENTS=0)")
            return []

        provider = ctx.provider

        # 1. Collect (league, event_id) hooks — deduplicated by ESPN event ID.
        #    ESPN event IDs live in a shared numeric namespace, and the SAME
        #    historical event is referenced under multiple league scopes
        #    (live-verified: Bellator events appear in both ufc- and
        #    bellator-scoped winningFight refs). Keying by league:event fetched
        #    each event once per scope AND made promotion attribution
        #    non-deterministic (last-upsert-wins). Keying by event_id fetches
        #    each event exactly once; the FIRST ref's scope wins (deterministic).
        hooks: dict[str, dict[str, str]] = {}  # event_id → {"league", "event_id"}

        # 1a. Rankings winningFight refs (THE historical hook)
        for league in sync_league_slugs():
            for ref in await provider.fetch_winning_fight_refs(league):
                parsed = parse_winning_fight_ref(ref)
                if parsed is None:
                    continue
                event_id = parsed["event_id"]
                if event_id not in hooks:
                    hooks[event_id] = {
                        "league": parsed["league"],
                        "event_id": event_id,
                    }

        # 1b. Athlete eventlogs (config-gated breadth; content-dependent)
        if _eventlog_enabled():
            athlete_ids = await self._known_fighter_ids(ctx)
            if athlete_ids:
                for payload in await provider.fetch_eventlog_hooks(athlete_ids):
                    for entry in parse_eventlog_refs(payload):
                        event_id = entry["event_id"]
                        if event_id not in hooks:
                            hooks[event_id] = {
                                "league": entry["league"],
                                "event_id": event_id,
                            }

        max_events = _max_events()
        hooks_list = list(hooks.values())[:max_events]
        if not hooks_list:
            logger.info("No historical hooks resolved to events")
            return []

        logger.info(f"Historical discovery: {len(hooks_list)} events (cap {max_events})")

        # 2. Fetch events + competitions under each hook's league slug
        sem = asyncio.Semaphore(provider._config.max_concurrency)

        async def fetch_hook(hook: dict[str, str]) -> tuple[EventDTO | None, list[CompetitionDTO]]:
            league = hook["league"]
            event_id = hook["event_id"]
            async with sem:
                try:
                    event = await provider.fetch_event(event_id, league_slug=league)
                    comps = await provider.fetch_competitions(event_id, league_slug=league)
                    return event, comps
                except Exception as e:
                    logger.warning(f"Historical event {league}/{event_id} failed: {e}")
                    return None, []

        results = await asyncio.gather(*(fetch_hook(h) for h in hooks_list))

        dtos: list[Any] = []
        fetched = 0
        for event, comps in results:
            if event is not None:
                dtos.append(event)
                fetched += 1
            dtos.extend(comps)

        logger.info(
            f"Historical discovery: {fetched} events, "
            f"{len(dtos) - fetched} competitions"
        )
        return dtos

    @staticmethod
    async def _known_fighter_ids(ctx: Any) -> list[str]:
        """Sample fighter external IDs from the DB for eventlog breadth."""
        from sqlalchemy import select

        from src.db.models.fighter import Fighter

        try:
            result = await ctx.db.execute(
                select(Fighter.external_id)
                .order_by(Fighter.id)
                .limit(_max_eventlog_fighters())
            )
            return [str(row) for row in result.scalars().all()]
        except Exception as e:
            logger.warning(f"Eventlog fighter sampling failed: {e}")
            return []

    async def _upsert(self, ctx: Any, dtos: list[Any]) -> dict[str, int]:
        from src.sync.upserts.competition import CompetitionUpsert
        from src.sync.upserts.event import EventUpsert
        from src.sync.upserts.id_resolver import IdResolver

        resolver = IdResolver(ctx.db)
        event_dtos = [d for d in dtos if isinstance(d, EventDTO)]
        comp_dtos = [d for d in dtos if isinstance(d, CompetitionDTO)]

        result = {"inserted": 0, "updated": 0, "skipped": 0, "errors": 0}

        if event_dtos:
            event_upsert = EventUpsert(resolver)
            r = await event_upsert.upsert_batch(event_dtos)
            for k in result:
                result[k] += getattr(r, k)
            await ctx.db.flush()

        if comp_dtos:
            comp_upsert = CompetitionUpsert(resolver)
            r = await comp_upsert.upsert_batch(comp_dtos)
            for k in result:
                result[k] += getattr(r, k)
            await ctx.db.flush()

        return result
