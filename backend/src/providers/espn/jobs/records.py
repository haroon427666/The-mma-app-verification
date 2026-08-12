"""ESPN Records backfill job — records-only, registry-neutral.

W007 purpose: re-fetch `/athletes/{id}/records` for fighters whose records
were never fetched or were interrupted by a breaker/503 episode (W006's
records phase stopped early: ~4,608 W006 fighters lack records, plus ~993
pre-existing).

Contract differences from the fighter job (all deliberate):
- Operates ONLY on fighters already in the database — the discovery registry
  (sync_discovered_athletes) is never read, written, or advanced; discovery
  walks are never run. Registry consumed/pending counts are untouched.
- Writes ONLY the fighter_records table via FighterUpsert.upsert_records —
  a records-only DTO must never go through upsert_batch (BaseUpsert FIELD_MAP
  change detection would clobber fighter profile columns to NULL).
- Content-dependent 404/empty payloads → fetch_fighter_record returns None →
  no row, no fake 0-0-0-0. The "never reset stored values" rule is preserved.
- Transient 503/network errors also surface as None (provider swallows them),
  so the breaker trips at the client level and the fighter simply stays in
  the missing set — the next bounded rerun re-probes exactly the remainder.
- Bounded per run by ESPN_RECORDS_BACKFILL_LIMIT (default 0 = all missing,
  which is itself bounded by the existing-fighter set — never the census).
- Rerun-safe/idempotent: records upsert is keyed on fighter_id (unique);
  fighters already having records are excluded by the target query.
- Phase D (absence classification): every fetch is classified AVAILABLE /
  EMPTY / FAILED. EMPTY (200-empty or content 404) persists CONFIRMED_ABSENT
  so future runs skip known absences; FAILED persists FETCH_FAILED (retryable
  within MAX_RECORD_FETCH_RETRIES) — failures are never absence evidence.
  A persisted absence NEVER blocks a future real record (FighterUpsert
  deletes the status row when a record is persisted).
"""

import asyncio
import logging
import os
from typing import Any, cast

from sqlalchemy import and_, or_, select

from src.db.models.support import FighterProviderRecordStatus
from src.domain.models.fighter import Fighter, FighterRecord
from src.providers.dto import FighterDTO
from src.sync.job import SyncJob
from src.sync.types import EntityType, RecordFetchOutcome, RecordFetchStatus

logger = logging.getLogger(__name__)


def _backfill_limit() -> int:
    """Bounded per-run records backfill size (0 = all missing fighters)."""
    try:
        return int(os.environ.get("ESPN_RECORDS_BACKFILL_LIMIT", "0") or 0)
    except ValueError:
        return 0


# Transient failures are retried up to this many times before the fighter is
# left queued for an explicit operator decision (Phase D retry budget).
MAX_RECORD_FETCH_RETRIES = 3


class ESPN_RecordsBackfillJob(SyncJob):
    entity_type = EntityType.RECORDS
    depends_on = [EntityType.FIGHTER]
    critical = False  # records are enrichment — never abort a run on failure
    batch_size = 100
    supports_incremental = False

    async def _fetch(self, ctx: Any, state: Any) -> list[Any]:
        provider = ctx.provider
        limit = _backfill_limit()

        # 1. Existing fighters missing fighter_records, deterministic order.
        #    Never touches the discovery registry — pure fighters-table query.
        #    Phase D: fighters whose absence is established evidence
        #    (CONFIRMED_ABSENT, or FETCH_FAILED past the retry budget) are
        #    excluded — they are not a fetch backlog.
        stmt = (
            select(Fighter.external_id)
            .outerjoin(FighterRecord, FighterRecord.fighter_id == Fighter.id)
            .outerjoin(
                FighterProviderRecordStatus,
                and_(
                    FighterProviderRecordStatus.fighter_id == Fighter.id,
                    FighterProviderRecordStatus.provider == "espn",
                ),
            )
            .where(
                FighterRecord.id.is_(None),
                or_(
                    FighterProviderRecordStatus.fighter_id.is_(None),
                    and_(
                        FighterProviderRecordStatus.status
                        == RecordFetchStatus.FETCH_FAILED.value,
                        FighterProviderRecordStatus.retry_count
                        < MAX_RECORD_FETCH_RETRIES,
                    ),
                ),
            )
            .order_by(Fighter.external_id.asc())
        )
        if limit:
            stmt = stmt.limit(limit)
        rows = (await ctx.db.execute(stmt)).scalars().all()
        ids = list(rows)
        if not ids:
            logger.info("Records backfill: no fighters missing records — done")
            return []

        logger.info(
            f"Records backfill: {len(ids)} fighters missing records "
            f"(limit={limit or 'all'})"
        )

        # 2. Fetch /athletes/{id}/records with bounded concurrency. The client
        #    rate-limiter + circuit breaker protect the envelope; the provider
        #    returns None for 404/empty AND transient failures (no crash, no
        #    fake data). Never resets stored values.
        sem = asyncio.Semaphore(provider._config.max_concurrency)

        async def fetch(
            eid: str,
        ) -> tuple[FighterDTO, RecordFetchOutcome, int | None]:
            dto = FighterDTO(
                provider="espn", external_id=eid, first_name="", last_name=""
            )
            async with sem:
                record, outcome, http_status = (
                    await provider.fetch_fighter_record_with_outcome(eid)
                )
            if record is None:
                return dto, outcome, http_status
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
            return dto, RecordFetchOutcome.AVAILABLE, http_status

        dtos = await asyncio.gather(*(fetch(eid) for eid in ids))

        # Lazy import mirrors the fighter job's pattern (avoids import cycles).
        from src.sync.upserts.fighter import FighterUpsert

        with_data = sum(1 for d, _o, _s in dtos if FighterUpsert._has_record_data(d))
        empty = sum(1 for _d, o, _s in dtos if o == RecordFetchOutcome.EMPTY)
        failed = sum(1 for _d, o, _s in dtos if o == RecordFetchOutcome.FAILED)
        logger.info(
            f"Records backfill: {with_data}/{len(ids)} returned real record "
            f"payloads ({empty} empty, {failed} transient failures)"
        )
        return cast(list[Any], dtos)

    async def _upsert(self, ctx: Any, dtos: list[Any]) -> dict[str, int]:
        from src.sync.upserts.fighter import FighterUpsert
        from src.sync.upserts.id_resolver import IdResolver

        resolver = IdResolver(ctx.db)
        upsert = FighterUpsert(resolver)
        payload = [dto for dto, _outcome, _status in dtos]
        result = await upsert.upsert_records(payload)
        status_counts = await upsert.apply_record_fetch_outcomes(
            dtos, run_id=ctx.run_id
        )
        await ctx.db.flush()
        logger.info(
            f"Records backfill status: {status_counts['status_absent']} "
            f"confirmed absent, {status_counts['status_failed']} fetch failed, "
            f"{status_counts['status_cleared']} cleared"
        )
        return {
            "inserted": result.inserted,
            "updated": result.updated,
            "skipped": result.skipped,
            "errors": result.errors,
            **status_counts,
        }
