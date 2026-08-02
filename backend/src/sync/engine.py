"""
Sync engine — plan-based orchestrator.

The engine knows NOTHING about entities, dependencies, or ordering.
It receives a SyncPlan and executes it. Plans define WHAT and in WHAT ORDER.
The engine defines HOW.

Plans:
- FullSyncPlan → 9 jobs in dependency order
- RankingsPlan → 1 job
- EventsPlan → 3 jobs (events, competitions, broadcasts)
- FighterPlan → 2 jobs (fighters, statistics)
- FoundationPlan → 3 jobs (promotions, venues, weight_classes)

All reuse this exact same engine.
"""

import logging
from datetime import datetime, timezone
from typing import Any

from src.providers.base import BaseDataProvider
from src.sync.clock import SystemClock
from src.sync.context import CancellationToken, ProgressTracker, SyncContext
from src.sync.dependency import DependencyGraph
from src.sync.events import SyncEventBus, SyncEventCtx
from src.sync.job import JobResult, SyncJob
from src.sync.metrics import SyncMetrics
from src.sync.pipeline import SyncPipeline
from src.sync.plan import SyncPlan
from src.sync.result import SyncResult, SyncStatus
from src.sync.reliability import ReliabilityConfig
from src.sync.state import SyncState
from src.sync.state_store import SyncStateStore
from src.sync.types import EntityType, JobStatus, SyncMode

logger = logging.getLogger(__name__)


class SyncEngine:
    """Plan-based sync orchestrator.

    Usage:
        engine = SyncEngine(jobs={
            EntityType.PROMOTION: PromotionSyncJob(),
            EntityType.FIGHTER: FighterSyncJob(),
            ...
        })

        plan = FullSyncPlan()
        result = await engine.execute(plan=plan, provider=espn_provider)
        print(result.summary())
    """

    def __init__(
        self,
        jobs: dict[EntityType, SyncJob],
        statestore: "SyncStateStore | None" = None,
        events: SyncEventBus | None = None,
        reliability: ReliabilityConfig | None = None,
    ) -> None:
        """Initialize the engine.

        Args:
            jobs: Map of EntityType → SyncJob. The engine looks up jobs by type.
            statestore: Persistence for SyncState (checkpoints, cursors).
                       If None, state is in-memory only (no resume).
            events: Optional event bus for lifecycle hooks.
            reliability: Optional reliability config (circuit breaker, dead-letter).
        """
        self._jobs = jobs
        self._statestore = statestore
        self._events = events or SyncEventBus()
        self._reliability = reliability

    # ── Public API ─────────────────────────────────────────────────────────

    async def execute(
        self,
        plan: SyncPlan,
        provider: BaseDataProvider,
        db_session: Any = None,
        token: CancellationToken | None = None,
        mode: SyncMode | None = None,
    ) -> SyncResult:
        """Execute a sync plan against a provider.

        Args:
            plan: What to sync and in what order.
            provider: Data source (ESPN, Tapology, etc.).
            db_session: Optional SQLAlchemy async session for DB writes.
            token: Optional cancellation token.
            mode: Optional SyncMode override (FULL, INCREMENTAL, RESUME, FORCE).
                  If None, SyncStrategy auto-detects from state.

        Returns:
            SyncResult with per-job and aggregate metrics.
        """
        if token is None:
            token = CancellationToken()

        clock = SystemClock()
        started_at = clock.now()
        run_id = ""

        # Build context
        ctx = SyncContext(
            provider=provider,
            db=db_session,
            logger=logger,
            clock=clock,
            token=token,
        )
        run_id = ctx.run_id

        lookback_seconds = 3600  # Default 1-hour deduplication window

        ctx.progress = ProgressTracker(total_jobs=plan.job_count)
        ctx.metrics = SyncMetrics()

        logger.info(
            f"Sync run started: {run_id} "
            f"plan={plan.name} "
            f"provider={provider.provider_slug} "
            f"jobs={plan.job_count}"
        )

        # Fire before_sync event
        await self._events.fire_before_sync(self._event_ctx(ctx))

        # Execute jobs — order resolved from plan + dependency graph
        ordered_jobs = self._resolve_order(plan)

        job_results: list[JobResult] = []
        overall_status = SyncStatus.COMPLETED

        try:
            for job in ordered_jobs:
                ctx.token.check()

                # Load or create sync state
                state = await self._get_state(job.entity_type, provider.provider_slug)

                # Build pipeline with strategy and execute
                pipeline = SyncPipeline(
                    job=job,
                    reliability=self._reliability,
                )
                result = await pipeline.execute(
                    ctx, state, events=self._events, requested_mode=mode
                )
                job_results.append(result)

                # Persist state after each job
                await self._save_state(state)

                if result.status == JobStatus.FAILED and job.critical:
                    overall_status = SyncStatus.FAILED
                    logger.error(
                        f"Critical job failed: {job.entity_type.value}. "
                        f"Aborting plan '{plan.name}'."
                    )
                    break

                ctx.progress.mark_completed(job.entity_type.value)

            # Determine overall status
            if overall_status == SyncStatus.COMPLETED:
                if any(r.status == JobStatus.FAILED for r in job_results):
                    overall_status = SyncStatus.PARTIAL

        except Exception as e:
            overall_status = SyncStatus.CANCELLED
            logger.warning(f"Sync run cancelled: {run_id} — {e}")

        # Finalize
        completed_at = clock.now()
        duration_ms = (clock.monotonic() - (started_at.timestamp() if hasattr(started_at, 'timestamp') else 0)) * 1000
        # Use clock for accurate duration
        duration_ms = (clock.now().timestamp() - started_at.timestamp()) * 1000 if clock.now() > started_at else 0

        result = SyncResult(
            run_id=run_id,
            overall_status=overall_status,
            job_results=job_results,
            started_at=started_at,
            completed_at=completed_at,
            duration_ms=abs(duration_ms),
        )

        # Fire after_sync event
        await self._events.fire_after_sync(self._event_ctx(ctx), result)

        logger.info(
            f"Sync run finished: {run_id} "
            f"plan={plan.name} "
            f"status={overall_status.value} "
            f"jobs={result.total_jobs} "
            f"inserted={result.total_inserted} "
            f"updated={result.total_updated} "
            f"errors={result.total_errors} "
            f"duration={result.duration_ms:.0f}ms"
        )

        return result

    # ── Dependency resolution ──────────────────────────────────────────────

    def _resolve_order(self, plan: SyncPlan) -> list[SyncJob]:
        """Resolve execution order using the dependency graph.

        1. Build dependency graph from job registrations.
        2. Validate the plan's declared order.
        3. If valid → use plan order (plans are authoritative).
        4. If invalid → fall back to topological sort with a warning.
        """
        graph = DependencyGraph.from_jobs(self._jobs)

        # Validate plan order against declared dependencies
        is_valid, msg = graph.validate_plan(plan)
        if not is_valid:
            logger.warning(
                f"Plan '{plan.name}' order violates dependencies: {msg}. "
                f"Falling back to topological sort."
            )
            try:
                sorted_order = graph.topological_sort()
                plan_set = set(plan.order)
                plan_order = [e for e in sorted_order if e in plan_set]
                return [self._jobs[e] for e in plan_order if e in self._jobs]
            except ValueError as e:
                raise ValueError(
                    f"Cannot resolve plan '{plan.name}': {e}"
                ) from e

        # Plan is valid — use declared order
        return [self._jobs[e] for e in plan.order if e in self._jobs]

    async def _get_state(
        self, entity_type: EntityType, provider_slug: str
    ) -> SyncState:
        """Load or create sync state for an entity/provider pair."""
        if self._statestore:
            state = await self._statestore.load(entity_type, provider_slug)
            if state:
                return state
        return SyncState.for_entity(entity_type, provider_slug)

    async def _save_state(self, state: SyncState) -> None:
        """Persist sync state after a job completes."""
        if self._statestore:
            await self._statestore.save(state)

    # ── Helpers ────────────────────────────────────────────────────────────

    @staticmethod
    def _event_ctx(ctx: SyncContext) -> SyncEventCtx:
        return SyncEventCtx(
            run_id=ctx.run_id,
            provider_slug=ctx.provider.provider_slug if ctx.provider else "unknown",
            progress_pct=ctx.progress.percent,
            metrics=ctx.metrics.summary() if ctx.metrics else {},
        )


# Re-exported from state_store module (kept here for backward compatibility)
# New code should import from src.sync.state_store directly.
from src.sync.state_store import MemorySyncStateStore  # noqa: F401
