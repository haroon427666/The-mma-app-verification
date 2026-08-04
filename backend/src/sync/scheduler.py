"""
Sync scheduler — cron, manual, one-off execution of sync plans.

Provider-agnostic: schedules (provider_slug + plan_name + mode) → engine.
Concurrent-safe: ExecutionLock prevents duplicate runs of same plan/provider.
Graceful shutdown: waits for in-flight jobs to complete.

Uses APScheduler's AsyncIOScheduler under the hood.

Usage:
    engine = SyncEngine(jobs=registry)
    scheduler = SyncScheduler(engine, lock=InMemoryLock())

    scheduler.register(
        SyncJobDefinition(
            id="full_sync_espn",
            provider_slug="espn",
            plan_name="full_sync",
            cron="0 3 * * *",
            timezone="America/New_York",
        ),
        SyncJobDefinition(
            id="rankings_espn",
            provider_slug="espn",
            plan_name="rankings_sync",
            cron="0 */6 * * *",
            priority=50,  # lower = higher priority
        ),
    )

    await scheduler.start()
    # ...
    await scheduler.trigger("full_sync_espn")  # manual run
    print(scheduler.get_status())
    await scheduler.shutdown()
"""

import logging
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.date import DateTrigger

from src.providers.base import BaseDataProvider
from src.sync.engine import SyncEngine
from src.sync.lock import ExecutionLock, InMemoryLock
from src.sync.observability import AlertManager, StructuredLogger
from src.sync.plan import (
    EventsPlan,
    FighterPlan,
    FoundationPlan,
    FullSyncPlan,
    RankingsPlan,
    SyncPlan,
)
from src.sync.retry import RetryPolicy
from src.sync.types import SyncMode

logger = logging.getLogger(__name__)


# ── Plan registry ─────────────────────────────────────────────────────────────
# Maps plan_name → SyncPlan factory. Extend when adding new plans.

PLAN_REGISTRY: dict[str, type[SyncPlan]] = {
    "full_sync": FullSyncPlan,
    "rankings_sync": RankingsPlan,
    "events_sync": EventsPlan,
    "fighter_sync": FighterPlan,
    "foundation_sync": FoundationPlan,
}


# ── Job Definition ────────────────────────────────────────────────────────────


@dataclass
class SyncJobDefinition:
    """Declarative definition of a scheduled sync job.

    Provider-agnostic: specifies provider_slug + plan_name + mode.
    The engine handles the rest.
    """

    id: str
    """Unique identifier for this schedule (e.g. 'full_sync_espn')."""

    provider_slug: str
    """Provider to sync from (e.g. 'espn', 'tapology')."""

    plan_name: str
    """Plan to execute (e.g. 'full_sync', 'rankings_sync')."""

    mode: SyncMode | None = None
    """Sync mode override. None = auto-detect via SyncStrategy."""

    # Schedule
    cron: str | None = None
    """Cron expression (e.g. '0 3 * * *'). None = manual-only."""

    timezone: str = "UTC"
    """Timezone for cron schedule."""

    enabled: bool = True
    """If False, the job is registered but not scheduled."""

    # Behavior
    priority: int = 100
    """Lower = higher priority. Manual runs default to priority 0."""

    coalesce: bool = True
    """If multiple runs pile up (misfire), run only the latest."""

    misfire_grace_time: int | None = 3600
    """Seconds after a missed fire that the job is still considered 'on time'.
    None = no limit (always fire)."""

    max_instances: int = 1
    """Maximum concurrent instances. Default 1 prevents self-overlap."""

    # Retry
    retry_enabled: bool = True
    """If True, failed runs are retried according to retry_policy."""

    retry_policy: RetryPolicy | None = None
    """Retry strategy for failed sync runs. None = use DEFAULT_RETRY."""

    # Metadata
    description: str = ""
    """Human-readable description for visibility/debugging."""


# ── Run record ────────────────────────────────────────────────────────────────


@dataclass
class RunRecord:
    """Lightweight record of one sync execution for visibility."""

    definition_id: str
    provider_slug: str
    plan_name: str
    mode: SyncMode | None
    run_id: str
    started_at: datetime
    completed_at: datetime | None = None
    status: str = "RUNNING"
    error: str | None = None
    duration_ms: float = 0.0
    is_manual: bool = False


# ── Scheduler ─────────────────────────────────────────────────────────────────


class SyncScheduler:
    """APScheduler-based sync scheduler.

    Features:
    - Cron schedules (via CronTrigger)
    - Manual one-off runs (via trigger())
    - One-off future runs (via schedule_once())
    - Concurrent execution prevention (via ExecutionLock)
    - Misfire handling (missed executions coalesced or skipped)
    - Priority: manual runs take priority 0, scheduled use definition.priority
    - Visibility: get_status() returns all jobs + last runs
    - Graceful shutdown: waits for in-flight jobs
    """

    MAX_RUN_HISTORY = 100

    def __init__(
        self,
        engine: SyncEngine,
        providers: dict[str, BaseDataProvider] | None = None,
        lock: ExecutionLock | None = None,
        alert_manager: AlertManager | None = None,
        structured_logger: StructuredLogger | None = None,
    ) -> None:
        """Initialize the scheduler.

        Args:
            engine: SyncEngine instance (already configured with jobs).
            providers: {provider_slug: BaseDataProvider} map.
            lock: Distributed lock. Defaults to InMemoryLock.
            alert_manager: Optional alert manager for threshold-based alerts.
            structured_logger: Optional structured logger for context-aware logging.
        """
        self._engine = engine
        self._providers = providers or {}
        self._lock = lock or InMemoryLock()
        self._alert_manager = alert_manager
        self._slog = structured_logger or StructuredLogger()

        self._scheduler = AsyncIOScheduler()
        self._definitions: dict[str, SyncJobDefinition] = {}
        self._run_history: list[RunRecord] = []
        self._running: dict[str, RunRecord] = {}  # definition_id → current run

    # ── Registration ───────────────────────────────────────────────────────

    def register(self, *definitions: SyncJobDefinition) -> None:
        """Register one or more job definitions. Call before start()."""
        for d in definitions:
            if d.id in self._definitions:
                logger.warning(f"Job '{d.id}' already registered — overwriting")
            self._definitions[d.id] = d

    # ── Lifecycle ──────────────────────────────────────────────────────────

    async def start(self) -> None:
        """Start the scheduler. Adds all enabled cron jobs to APScheduler."""
        for def_id, d in self._definitions.items():
            if not d.enabled or not d.cron:
                continue

            trigger = CronTrigger.from_crontab(
                d.cron, timezone=d.timezone
            )

            self._scheduler.add_job(
                func=self._execute_job,
                trigger=trigger,
                args=[def_id],
                id=def_id,
                name=d.description or def_id,
                coalesce=d.coalesce,
                max_instances=d.max_instances,
                misfire_grace_time=d.misfire_grace_time,
                replace_existing=True,
            )
            logger.info(
                f"Scheduled '{def_id}': cron={d.cron} tz={d.timezone} "
                f"provider={d.provider_slug} plan={d.plan_name}"
            )

        self._scheduler.start()
        logger.info(f"Scheduler started with {len(self._definitions)} definitions")

    async def shutdown(self, wait: bool = True) -> None:
        """Graceful shutdown. Waits for in-flight jobs if wait=True."""
        logger.info("Scheduler shutting down...")
        if self._scheduler.running:
            self._scheduler.shutdown(wait=wait)
        logger.info("Scheduler stopped")

    # ── Manual execution ───────────────────────────────────────────────────

    async def trigger(
        self,
        definition_id: str,
        mode: SyncMode | None = None,
    ) -> str | None:
        """Trigger a manual run of a registered definition.

        Returns:
            run_id if the run was started, None if another run is in progress.
        """
        d = self._definitions.get(definition_id)
        if d is None:
            logger.error(f"Unknown job definition: {definition_id}")
            return None

        logger.info(f"Manual trigger: {definition_id} (mode={mode})")
        return await self._execute_job(definition_id, override_mode=mode, is_manual=True)

    async def schedule_once(
        self,
        definition_id: str,
        run_at: datetime,
        mode: SyncMode | None = None,
    ) -> str:
        """Schedule a one-off future run.

        Args:
            definition_id: Registered job definition.
            run_at: When to execute (timezone-aware).
            mode: SyncMode override.
        """
        d = self._definitions.get(definition_id)
        if d is None:
            raise ValueError(f"Unknown job definition: {definition_id}")

        job_id = f"{definition_id}_once_{run_at.timestamp()}"
        trigger = DateTrigger(run_date=run_at)
        self._scheduler.add_job(
            func=self._execute_job,
            trigger=trigger,
            args=[definition_id],
            kwargs={"override_mode": mode, "is_manual": True},
            id=job_id,
        )
        logger.info(f"One-off scheduled: {definition_id} at {run_at.isoformat()}")
        return job_id

    # ── Visibility ─────────────────────────────────────────────────────────

    def get_status(self) -> dict[str, Any]:
        """Return full visibility into all registered jobs and their runs."""
        jobs_status = []
        for def_id, d in self._definitions.items():
            aps_job = self._scheduler.get_job(def_id)
            running = self._running.get(def_id)

            jobs_status.append({
                "id": def_id,
                "provider": d.provider_slug,
                "plan": d.plan_name,
                "cron": d.cron,
                "timezone": d.timezone,
                "enabled": d.enabled,
                "mode": d.mode.value if d.mode else "auto",
                "priority": d.priority,
                "next_run": aps_job.next_run_time.isoformat() if aps_job and aps_job.next_run_time else None,
                "is_running": running is not None,
                "current_run_id": running.run_id if running else None,
                "description": d.description,
            })

        return {
            "total_definitions": len(self._definitions),
            "active_schedules": sum(1 for d in self._definitions.values() if d.enabled and d.cron),
            "running_jobs": len(self._running),
            "jobs": jobs_status,
            "recent_runs": [
                {
                    "definition_id": r.definition_id,
                    "run_id": r.run_id,
                    "status": r.status,
                    "started_at": r.started_at.isoformat() if r.started_at else None,
                    "duration_ms": r.duration_ms,
                    "is_manual": r.is_manual,
                }
                for r in self._run_history[-20:]  # Last 20 runs
            ],
        }

    def get_run_history(self, definition_id: str, limit: int = 20) -> list[RunRecord]:
        """Get recent runs for a specific job definition."""
        return [
            r for r in self._run_history
            if r.definition_id == definition_id
        ][-limit:]

    # ── Internal: job execution ────────────────────────────────────────────

    async def _execute_job(
        self,
        definition_id: str,
        override_mode: SyncMode | None = None,
        is_manual: bool = False,
    ) -> str | None:
        """Core execution: lock → build → execute → record.

        Returns run_id on success, None if locked by another instance.
        """
        d = self._definitions.get(definition_id)
        if d is None:
            logger.error(f"Unknown definition: {definition_id}")
            return None

        # ── Concurrent execution prevention ────────────────────────────
        acquired = await self._lock.acquire(d.plan_name, d.provider_slug)
        if not acquired:
            logger.warning(
                f"Skipping '{definition_id}': another instance is running "
                f"{d.plan_name}/{d.provider_slug}"
            )
            return None

        try:
            # ── Build plan ──────────────────────────────────────────────
            plan_cls = PLAN_REGISTRY.get(d.plan_name)
            if plan_cls is None:
                logger.error(f"Unknown plan: {d.plan_name}")
                return None
            plan = plan_cls()

            # ── Get provider ────────────────────────────────────────────
            provider = self._providers.get(d.provider_slug)
            if provider is None:
                logger.error(f"Unknown provider: {d.provider_slug}")
                return None

            mode = override_mode or d.mode

            # ── Create run record ───────────────────────────────────────
            record = RunRecord(
                definition_id=definition_id,
                provider_slug=d.provider_slug,
                plan_name=d.plan_name,
                mode=mode,
                run_id="",
                started_at=datetime.now(UTC),
                is_manual=is_manual,
            )
            self._running[definition_id] = record

            # ── Execute ─────────────────────────────────────────────────
            logger.info(
                f"Executing: {definition_id} plan={d.plan_name} "
                f"provider={d.provider_slug} mode={mode}"
            )

            result = await self._engine.execute(
                plan=plan,
                provider=provider,
                mode=mode,
            )

            # ── Record result ───────────────────────────────────────────
            record.run_id = result.run_id
            record.completed_at = result.completed_at or datetime.now(UTC)
            record.duration_ms = result.duration_ms
            record.status = result.overall_status.value

            self._add_to_history(record)

            # Phase 3.7: check alert thresholds after each run
            if self._alert_manager:
                alerts = self._alert_manager.check_run_result(
                    result.run_id, result
                )
                if alerts:
                    logger.warning(
                        f"{len(alerts)} alert(s) triggered for run {result.run_id}"
                    )

            return result.run_id

        except Exception as e:
            logger.exception(f"Job '{definition_id}' failed")
            rec = self._running.get(definition_id)
            if rec:
                rec.status = "FAILED"
                rec.error = str(e)
                rec.completed_at = datetime.now(UTC)
                self._add_to_history(rec)
            return None

        finally:
            self._running.pop(definition_id, None)
            await self._lock.release(d.plan_name, d.provider_slug)

    # ── Helpers ────────────────────────────────────────────────────────────

    def _add_to_history(self, record: RunRecord) -> None:
        self._run_history.append(record)
        if len(self._run_history) > self.MAX_RUN_HISTORY:
            self._run_history = self._run_history[-self.MAX_RUN_HISTORY :]
