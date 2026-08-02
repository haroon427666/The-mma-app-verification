"""ESPN Event sync job.

Events are fetched from /leagues/{league}/events.
Competitions are EMBEDDED in the event response — no separate fetch needed.
"""

from src.sync.job import SyncJob
from src.sync.types import EntityType


class ESPN_EventSyncJob(SyncJob):
    entity_type = EntityType.EVENT
    depends_on = [EntityType.PROMOTION, EntityType.VENUE]
    critical = True
    batch_size = 25
    supports_incremental = False

    async def _fetch(self, ctx, state):
        provider = ctx.provider
        offset = state.last_offset if state.last_offset else 0
        events = await provider.fetch_events(limit=self.batch_size, offset=offset)
        return events

    async def _upsert(self, ctx, dtos):
        from src.sync.upserts.id_resolver import IdResolver
        from src.sync.upserts.event import EventUpsert

        resolver = IdResolver(ctx.db)
        upsert = EventUpsert(resolver)
        result = await upsert.upsert_batch(dtos)
        await ctx.db.flush()
        return {"inserted": result.inserted, "updated": result.updated,
                "skipped": result.skipped, "errors": result.errors}
