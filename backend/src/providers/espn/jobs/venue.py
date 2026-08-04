"""ESPN Venue sync job."""

from typing import Any, cast

from src.sync.job import SyncJob
from src.sync.types import EntityType


class ESPN_VenueSyncJob(SyncJob):
    entity_type = EntityType.VENUE
    depends_on = []
    critical = False  # Venues embedded in events — non-critical standalone
    batch_size = 50
    supports_incremental = False

    async def _fetch(self, ctx: Any, state: Any) -> list[Any]:
        provider = ctx.provider
        return cast(list[Any], await provider.fetch_venues())

    async def _upsert(self, ctx: Any, dtos: list[Any]) -> dict[str, int]:
        from src.sync.upserts.id_resolver import IdResolver
        from src.sync.upserts.venue import VenueUpsert

        resolver = IdResolver(ctx.db)
        upsert = VenueUpsert(resolver)
        result = await upsert.upsert_batch(dtos)
        await ctx.db.flush()
        return {"inserted": result.inserted, "updated": result.updated,
                "skipped": result.skipped, "errors": result.errors}
