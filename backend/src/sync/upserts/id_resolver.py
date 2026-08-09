"""
ExternalId resolver — maps provider:external_id pairs to internal entity UUIDs.

Every upsert service uses this to:
1. Look up existing entities: (provider="espn", external_id="3332412") → fighter UUID
2. Create mappings: insert into external_ids when a new entity is created
3. Bulk resolve: resolve many external IDs in a single query (avoids N+1)

This is the key to idempotent upsert: we always look up by external_id first.
"""

import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


# ── In-memory cache ───────────────────────────────────────────────────────────
# Per-upsert-run cache to avoid repeated DB hits for the same external_id lookup.
# Cleared between sync runs. Not shared across processes (safe for horizontal scaling).


class IdResolver:
    """Resolves provider external IDs to internal entity UUIDs.

    CACHE LIFECYCLE: The in-memory cache exists for ONE upsert batch.
    Created fresh per SyncPipeline execution. Never shared across runs.
    No global state, no TTL — cleared explicitly via clear() between runs.
    This guarantees cache freshness: every sync run starts with an empty cache.

    Usage:
        resolver = IdResolver(db_session)
        fighter_id = await resolver.resolve("espn", "3332412", "fighter")
        if fighter_id is None:
            # New fighter — create and register
            fighter = Fighter(id=uuid4(), ...)
            db.add(fighter)
            await resolver.register("espn", "3332412", "fighter", fighter.id)
    """

    def __init__(self, db: AsyncSession) -> None:
        self._db = db
        self._cache: dict[tuple[str, str, str], str | None] = {}
        # Cache key: (provider, external_id, entity_type) → internal UUID string or None

    # ── Single ID resolution ───────────────────────────────────────────────

    async def resolve(
        self,
        provider: str,
        external_id: str,
        entity_type: str,
    ) -> str | None:
        """Resolve a single external ID to an internal entity UUID (string).

        Returns None if no mapping exists (entity needs to be created).
        """
        cache_key = (provider, external_id, entity_type)
        if cache_key in self._cache:
            return self._cache[cache_key]

        try:
            # Direct SQL to avoid circular imports (repositories not built yet)
            result = await self._db.execute(
                select(ExternalId.entity_id).where(
                    ExternalId.provider == provider,
                    ExternalId.external_id == external_id,
                    ExternalId.entity_type == entity_type,
                )
            )
            row = result.scalar_one_or_none()
            entity_uuid = str(row) if row else None
            self._cache[cache_key] = entity_uuid
            return entity_uuid
        except Exception as e:
            logger.error(f"Failed to resolve external ID: {provider}/{external_id}/{entity_type}: {e}")
            return None

    # ── Bulk resolution ─────────────────────────────────────────────────────

    async def resolve_bulk(
        self,
        provider: str,
        entity_type: str,
        external_ids: list[str],
    ) -> dict[str, str]:
        """Resolve many external IDs in a single query.

        Args:
            provider: "espn"
            entity_type: "fighter", "event", etc.
            external_ids: List of provider-specific IDs.

        Returns:
            dict mapping external_id → internal entity UUID (string). Missing
            IDs are not included.
        """
        result_map: dict[str, str] = {}
        uncached: list[str] = []

        # Check cache first
        for eid in external_ids:
            cache_key = (provider, eid, entity_type)
            if cache_key in self._cache:
                cached = self._cache[cache_key]
                if cached is not None:
                    result_map[eid] = cached
            else:
                uncached.append(eid)

        if not uncached:
            return result_map

        # Single query for all uncached IDs
        try:
            result = await self._db.execute(
                select(ExternalId.external_id, ExternalId.entity_id).where(
                    ExternalId.provider == provider,
                    ExternalId.entity_type == entity_type,
                    ExternalId.external_id.in_(uncached),
                )
            )
            for row in result:
                eid = str(row.external_id)
                uuid_val = str(row.entity_id)
                result_map[eid] = uuid_val
                self._cache[(provider, eid, entity_type)] = uuid_val

            # Cache misses (IDs not found)
            for eid in uncached:
                if eid not in result_map:
                    self._cache[(provider, eid, entity_type)] = None

        except Exception as e:
            logger.error(f"Bulk resolve failed for {entity_type}: {e}")

        return result_map

    # ── Registration ────────────────────────────────────────────────────────

    async def register(
        self,
        provider: str,
        external_id: str,
        entity_type: str,
        entity_uuid: str,
    ) -> None:
        """Create an external_id mapping for a newly created entity."""
        try:
            mapping = ExternalId(
                provider=provider,
                external_id=external_id,
                entity_type=entity_type,
                entity_id=entity_uuid,
            )
            self._db.add(mapping)
            self._cache[(provider, external_id, entity_type)] = entity_uuid
        except Exception as e:
            logger.error(f"Failed to register external ID: {e}")

    async def flush(self) -> None:
        """Flush pending external_id inserts to the database."""
        try:
            await self._db.flush()
        except Exception:
            pass  # Let the caller handle commit/rollback

    # ── Cache management ────────────────────────────────────────────────────

    def clear(self) -> None:
        """Clear the in-memory cache. Call between sync runs."""
        self._cache.clear()

    @property
    def cache_size(self) -> int:
        return len(self._cache)


# ── Late import to avoid circular dependency ──────────────────────────────────
# ExternalId model lives in db.models.support — imported at module bottom
# to avoid circular imports with the repository / ORM layer.

from src.db.models.support import ExternalId
