"""ESPN Competition sync job.

Competitions are EMBEDDED in event responses. This job:
1. Fetches events from the provider
2. Extracts competitions from each event
3. Upserts competitions and their nested competitors

Competitors reference fighters via external_id → resolved by IdResolver.
"""

from src.providers.dto import CompetitionDTO
from src.sync.job import SyncJob
from src.sync.types import EntityType


class ESPN_CompetitionSyncJob(SyncJob):
    entity_type = EntityType.COMPETITION
    depends_on = [EntityType.EVENT, EntityType.FIGHTER, EntityType.WEIGHT_CLASS]
    critical = True
    batch_size = 50
    supports_incremental = False

    async def _fetch(self, ctx, state):
        """Fetch competitions from events embedded data.

        For each event, fetch the full event detail (which includes
        competitions[] inline). The provider handles this.
        """
        provider = ctx.provider
        offset = state.last_offset if state.last_offset else 0

        # Fetch events first (to get event IDs), then competitions from each
        events = await provider.fetch_events(limit=25, offset=offset)
        competitions: list[CompetitionDTO] = []

        for event in events:
            comps = await provider.fetch_competitions(event.external_id)
            competitions.extend(comps)

        return competitions

    async def _upsert(self, ctx, dtos):
        from src.sync.upserts.id_resolver import IdResolver
        from src.sync.upserts.competition import CompetitionUpsert

        resolver = IdResolver(ctx.db)
        upsert = CompetitionUpsert(resolver)
        result = await upsert.upsert_batch(dtos)
        await ctx.db.flush()
        return {"inserted": result.inserted, "updated": result.updated,
                "skipped": result.skipped, "errors": result.errors}
