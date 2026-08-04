"""ESPN Ranking sync job."""

from typing import Any, cast

from src.sync.job import SyncJob
from src.sync.types import EntityType


class ESPN_RankingSyncJob(SyncJob):
    entity_type = EntityType.RANKING
    depends_on = [EntityType.PROMOTION, EntityType.FIGHTER, EntityType.WEIGHT_CLASS]
    critical = False
    batch_size = 100
    supports_incremental = False

    async def _fetch(self, ctx: Any, state: Any) -> list[Any]:
        provider = ctx.provider
        return cast(list[Any], await provider.fetch_rankings())

    async def _upsert(self, ctx: Any, dtos: list[Any]) -> dict[str, int]:
        from src.sync.upserts.id_resolver import IdResolver
        from src.sync.upserts.ranking import RankingUpsert

        resolver = IdResolver(ctx.db)
        upsert = RankingUpsert(resolver)
        result = await upsert.upsert_batch(dtos)
        await ctx.db.flush()
        return {"inserted": result.inserted, "updated": result.updated,
                "skipped": result.skipped, "errors": result.errors}
