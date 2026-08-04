"""ESPN Weight Class sync job."""

from typing import Any, cast

from src.sync.job import SyncJob
from src.sync.types import EntityType


class ESPN_WeightClassSyncJob(SyncJob):
    entity_type = EntityType.WEIGHT_CLASS
    depends_on = []
    critical = False  # Extracted inline — non-critical standalone
    batch_size = 20
    supports_incremental = False

    async def _fetch(self, ctx: Any, state: Any) -> list[Any]:
        provider = ctx.provider
        return cast(list[Any], await provider.fetch_weight_classes())

    async def _upsert(self, ctx: Any, dtos: list[Any]) -> dict[str, int]:
        from src.sync.upserts.id_resolver import IdResolver
        from src.sync.upserts.weight_class import WeightClassUpsert

        resolver = IdResolver(ctx.db)
        upsert = WeightClassUpsert(resolver)
        result = await upsert.upsert_batch(dtos)
        await ctx.db.flush()
        return {"inserted": result.inserted, "updated": result.updated,
                "skipped": result.skipped, "errors": result.errors}
