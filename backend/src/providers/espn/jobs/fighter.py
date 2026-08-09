"""ESPN Fighter sync job — discovery-driven.

Discovery sources (frozen research P0): global flat listing (/athletes) +
configured league rosters (/leagues/{slug}/athletes), deduplicated by ESPN
athlete ID. Hidden profiles (DJ/Rousey/Gracie/Ngannou...) that are absent from
listings are reached via ranking/event refs in the historical job; the fighter
job resolves every discovered ID exactly once (client cache + in-flight dedup).

Records (/athletes/{id}/records) are fetched per fighter with bounded
concurrency and persisted to the fighter_records table via FighterUpsert.
A missing/empty records response NEVER resets stored values.

Resumable: the discovered ID set is cached in SyncState.checkpoint; progress
is tracked via the pipeline's per-batch offset. A failed run resumes from the
last upserted batch; successful runs are idempotent.
"""

import asyncio
import logging
import os
from typing import Any, cast

from src.providers.dto import FighterDTO
from src.sync.job import SyncJob
from src.sync.types import EntityType

logger = logging.getLogger(__name__)


def _sync_limit() -> int:
    """Bounded per-run discovery window (ESPN_FIGHTER_SYNC_LIMIT, default 0 = all)."""
    try:
        return int(os.environ.get("ESPN_FIGHTER_SYNC_LIMIT", "0") or 0)
    except ValueError:
        return 0


class ESPN_FighterSyncJob(SyncJob):
    entity_type = EntityType.FIGHTER
    depends_on = [EntityType.WEIGHT_CLASS]
    critical = True
    batch_size = 100
    supports_incremental = False  # ESPN doesn't support modifiedSince for athletes

    async def _fetch(self, ctx: Any, state: Any) -> list[Any]:
        provider = ctx.provider

        # 1. Discover the athlete ID universe once — cached in checkpoint so a
        #    re-run never re-enumerates listings (research: resumable discovery).
        ids: list[str] = list(state.checkpoint.get("athlete_ids") or [])
        if not ids:
            discovered = await provider.fetch_athlete_ids()
            ids = sorted(discovered)
            state.checkpoint["athlete_ids"] = ids
            logger.info(f"Fighter discovery: {len(ids)} unique athlete IDs")

        # 2. Window: resume from last upserted offset, bounded per run
        limit = _sync_limit()
        start = state.last_offset or 0
        window = ids[start:] if not limit else ids[start : start + limit]
        if not window:
            logger.info("Fighter discovery window exhausted — nothing to fetch")
            return []

        # 3. Resolve profiles with bounded concurrency
        fighters = await provider.fetch_fighters_by_ids(window)

        # 4. Attach records (bounded concurrency, best-effort)
        fighters = await self._attach_records(provider, fighters)

        logger.info(
            f"Fighter window: {len(fighters)} resolved "
            f"(ids {start}-{start + len(window)} of {len(ids)})"
        )
        return cast(list[Any], fighters)

    async def _attach_records(
        self, provider: Any, fighters: list[FighterDTO]
    ) -> list[FighterDTO]:
        """Fetch each fighter's /athletes/{id}/records with bounded concurrency.

        Never resets stored records: fetch_fighter_record returns None for
        empty/unavailable payloads and the DTO keeps None fields, which
        FighterUpsert skips.
        """
        if not fighters:
            return fighters

        sem = asyncio.Semaphore(provider._config.max_concurrency)

        async def attach(dto: FighterDTO) -> None:
            async with sem:
                record = await provider.fetch_fighter_record(dto.external_id)
                if record is None:
                    return
                dto.record_summary = record.record_summary
                dto.ko_tko_wins = record.ko_tko_wins
                dto.ko_tko_losses = record.ko_tko_losses
                dto.submission_wins = record.submission_wins
                dto.submission_losses = record.submission_losses
                dto.title_wins = record.title_wins
                dto.title_losses = record.title_losses
                dto.title_draws = record.title_draws
                dto.total_fights = record.total_fights
                dto.win_percentage = record.win_percentage
                dto.finish_rate = record.finish_rate
                dto.record_wins = record.wins
                dto.record_losses = record.losses
                dto.record_draws = record.draws
                dto.record_no_contests = record.no_contests

        await asyncio.gather(*(attach(f) for f in fighters))
        return fighters

    async def _upsert(self, ctx: Any, dtos: list[Any]) -> dict[str, int]:
        from src.sync.upserts.fighter import FighterUpsert
        from src.sync.upserts.id_resolver import IdResolver

        resolver = IdResolver(ctx.db)
        upsert = FighterUpsert(resolver)
        result = await upsert.upsert_batch(dtos)
        await ctx.db.flush()
        return {"inserted": result.inserted, "updated": result.updated,
                "skipped": result.skipped, "errors": result.errors}
