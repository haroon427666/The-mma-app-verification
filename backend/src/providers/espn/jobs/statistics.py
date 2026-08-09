"""ESPN Statistic sync job — career statistics.

Career stats come from /athletes/{id}/statistics (fighter-scoped; no
competition). The job:
1. Samples fighter external IDs from the DB (bounded: ESPN_STATS_MAX_FIGHTERS,
   default 200 — the research envelope is sustained 2–5 rps, so unbounded
   enumeration of 38k fighters in one run would exceed it).
2. Fetches each fighter's career statistics (bounded concurrency).
3. Produces StatisticDTOs with competition_external_id="" (career shape) —
   StatisticsUpsert persists them keyed by (fighter_id, category, label) with
   NULL competitor_id.

Per-fight statistics (competitors/{id}/statistics) are content-dependent and
handled during competition sync where ESPN provides them.

Missing stats are NEVER fabricated: athletes without statistics produce no
DTOs and no rows.
"""

import asyncio
import logging
import os
from typing import Any

from src.providers.dto import StatisticDTO
from src.sync.job import SyncJob
from src.sync.types import EntityType

logger = logging.getLogger(__name__)


def _max_fighters() -> int:
    try:
        return int(os.environ.get("ESPN_STATS_MAX_FIGHTERS", "200") or 200)
    except ValueError:
        return 200


class ESPN_StatisticSyncJob(SyncJob):
    entity_type = EntityType.STATISTIC
    depends_on = [EntityType.FIGHTER, EntityType.COMPETITION]
    critical = False
    batch_size = 100
    supports_incremental = False

    async def _fetch(self, ctx: Any, state: Any) -> list[Any]:
        provider = ctx.provider
        athlete_ids = await self._known_fighter_ids(ctx, _max_fighters())
        if not athlete_ids:
            logger.info("No fighters to fetch statistics for")
            return []

        sem = asyncio.Semaphore(provider._config.max_concurrency)

        async def fetch_stats(athlete_id: str) -> list[StatisticDTO]:
            async with sem:
                try:
                    result = await provider.fetch_fighter_statistics(athlete_id)
                    # Provider returns FighterStatistics; extract raw DTOs
                    dtos = getattr(result, "raw_dtos", None)
                    if dtos is None and isinstance(result, list):
                        dtos = result
                    if not dtos:
                        logger.debug(f"No statistics for fighter {athlete_id}")
                        return []
                    for dto in dtos:
                        dto.competition_external_id = ""  # career shape
                    return list(dtos)
                except Exception as e:
                    logger.warning(f"Statistics failed for {athlete_id}: {e}")
                    return []

        results = await asyncio.gather(*(fetch_stats(i) for i in athlete_ids))
        dtos: list[StatisticDTO] = [d for batch in results for d in batch]
        logger.info(
            f"Career statistics: {len(dtos)} stats across {len(athlete_ids)} fighters"
        )
        return dtos

    @staticmethod
    async def _known_fighter_ids(ctx: Any, limit: int) -> list[str]:
        """Sample fighter external IDs from the DB (bounded)."""
        from sqlalchemy import select

        from src.db.models.fighter import Fighter

        try:
            result = await ctx.db.execute(
                select(Fighter.external_id)
                .order_by(Fighter.id)
                .limit(limit)
            )
            return [str(row) for row in result.scalars().all()]
        except Exception as e:
            logger.warning(f"Fighter sampling failed: {e}")
            return []

    async def _upsert(self, ctx: Any, dtos: list[Any]) -> dict[str, int]:
        from src.sync.upserts.id_resolver import IdResolver
        from src.sync.upserts.statistics import StatisticsUpsert

        resolver = IdResolver(ctx.db)
        upsert = StatisticsUpsert(resolver)
        result = await upsert.upsert_batch(dtos)
        await ctx.db.flush()
        return {"inserted": result.inserted, "updated": result.updated,
                "skipped": result.skipped, "errors": result.errors}
