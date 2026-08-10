"""ESPN Fighter sync job — discovery-driven.

Discovery sources (frozen research P0): global flat listing (/athletes) +
configured league rosters (/leagues/{slug}/athletes), deduplicated by ESPN
athlete ID. Hidden profiles (DJ/Rousey/Gracie/Ngannou...) that are absent from
listings are reached via ranking injection / competition refs; the fighter job
resolves every discovered ID exactly once (client cache + in-flight dedup).

The discovered ID set lives in the durable registry (sync_discovered_athletes),
NOT in SyncState: a COMPLETED discovery source is never re-walked and the
window is the next N UNCONSUMED registry IDs (ascending). Consumed flags make
progress crash-proof — a re-run never re-scans the synced prefix.

Records (/athletes/{id}/records) are fetched per fighter with bounded
concurrency and persisted to the fighter_records table via FighterUpsert.
A missing/empty records response NEVER resets stored values.

Resume semantics:
- successfully upserted ids → consumed (per batch, in _upsert);
- content-dependent 404 / parse failure → consumed once in _fetch (never
  retried — matches the records "never reset" rule), but ONLY when the fetch
  was healthy (breaker closed, no 5xx/429/network errors) — under system
  trouble ids stay queued and are retried on the next run.
"""

import asyncio
import logging
import os
from typing import Any, cast

from src.providers.dto import FighterDTO
from src.sync.job import SyncJob
from src.sync.types import EntityType

logger = logging.getLogger(__name__)


def _sync_limit() -> int:
    """Bounded per-run discovery window (ESPN_FIGHTER_SYNC_LIMIT, default 0 = all)."""
    try:
        return int(os.environ.get("ESPN_FIGHTER_SYNC_LIMIT", "0") or 0)
    except ValueError:
        return 0


async def attach_records(
    provider: Any, fighters: list[FighterDTO]
) -> list[FighterDTO]:
    """Fetch each fighter's /athletes/{id}/records with bounded concurrency.

    Never resets stored records: fetch_fighter_record returns None for
    empty/unavailable payloads and the DTO keeps None fields, which
    FighterUpsert skips.
    """
    if not fighters:
        return fighters

    sem = asyncio.Semaphore(provider._config.max_concurrency)

    async def attach(dto: FighterDTO) -> None:
        async with sem:
            record = await provider.fetch_fighter_record(dto.external_id)
            if record is None:
                return
            dto.record_summary = record.record_summary
            dto.ko_tko_wins = record.ko_tko_wins
            dto.ko_tko_losses = record.ko_tko_losses
            dto.submission_wins = record.submission_wins
            dto.submission_losses = record.submission_losses
            dto.title_wins = record.title_wins
            dto.title_losses = record.title_losses
            dto.title_draws = record.title_draws
            dto.total_fights = record.total_fights
            dto.win_percentage = record.win_percentage
            dto.finish_rate = record.finish_rate
            dto.record_wins = record.wins
            dto.record_losses = record.losses
            dto.record_draws = record.draws
            dto.record_no_contests = record.no_contests

    await asyncio.gather(*(attach(f) for f in fighters))
    return fighters


class ESPN_FighterSyncJob(SyncJob):
    entity_type = EntityType.FIGHTER
    depends_on = [EntityType.WEIGHT_CLASS]
    critical = True
    batch_size = 100
    supports_incremental = False  # ESPN doesn't support modifiedSince for athletes

    async def _fetch(self, ctx: Any, state: Any) -> list[Any]:
        provider = ctx.provider

        # 1. Ensure the durable census is walked (resumable; completed sources
        #    are skipped — no repeated prefix scanning).
        from src.providers.espn.discovery import DiscoveryService

        service = DiscoveryService(provider=provider, session=ctx.db)
        summaries = await service.ensure_enumerated(run_id=ctx.run_id)
        for s in summaries:
            if s.skipped:
                logger.info(
                    f"Fighter discovery {s.source}/{s.league_slug or 'global'}: "
                    f"already completed ({s.discovered} ids) — skipped"
                )
            else:
                logger.info(
                    f"Fighter discovery {s.source}/{s.league_slug or 'global'}: "
                    f"{s.discovered} ids ({s.inserted} new), "
                    f"pages {s.started_page}.., completed={s.completed}"
                )

        # 2. Window: next N unconsumed registry ids (ascending), bounded per run
        limit = _sync_limit()
        window = await service.next_window(limit)
        if not window:
            logger.info(
                f"Fighter discovery window exhausted — nothing to fetch "
                f"(registry={await service.registry_count()}, "
                f"pending={await service.pending_count()})"
            )
            return []

        # 3. Resolve profiles with bounded concurrency
        #    fetch_fighters_by_ids swallows per-id failures (404 AND network)
        #    as None — so before consuming dead-ended ids we require a HEALTHY
        #    fetch: breaker closed and zero system-level signals (5xx/429/
        #    network errors). Under real system trouble the ids stay queued
        #    and are retried; content-dependent 404s are consumed once.
        from src.providers.espn.client import CircuitState

        client = provider._client
        signal_keys = ("network_errors", "server_errors_5xx", "rate_limited_429")
        before = {k: client.metrics.get(k, 0) for k in signal_keys}
        fighters = await provider.fetch_fighters_by_ids(window)
        after = {k: client.metrics.get(k, 0) for k in signal_keys}
        healthy = (
            client._circuit_breaker.state is CircuitState.CLOSED
            and all(after[k] == before[k] for k in signal_keys)
        )

        # 4. Content-dependent 404s / parse failures are dead-ended: consumed
        #    once, never retried.
        resolved_ids = {f.external_id for f in fighters}
        dead_ended = [i for i in window if i not in resolved_ids]
        if dead_ended:
            if healthy:
                await service.mark_consumed(dead_ended)
                logger.info(
                    f"Fighter window: {len(dead_ended)} unresolvable ids consumed "
                    f"(content-dependent 404/parse-fail, never retried)"
                )
            else:
                logger.warning(
                    f"Fighter window: {len(dead_ended)} ids unresolved during an "
                    f"unhealthy fetch (system signals detected) — left queued "
                    f"for retry, NOT consumed"
                )

        # 5. Attach records (bounded concurrency, best-effort)
        fighters = await self._attach_records(provider, fighters)

        # 6. Keep the service for _upsert to mark consumed
        self._service = service
        logger.info(
            f"Fighter window: {len(fighters)} resolved of {len(window)} ids"
        )
        return cast(list[Any], fighters)

    async def _attach_records(
        self, provider: Any, fighters: list[FighterDTO]
    ) -> list[FighterDTO]:
        return await attach_records(provider, fighters)

    async def _upsert(self, ctx: Any, dtos: list[Any]) -> dict[str, int]:
        from src.sync.upserts.fighter import FighterUpsert
        from src.sync.upserts.id_resolver import IdResolver

        resolver = IdResolver(ctx.db)
        upsert = FighterUpsert(resolver)
        result = await upsert.upsert_batch(dtos)
        await ctx.db.flush()

        # Only successfully upserted ids are consumed (crash-safe: a batch that
        # never persisted stays queued and is retried idempotently).
        service = getattr(self, "_service", None)
        if service is not None and dtos:
            consumed = await service.mark_consumed([d.external_id for d in dtos])
            logger.debug(
                f"Fighter window: marked {consumed} ids consumed "
                f"(pending={await service.pending_count()})"
            )

        return {"inserted": result.inserted, "updated": result.updated,
                "skipped": result.skipped, "errors": result.errors}
