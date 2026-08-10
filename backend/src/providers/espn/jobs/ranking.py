"""ESPN Ranking sync job — per-promotion rankings + athlete injection.

Rankings reference fighters via athlete $refs. When a referenced fighter is
not yet synced (research: only ~18 of 150 ranked fighters were synced because
the census window had not reached them), RankingUpsert would skip the entry —
leaving the rankings table incomplete. This job injects the missing fighters
into the normal pipeline BEFORE the ranking upsert:

- Real refs only (no fake IDs, no speculative athlete creation).
- Bounded by ESPN_RANKING_INJECTION_LIMIT (default 25, 0 = disabled) — deep
  backfills are the fighter window's job, not the ranking run's.
- Idempotent: resolve_bulk skips already-synced fighters; FighterUpsert is
  keyed by (provider, external_id); registry inserts are ON CONFLICT DO NOTHING.
- Injected fighters are fully synced (profile + records) and marked consumed
  in the discovery registry (source='rankings') so the fighter window never
  re-fetches them.
"""

import logging
import os
from typing import Any

from src.sync.job import SyncJob
from src.sync.types import EntityType

logger = logging.getLogger(__name__)


def _injection_limit() -> int:
    """Max missing ranked fighters injected per run (0 = disabled)."""
    try:
        return int(os.environ.get("ESPN_RANKING_INJECTION_LIMIT", "25") or 25)
    except ValueError:
        return 25


class ESPN_RankingSyncJob(SyncJob):
    entity_type = EntityType.RANKING
    depends_on = [EntityType.PROMOTION, EntityType.FIGHTER, EntityType.WEIGHT_CLASS]
    critical = False
    batch_size = 100
    supports_incremental = False

    async def _fetch(self, ctx: Any, state: Any) -> list[Any]:
        provider = ctx.provider
        # fetch_rankings is per-promotion (league slug) — fetch for every
        # synced promotion so UFC/PFL/Bellator rankings all land.
        promotions = await provider.fetch_promotions()
        rankings: list[Any] = []
        for promo in promotions:
            rankings.extend(await provider.fetch_rankings(promo.external_id))

        await self._inject_missing_fighters(ctx, rankings)

        return rankings

    async def _inject_missing_fighters(self, ctx: Any, rankings: list[Any]) -> None:
        """Fetch + upsert ranked fighters that are not yet in the DB.

        Runs before the ranking upsert so the SAME run's RankingUpsert can
        resolve every injected fighter.
        """
        limit = _injection_limit()
        if limit <= 0 or not rankings:
            return

        referenced = sorted(
            {r.fighter_external_id for r in rankings if r.fighter_external_id}
        )
        if not referenced:
            return

        from src.sync.upserts.id_resolver import IdResolver

        resolver = IdResolver(ctx.db)
        known = await resolver.resolve_bulk("espn", "fighter", referenced)
        missing = [eid for eid in referenced if eid not in known]
        if not missing:
            logger.info(
                f"Ranking injection: all {len(referenced)} ranked fighters "
                f"already synced — nothing to inject"
            )
            return

        missing = missing[:limit]
        logger.info(
            f"Ranking injection: {len(missing)} unsynced ranked fighters "
            f"(of {len(referenced)} referenced, limit={limit})"
        )

        provider = ctx.provider
        from src.providers.espn.jobs.fighter import attach_records

        fighters = await provider.fetch_fighters_by_ids(missing)
        if not fighters:
            logger.warning("Ranking injection: no profiles resolved")
            return
        fighters = await attach_records(provider, fighters)

        from src.sync.upserts.fighter import FighterUpsert

        upsert = FighterUpsert(resolver)
        result = await upsert.upsert_batch(fighters)
        await ctx.db.flush()

        # Registry bookkeeping: fully synced (profile + records) → consumed so
        # the fighter window never re-fetches them. Covers both new registry
        # rows (inserted consumed) and rows the listing walk already queued
        # (marked consumed in place).
        from src.providers.espn.discovery import DiscoveryService

        service = DiscoveryService(session=ctx.db)
        injected = [f.external_id for f in fighters]
        if injected:
            await service.register_ids(
                injected, source="rankings", consumed=True, run_id=ctx.run_id
            )
            consumed = await service.mark_consumed(injected)
            logger.info(
                f"Ranking injection: upserted {result.inserted} new, "
                f"{result.updated} updated; {consumed} ids marked consumed "
                f"(source='rankings')"
            )

    async def _upsert(self, ctx: Any, dtos: list[Any]) -> dict[str, int]:
        from src.sync.upserts.id_resolver import IdResolver
        from src.sync.upserts.ranking import RankingUpsert

        resolver = IdResolver(ctx.db)
        upsert = RankingUpsert(resolver)
        result = await upsert.upsert_batch(dtos)
        await ctx.db.flush()
        return {"inserted": result.inserted, "updated": result.updated,
                "skipped": result.skipped, "errors": result.errors}
