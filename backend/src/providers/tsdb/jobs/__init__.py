"""TheSportsDB Enrichment Sync Jobs.

These jobs do NOT create new records. They only UPDATE existing records
with enrichment fields (media, bios, social links) that ESPN doesn't provide.

They depend on the ESPN sync having completed first.
"""

from src.sync.job import SyncJob
from src.sync.types import EntityType


class TSDB_PromotionEnrichmentJob(SyncJob):
    """Merge TSDB media + social + description into existing promotions."""

    entity_type = EntityType.PROMOTION
    depends_on = []  # Runs independently after ESPN promotion sync
    critical = False
    batch_size = 25
    supports_incremental = False

    async def _fetch(self, ctx, state):
        provider = ctx.tsdb_provider
        return await provider.fetch_promotions()

    async def _upsert(self, ctx, dtos):
        """MERGE only enrichment fields. Never overwrite ESPN fields."""
        from src.sync.upserts.id_resolver import IdResolver
        resolver = IdResolver(ctx.db)
        enriched = 0
        for dto in dtos:
            try:
                internal_id = await resolver.resolve_external(
                    EntityType.PROMOTION, dto.external_id, "tsdb"
                )
                if not internal_id:
                    # No matching ESPN promotion — skip
                    continue
                enrichment = await ctx.tsdb_provider.fetch_promotion_enrichment(dto.external_id)
                if enrichment:
                    await self._merge_enrichment(ctx.db, internal_id, enrichment)
                    enriched += 1
            except Exception:
                continue
        return {"inserted": 0, "updated": enriched, "skipped": 0, "errors": 0}

    async def _merge_enrichment(self, db, internal_id: str, enrichment: dict):
        """UPDATE only TSDB-owned fields on the promotion record."""
        # Uses the merge logic from merge.py
        from src.providers.merge import merge_record
        await merge_record(db, "promotions", internal_id, enrichment, "tsdb")


class TSDB_EventEnrichmentJob(SyncJob):
    """Merge TSDB event media + descriptions into existing events."""

    entity_type = EntityType.EVENT
    depends_on = [EntityType.EVENT]
    critical = False
    batch_size = 25
    supports_incremental = False

    async def _fetch(self, ctx, state):
        provider = ctx.tsdb_provider
        return await provider.fetch_events()

    async def _upsert(self, ctx, dtos):
        from src.providers.merge import merge_record
        enriched = 0
        for dto in dtos:
            enrichment = await ctx.tsdb_provider.fetch_event_enrichment(dto.external_id)
            if enrichment:
                await merge_record(ctx.db, "events", dto.external_id, enrichment, "tsdb")
                enriched += 1
        return {"inserted": 0, "updated": enriched, "skipped": 0, "errors": 0}


class TSDB_FighterEnrichmentJob(SyncJob):
    """Merge TSDB fighter bios + cutout/render images into existing fighters."""

    entity_type = EntityType.FIGHTER
    depends_on = [EntityType.FIGHTER]
    critical = False
    batch_size = 100
    supports_incremental = False

    async def _fetch(self, ctx, state):
        provider = ctx.tsdb_provider
        return await provider.fetch_fighters()

    async def _upsert(self, ctx, dtos):
        from src.providers.merge import merge_record
        enriched = 0
        for dto in dtos:
            enrichment = await ctx.tsdb_provider.fetch_fighter_enrichment(dto.external_id)
            if enrichment:
                await merge_record(ctx.db, "fighters", dto.external_id, enrichment, "tsdb")
                enriched += 1
        return {"inserted": 0, "updated": enriched, "skipped": 0, "errors": 0}
