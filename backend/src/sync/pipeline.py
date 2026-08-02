"""
Sync pipeline — the layer between SyncEngine and SyncJob.

The pipeline owns:
- Retries        (via injected RetryPolicy)
- Batching       (batch_size from SyncJob metadata)
- Pagination     (page-by-page with checkpointing)
- Cancellation   (checked between batches)
- Metrics        (provider, database, HTTP timers)
- Checkpointing  (SyncState updated after each batch)
- Events         (on_batch_complete, on_retry, on_failure)

Jobs only know:
- _fetch(ctx, state) → list[DTO]
- _transform(ctx, dtos) → list[DTO]
- _upsert(ctx, dtos) → dict

This keeps jobs extremely small — typically 30-80 lines each.
"""

import logging
from typing import Any

from src.sync.clock import Clock
from src.sync.context import SyncContext
from src.sync.events import SyncEventBus, SyncEventCtx
from src.sync.failure import CircuitBreakerOpenError, FailureCategory
from src.sync.job import JobResult, JobStatus, SyncJob
from src.sync.reliability import ReliabilityConfig
from src.sync.retry import DEFAULT_RETRY, RetryPolicy
from src.sync.state import SyncState
from src.sync.strategy import SyncDecision, SyncStrategy
from src.sync.types import SyncMode

logger = logging.getLogger(__name__)


class SyncPipeline:
    """Executes a single SyncJob with retries, batching, and checkpointing.

    The engine creates one pipeline per job. The pipeline:
    1. Checks checkpoint state → decides full vs incremental
    2. Fetches data from provider (with retry)
    3. Processes in batches (with cancellation checks between batches)
    4. Saves checkpoint after each batch
    5. Collects metrics and fires events
    """

    def __init__(
        self,
        job: SyncJob,
        retry_policy: RetryPolicy | None = None,
        strategy: SyncStrategy | None = None,
        reliability: ReliabilityConfig | None = None,
    ) -> None:
        self._job = job
        self._retry = retry_policy or DEFAULT_RETRY
        self._strategy = strategy or SyncStrategy()
        self._reliability = reliability

    # ── Main entry point ───────────────────────────────────────────────────

    async def execute(
        self,
        ctx: SyncContext,
        state: SyncState,
        events: SyncEventBus | None = None,
        requested_mode: SyncMode | None = None,
    ) -> JobResult:
        """Execute a job through the full pipeline.

        PHASE 3.4: Determines sync mode (full/incremental/resume) before fetch.
        Passes updated_since/cursor/offset to the job via SyncState.
        On crash: next run auto-resumes from last checkpointed page.

        Args:
            ctx: Sync context (provider, db, logger, clock).
            state: Per-entity sync state (checkpoint, last sync, cursor).
            events: Optional event bus.
            requested_mode: Optional override (FULL, INCREMENTAL, RESUME, FORCE).

        Returns:
            JobResult with per-entity metrics.
        """
        clock: Clock = ctx.clock
        job = self._job
        job_logger = ctx.logger or logger

        # ── Phase 3.4: Determine sync mode ─────────────────────────────
        decision = self._strategy.decide(
            state=state,
            capabilities=None,  # Injected later from provider
            requested=requested_mode,
        )
        job_logger.info(
            f"{job.entity_type.value}: mode={decision.mode.value} "
            f"reason="{decision.reason}" "
            f"page={decision.start_page} offset={decision.start_offset}"
        )

        # Apply decision to state so the job can read it
        if decision.updated_since:
            state.updated_since = decision.updated_since
        if decision.cursor:
            state.last_cursor = decision.cursor
        if decision.start_offset > 0:
            state.last_offset = decision.start_offset

        # Fire before_job event
        if events:
            await events.fire_before_job(self._event_ctx(ctx), job.entity_type)

        state.mark_started(clock.now())
        start = clock.monotonic()

        try:
            # Phase 3.6: check circuit breaker before any provider call
            provider_slug = ctx.provider.provider_slug if ctx.provider else "unknown"
            if self._reliability:
                try:
                    await self._reliability.before_provider_call(provider_slug)
                except CircuitBreakerOpenError as cb_err:
                    job_logger.warning(f"Circuit breaker open: {cb_err}")
                    return JobResult(
                        entity_type=job.entity_type.value,
                        status=JobStatus.FAILED,
                        records_errors=1,
                        error_msg=str(cb_err),
                    )

            # 1. Fetch (with retry + circuit breaker)
            ctx.metrics.start_provider_timer()
            try:
                dtos = await self._retry.execute(
                    lambda: job._fetch(ctx, state),
                    context=f"{job.entity_type.value}.fetch",
                )
                # Phase 3.6: record success with circuit breaker
                if self._reliability:
                    await self._reliability.on_provider_success()
            finally:
                ctx.metrics.stop_provider_timer()

            job_logger.info(f"{job.entity_type.value}: fetched {len(dtos)} items")

            # 2. Transform
            transformed = await job._transform(ctx, dtos)

            # 3. Upsert in batches with checkpointing
            ctx.metrics.start_db_timer()
            batch_results = await self._upsert_in_batches(
                ctx, state, transformed, events
            )
            ctx.metrics.stop_db_timer()

            # 4. Update entity metrics
            entity_metrics = ctx.metrics.entity(job.entity_type.value)
            entity_metrics.inserted += batch_results["inserted"]
            entity_metrics.updated += batch_results["updated"]
            entity_metrics.skipped += batch_results["skipped"]
            entity_metrics.errors += batch_results["errors"]

            # 5. Mark complete
            state.mark_completed(clock.now())

            result = JobResult(
                entity_type=job.entity_type.value,
                status=JobStatus.COMPLETED,
                records_inserted=batch_results["inserted"],
                records_updated=batch_results["updated"],
                records_skipped=batch_results["skipped"],
                records_errors=batch_results["errors"],
                api_calls=ctx.metrics.provider.calls,
                duration_ms=(clock.monotonic() - start) * 1000,
            )

            if events:
                await events.fire_after_job(
                    self._event_ctx(ctx), job.entity_type, result
                )

            return result

        except Exception as e:
            # Phase 3.6: classify failure → circuit-break or dead-letter
            provider_slug = ctx.provider.provider_slug if ctx.provider else "unknown"
            if self._reliability:
                category = await self._reliability.on_provider_failure(
                    error=e,
                    provider_slug=provider_slug,
                    entity_type=job.entity_type,
                    run_id=ctx.run_id,
                )
                job_logger.error(
                    f"Sync job {job.entity_type.value}: {category.value} — {e}"
                )
            else:
                job_logger.error(f"Sync job {job.entity_type.value}: {e}")

            state.mark_failed(clock.now(), str(e))
            entity_metrics = ctx.metrics.entity(job.entity_type.value)
            entity_metrics.errors += 1

            if events:
                await events.fire_failure(
                    self._event_ctx(ctx), job.entity_type, e
                )

            return JobResult(
                entity_type=job.entity_type.value,
                status=JobStatus.FAILED,
                records_errors=1,
                duration_ms=(clock.monotonic() - start) * 1000,
                error_msg=str(e),
            )

    # ── Batch processing ───────────────────────────────────────────────────

    async def _upsert_in_batches(
        self,
        ctx: SyncContext,
        state: SyncState,
        dtos: list[Any],
        events: SyncEventBus | None,
    ) -> dict[str, int]:
        """Process DTOs in batches with checkpointing after each batch.

        If the pipeline crashes mid-run, the next run resumes from the
        last checkpointed batch, not from the beginning.
        """
        batch_size = self._job.batch_size
        total = len(dtos)
        totals = {"inserted": 0, "updated": 0, "skipped": 0, "errors": 0}
        batch_num = 0

        for start in range(0, total, batch_size):
            # Check cancellation between batches
            ctx.token.check()

            batch_num += 1
            batch = dtos[start : start + batch_size]

            result = await self._job._upsert(ctx, batch)

            # Accumulate
            for key in totals:
                totals[key] += result.get(key, 0)

            # Checkpoint after each successful batch
            state.update_progress(
                page=batch_num,
                offset=start + len(batch),
                items_synced=len(batch),
            )

            # Fire batch event
            if events:
                await events.fire_batch_complete(
                    self._event_ctx(ctx),
                    self._job.entity_type,
                    batch_num,
                    len(batch),
                )

            ctx.progress.advance(len(batch), batch_num)

        return totals

    # ── Helpers ────────────────────────────────────────────────────────────

    @staticmethod
    def _event_ctx(ctx: SyncContext) -> SyncEventCtx:
        return SyncEventCtx(
            run_id=ctx.run_id,
            provider_slug=ctx.provider.provider_slug if ctx.provider else "unknown",
            progress_pct=ctx.progress.percent,
            metrics=ctx.metrics.summary() if ctx.metrics else {},
        )
