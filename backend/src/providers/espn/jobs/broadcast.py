"""ESPN Broadcast sync job."""

from src.sync.job import SyncJob
from src.sync.types import EntityType


class ESPN_BroadcastSyncJob(SyncJob):
    entity_type = EntityType.BROADCAST
    depends_on = [EntityType.EVENT]
    critical = False
    batch_size = 50
    supports_incremental = False

    async def _fetch(self, ctx, state):
        provider = ctx.provider
        return await provider.fetch_broadcasts()

    async def _upsert(self, ctx, dtos):
        from src.sync.upserts.id_resolver import IdResolver
        from src.sync.upserts.broadcast import BroadcastUpsert

        resolver = IdResolver(ctx.db)
        upsert = BroadcastUpsert(resolver)
        result = await upsert.upsert_batch(dtos)
        await ctx.db.flush()
        return {"inserted": result.inserted, "updated": result.updated,
                "skipped": result.skipped, "errors": result.errors}
