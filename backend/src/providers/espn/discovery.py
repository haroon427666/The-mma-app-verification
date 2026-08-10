"""Discovery service — resumable athlete-ID census + deduplicated registry.

Research problem: the flat listing (~38k IDs) was re-enumerated from page 1 on
every fighter run, and progress lived only in the in-memory SyncState. This
module makes discovery durable and resumable:

- Registry (sync_discovered_athletes): ONE deduplicated row per athlete ID.
  Every discovery surface converges here — global listing walk, roster walks,
  ranking injection, competition/eventlog competitor refs.
- Per-source walk checkpoints (sync_discovery_checkpoints): a COMPLETED source
  is never re-walked (unless ESPN_DISCOVERY_FORCE=1); an interrupted walk
  resumes from the next page. Every page is committed before the next request.
- The fighter window = next N unconsumed registry IDs (ascending, bounded by
  ESPN_FIGHTER_SYNC_LIMIT). Consumed flags are crash-proof: only successfully
  upserted IDs are consumed, and content-dependent 404s are consumed once
  (never retried — matching the records "never reset" rule).

Compatibility: provider.fetch_athlete_ids() is untouched (still used by tests);
the walk covers the same two sources (global listing + configured league
rosters) with the same ordering.
"""

import logging
from dataclasses import dataclass
from typing import Any

from sqlalchemy import select, update
from sqlalchemy.dialects import postgresql, sqlite

from src.providers.espn.config import ENDPOINTS, sync_league_slugs
from src.sync.checkpoints import (
    DiscoveryCheckpoint,
    DiscoveryCheckpointManager,
)

logger = logging.getLogger(__name__)

PROVIDER = "espn"
GLOBAL_SOURCE = "global_listing"
ROSTER_SOURCE = "roster"
PAGE_SIZE = 1000


@dataclass
class WalkSummary:
    """Outcome of walking one discovery source."""

    source: str
    league_slug: str
    started_page: int
    discovered: int
    inserted: int
    completed: bool
    skipped: bool = False  # True when the source was already COMPLETED


class DiscoveryService:
    """Resumable census + registry for athlete-ID discovery.

    Usage (inside a job's _fetch):
        service = DiscoveryService(provider, ctx.db)
        await service.ensure_enumerated(run_id=ctx.run_id)
        window = await service.next_window(limit=ESPN_FIGHTER_SYNC_LIMIT)

    The provider is only needed for the walk; registry queries (window,
    register, consume) work with a session alone.
    """

    def __init__(self, session: Any, provider: Any = None) -> None:
        self._db = session
        self._provider = provider
        self._manager = DiscoveryCheckpointManager(session)

    # ── Sources ───────────────────────────────────────────────────────────

    def sources(self) -> list[tuple[str, str]]:
        """(source, league_slug) pairs — '' league = the global listing."""
        sources: list[tuple[str, str]] = [(GLOBAL_SOURCE, "")]
        for slug in sync_league_slugs():
            sources.append((ROSTER_SOURCE, slug))
        return sources

    # ── Resumable enumeration ─────────────────────────────────────────────

    async def ensure_enumerated(
        self,
        run_id: str | None = None,
        force: bool = False,
    ) -> list[WalkSummary]:
        """Walk every discovery source, resuming completed/interrupted walks.

        COMPLETED sources are skipped (no repeated prefix scanning) unless
        ``force`` (ESPN_DISCOVERY_FORCE=1). Interrupted sources resume from the
        next unprocessed page. Per-source failures are logged and do not
        abort the remaining sources (mirrors fetch_athlete_ids behavior).
        """
        summaries: list[WalkSummary] = []
        for source, league_slug in self.sources():
            try:
                summaries.append(
                    await self._walk_source(source, league_slug, run_id, force)
                )
            except Exception as e:
                logger.warning(
                    f"Discovery walk failed ({source}/{league_slug or 'global'}): {e}"
                )
                summaries.append(
                    WalkSummary(
                        source=source,
                        league_slug=league_slug,
                        started_page=0,
                        discovered=0,
                        inserted=0,
                        completed=False,
                    )
                )
        return summaries

    async def _walk_source(
        self, source: str, league_slug: str, run_id: str | None, force: bool
    ) -> WalkSummary:
        if self._provider is None:
            raise RuntimeError("DiscoveryService requires a provider for the walk")

        checkpoint = await self._manager.load(PROVIDER, source, league_slug)
        if checkpoint is not None and checkpoint.completed and not force:
            logger.info(
                f"Discovery {source}/{league_slug or 'global'}: already completed "
                f"({checkpoint.discovered_count} ids) — skipping"
            )
            return WalkSummary(
                source=source,
                league_slug=league_slug,
                started_page=checkpoint.page,
                discovered=checkpoint.discovered_count,
                inserted=0,
                completed=True,
                skipped=True,
            )

        start_page = checkpoint.page + 1 if checkpoint else 1
        discovered = checkpoint.discovered_count if checkpoint else 0

        if source == GLOBAL_SOURCE:
            path = ENDPOINTS["global_athletes"]
        else:
            path = ENDPOINTS["athletes"].format(league_slug=league_slug)

        page = start_page
        inserted_total = 0
        last_id: str | None = None
        pages = 0

        async for data in self._client.paginate(
            path,
            params={"limit": PAGE_SIZE},
            start_page=start_page,
        ):
            ids = [i for i in (self._item_id(item) for item in data.get("items", [])) if i]
            if ids:
                inserted_total += await self.register_ids(
                    ids, source=source, run_id=run_id
                )
                discovered += len(ids)
                last_id = ids[-1]
            pages += 1
            await self._manager.save(
                DiscoveryCheckpoint(
                    provider=PROVIDER,
                    source=source,
                    league_slug=league_slug,
                    page=page,
                    offset=discovered,
                    discovered_count=discovered,
                    last_athlete_id=last_id,
                    status="IN_PROGRESS",
                    run_id=run_id,
                )
            )
            await self._db.commit()
            page += 1

        await self._manager.save(
            DiscoveryCheckpoint(
                provider=PROVIDER,
                source=source,
                league_slug=league_slug,
                page=max(start_page, page - 1),
                offset=discovered,
                discovered_count=discovered,
                last_athlete_id=last_id,
                status="COMPLETED",
                completed=True,
                run_id=run_id,
            )
        )
        await self._db.commit()

        logger.info(
            f"Discovery {source}/{league_slug or 'global'}: completed — "
            f"{discovered} ids ({inserted_total} new), pages {start_page}-{page - 1}"
        )
        return WalkSummary(
            source=source,
            league_slug=league_slug,
            started_page=start_page,
            discovered=discovered,
            inserted=inserted_total,
            completed=True,
        )

    @staticmethod
    def _item_id(item: Any) -> str | None:
        """Extract an athlete ID from a list item ($ref or inline id)."""
        if not isinstance(item, dict):
            return None
        from src.providers.espn.reference import extract_id_from_ref

        if "$ref" in item:
            return extract_id_from_ref(str(item["$ref"]))
        raw_id = item.get("id")
        return str(raw_id) if raw_id is not None else None

    @property
    def _client(self) -> Any:
        return self._provider._client

    # ── Registry ──────────────────────────────────────────────────────────

    async def register_ids(
        self,
        external_ids: list[str],
        source: str,
        consumed: bool = False,
        run_id: str | None = None,
    ) -> int:
        """Insert athlete IDs into the registry (idempotent, first source wins).

        Does NOT commit — callers control transaction boundaries.
        """
        if not external_ids:
            return 0
        from src.db.models.support import SyncDiscoveredAthlete

        values = [
            {
                "provider": PROVIDER,
                "external_id": eid,
                "source": source,
                "consumed": consumed,
                "run_id": run_id,
            }
            for eid in external_ids
        ]
        stmt = self._insert(SyncDiscoveredAthlete).values(values)
        result = await self._db.execute(stmt)
        return int(result.rowcount or 0)

    async def next_window(self, limit: int | None = None) -> list[str]:
        """Next N unconsumed athlete IDs (ascending — same order as before).

        Late arrivals from relationship surfaces are always selected: the
        window is a FILTER on unconsumed ids, not an offset cursor.
        """
        from src.db.models.support import SyncDiscoveredAthlete

        stmt = (
            select(SyncDiscoveredAthlete.external_id)
            .where(
                SyncDiscoveredAthlete.provider == PROVIDER,
                SyncDiscoveredAthlete.consumed.is_(False),
            )
            .order_by(SyncDiscoveredAthlete.external_id)
        )
        if limit:
            stmt = stmt.limit(limit)
        result = await self._db.execute(stmt)
        return [str(row) for row in result.scalars().all()]

    async def mark_consumed(
        self, external_ids: list[str], run_id: str | None = None
    ) -> int:
        """Mark athlete IDs consumed (window done / dead-ended 404).

        Does NOT commit — callers control transaction boundaries.
        """
        if not external_ids:
            return 0
        from src.db.models.support import SyncDiscoveredAthlete

        stmt = (
            update(SyncDiscoveredAthlete)
            .where(
                SyncDiscoveredAthlete.provider == PROVIDER,
                SyncDiscoveredAthlete.external_id.in_(external_ids),
            )
            .values(consumed=True)
        )
        result = await self._db.execute(stmt)
        return int(result.rowcount or 0)

    async def registry_count(self) -> int:
        """Total registry rows for the provider."""
        from sqlalchemy import func

        from src.db.models.support import SyncDiscoveredAthlete

        result = await self._db.execute(
            select(func.count())
            .select_from(SyncDiscoveredAthlete)
            .where(SyncDiscoveredAthlete.provider == PROVIDER)
        )
        return int(result.scalar_one())

    async def pending_count(self) -> int:
        """Unconsumed (queued) ids for the provider."""
        from sqlalchemy import func

        from src.db.models.support import SyncDiscoveredAthlete

        result = await self._db.execute(
            select(func.count())
            .select_from(SyncDiscoveredAthlete)
            .where(
                SyncDiscoveredAthlete.provider == PROVIDER,
                SyncDiscoveredAthlete.consumed.is_(False),
            )
        )
        return int(result.scalar_one())

    # ── Dialect-portable upsert (Postgres prod, SQLite tests) ─────────────

    def _insert(self, model: Any):
        """Build an ON CONFLICT DO NOTHING insert for the session's dialect.

        Postgres renders ON CONFLICT ON CONSTRAINT; SQLite renders a target-less
        ON CONFLICT DO NOTHING (valid for any uniqueness violation). Keeps the
        registry deduplicated and unit tests running on sqlite+aiosqlite.
        """
        dialect = getattr(getattr(self._db, "bind", None), "dialect", None)
        name = getattr(dialect, "name", "postgresql")
        if name == "sqlite":
            return sqlite.insert(model).on_conflict_do_nothing()
        return postgresql.insert(model).on_conflict_do_nothing(
            constraint="uq_sync_discovered_athletes_provider_external"
        )
