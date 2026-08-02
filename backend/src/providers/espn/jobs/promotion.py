"""ESPN Promotion sync job."""

from src.providers.dto import PromotionDTO
from src.sync.job import SyncJob
from src.sync.types import EntityType


class ESPN_PromotionSyncJob(SyncJob):
    entity_type = EntityType.PROMOTION
    depends_on = []
    critical = True
    batch_size = 25
    supports_incremental = False

    async def _fetch(self, ctx, state):
        provider = ctx.provider
        return await provider.fetch_promotions()

    async def _upsert(self, ctx, dtos):
        from src.sync.upserts.id_resolver import IdResolver
        from src.sync.upserts.promotion import PromotionUpsert

        resolver = IdResolver(ctx.db)
        upsert = PromotionUpsert(resolver)
        result = await upsert.upsert_batch(dtos)
        await ctx.db.flush()
        return {"inserted": result.inserted, "updated": result.updated,
                "skipped": result.skipped, "errors": result.errors}
