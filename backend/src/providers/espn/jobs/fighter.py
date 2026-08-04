"""ESPN Fighter sync job.

Fighters are fetched from /leagues/{league}/athletes.
Each fighter's record is resolved from /athletes/{id}/records.
Weight class inline data is extracted by the parser.
"""

from typing import Any, cast

from src.sync.job import SyncJob
from src.sync.types import EntityType


class ESPN_FighterSyncJob(SyncJob):
    entity_type = EntityType.FIGHTER
    depends_on = [EntityType.WEIGHT_CLASS]
    critical = True
    batch_size = 100
    supports_incremental = False  # ESPN doesn't support modifiedSince for athletes

    async def _fetch(self, ctx: Any, state: Any) -> list[Any]:
        provider = ctx.provider
        offset = state.last_offset if state.last_offset else 0
        fighters = await provider.fetch_fighters(limit=self.batch_size, offset=offset)
        return cast(list[Any], fighters)

    async def _upsert(self, ctx: Any, dtos: list[Any]) -> dict[str, int]:
        from src.sync.upserts.fighter import FighterUpsert
        from src.sync.upserts.id_resolver import IdResolver

        resolver = IdResolver(ctx.db)
        upsert = FighterUpsert(resolver)
        result = await upsert.upsert_batch(dtos)
        await ctx.db.flush()
        return {"inserted": result.inserted, "updated": result.updated,
                "skipped": result.skipped, "errors": result.errors}
