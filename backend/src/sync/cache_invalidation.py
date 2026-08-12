"""Cache invalidation on sync completion — bust what the sync just changed.

Cache-aside needs a write-through invalidation path: when a sync run touches
an entity type, the API cache entries derived from it must be discarded so
the next read is fresh. The sync engine fires an ``after_sync`` event; this
module subscribes to it and invalidates the matching ``mma:api:*`` prefixes.

Design notes:
- Entity → cache prefix map is explicit and lives here; adding a newly cached
  endpoint means adding one entry (or nothing if it maps to an existing one).
- Invalidation is best-effort and never blocks or fails the sync pipeline:
  both CacheManager backends swallow backend errors (degrade to serve-through).
- Only COMPLETED / PARTIAL runs bust caches; FAILED/CANCELLED runs leave
  previously cached data intact (stale-but-consistent beats empty).
"""

import logging
from typing import Any

from src.api.cache import API_CACHE_PREFIX
from src.middleware.cache import default_cache
from src.sync.types import EntityType, SyncStatus

logger = logging.getLogger(__name__)

# Entity type → API cache key segment(s). Keep in sync with src/api/cache.py.
# Competitions and broadcasts roll up into event detail, so they bust the same
# prefix as events. Statistic rows surface inside fighter/competition detail,
# so they bust both.
_ENTITY_CACHE_SEGMENTS: dict[EntityType, tuple[str, ...]] = {
    EntityType.FIGHTER: ("fighters",),
    # Records backfill writes fighter_records + record-fetch status rows, both
    # of which surface in the fighters:detail profile (Phase D D5) — bust the
    # same prefix as fighter syncs.
    EntityType.RECORDS: ("fighters",),
    EntityType.STATISTIC: ("fighters", "events"),
    EntityType.EVENT: ("events",),
    EntityType.COMPETITION: ("events",),
    EntityType.BROADCAST: ("events",),
    EntityType.RANKING: ("rankings",),
    EntityType.PROMOTION: ("promotions",),
    EntityType.VENUE: ("venues",),
    EntityType.WEIGHT_CLASS: ("weight-classes",),
}


def _prefixes_for(entity_type: str) -> set[str]:
    try:
        entity = EntityType(entity_type)
    except ValueError:
        logger.debug(f"Unknown entity type in cache invalidation: {entity_type}")
        return set()
    segments = _ENTITY_CACHE_SEGMENTS.get(entity)
    if not segments:
        return set()
    return {f"{API_CACHE_PREFIX}{segment}" for segment in segments}


async def invalidate_after_sync(event_ctx: Any, result: Any) -> None:
    """After-sync hook: bust API caches for entities written during the run.

    Args:
        event_ctx: SyncEventCtx (unused — kept for the handler signature).
        result: SyncResult — drives which prefixes get invalidated.
    """
    if result.overall_status not in (SyncStatus.COMPLETED, SyncStatus.PARTIAL):
        return

    prefixes: set[str] = set()
    for job_result in result.job_results:
        if job_result.status.value == "COMPLETED":
            prefixes |= _prefixes_for(job_result.entity_type)

    if not prefixes:
        return

    cache = default_cache()
    for prefix in sorted(prefixes):
        try:
            removed = await cache.invalidate(prefix)
            logger.info(
                f"Cache invalidated after sync run {result.run_id}: "
                f"prefix='{prefix}' removed={removed}"
            )
        except Exception:
            logger.warning(
                f"Cache invalidation failed after sync run {result.run_id} "
                f"(prefix='{prefix}') — serving stale data until TTL expiry",
                exc_info=True,
            )
