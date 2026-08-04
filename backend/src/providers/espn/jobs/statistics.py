"""ESPN Statistic sync job.

Statistics are per-fighter career stats from /athletes/{id}/statistics.
Each stat is attached to the fighter's most recent competitor row
(if resolved; otherwise skipped with a warning).
"""

from typing import Any

from src.sync.job import SyncJob
from src.sync.types import EntityType


class ESPN_StatisticSyncJob(SyncJob):
    entity_type = EntityType.STATISTIC
    depends_on = [EntityType.FIGHTER, EntityType.COMPETITION]
    critical = False
    batch_size = 200
    supports_incremental = False

    async def _fetch(self, ctx: Any, state: Any) -> list[Any]:
        # Fetch fighter stats in batches — iterate fighters
        # For now, return empty — stats are fetched per-fighter during fighter sync
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
