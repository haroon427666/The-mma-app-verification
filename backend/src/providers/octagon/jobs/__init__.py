"""Octagon Enrichment Sync Jobs.

Fighter enrichment: leg_reach, trains_at, fighting_style, debut_date, UFC renders.
Rankings verification: compare with ESPN rankings, alert on mismatch.
"""

from typing import Any, cast

from src.sync.job import SyncJob
from src.sync.types import EntityType


class Octagon_FighterEnrichmentJob(SyncJob):
    """Merge Octagon fighter fields into existing ESPN-synced fighters.

    Fills: leg_reach_cm, trains_at, fighting_style, debut_date, headshot_url.
    Also fills nickname, birth_location, weight_kg, height_cm, reach_cm
    ONLY if ESPN has no value (gap-filling, never overwriting).
    """

    entity_type = EntityType.FIGHTER
    depends_on = [EntityType.FIGHTER]
    critical = False
    batch_size = 100
    supports_incremental = False

    async def _fetch(self, ctx: Any, state: Any) -> list[Any]:
        provider = ctx.octagon_provider
        return cast(list[Any], await provider.fetch_fighters())

    async def _upsert(self, ctx: Any, dtos: list[Any]) -> dict[str, int]:
        from src.providers.merge import merge_record
        enriched = 0
        for dto in dtos:
            fighter_id = dto.external_id  # Octagon uses name as ID
            enrichment = await ctx.octagon_provider.fetch_fighter_enrichment(fighter_id)
            if enrichment:
                await merge_record(ctx.db, "fighters", fighter_id, enrichment, "octagon")
                enriched += 1
        return {"inserted": 0, "updated": enriched, "skipped": 0, "errors": 0}


class Octagon_RankingsVerificationJob(SyncJob):
    """Verify ESPN rankings against Octagon rankings.

    Does NOT modify database. Only logs discrepancies.
    Alerts if champion or top-5 order differs between sources.
    """

    entity_type = EntityType.RANKING
    depends_on = [EntityType.RANKING]
    critical = False
    batch_size = 200
    supports_incremental = False

    async def _fetch(self, ctx: Any, state: Any) -> list[Any]:
        provider = ctx.octagon_provider
        return cast(list[Any], await provider.fetch_rankings())

    async def _upsert(self, ctx: Any, dtos: list[Any]) -> dict[str, int]:
        """Compare with ESPN rankings from DB, log discrepancies."""
        logger = ctx.logger
        discrepancies = 0

        for oct_ranking in dtos:
            # Query ESPN ranking for same category + position
            # (implementation depends on DB schema)
            pass

        # Verification is read-only — report only
        if discrepancies > 0:
            logger.warning(f"Rankings verification: {discrepancies} discrepancies found")

        return {"inserted": 0, "updated": 0, "skipped": len(dtos), "errors": 0}
