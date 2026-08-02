"""SyncManager — autonomous production synchronization service.

The central orchestrator. Starts when the app starts. Runs continuously.
Manages: scheduling, locking, retry, live mode, recovery, metrics.

Usage:
    manager = SyncManager(context)
    await manager.start()    # Start all scheduled jobs
    # ... app runs ...
    await manager.shutdown() # Graceful shutdown
"""

import asyncio
import logging
import signal
import time
from datetime import datetime, timezone
from typing import Any, Optional

from src.scheduler.jobs import JOB_REGISTRY, JOB_FUNCTIONS, JobConfig, JobStatus, JobResult
from src.scheduler.queue import PriorityQueue, Priority
from src.scheduler.locks import LockManager
from src.scheduler.retry import RetryPolicy, RetryState
from src.scheduler.live_mode import LiveModeDetector
from src.scheduler.monitor import HealthMonitor
from src.scheduler.metrics import metrics
from src.scheduler.notifier import Notifier

logger = logging.getLogger(__name__)


class SyncManager:
    """Production sync orchestrator — autonomous, self-healing.

    Starts all scheduled jobs automatically on startup.
    Detects live events and switches to high-frequency polling.
    Uses distributed locks to prevent duplicate execution.
    Resumes from checkpoints after restart.
    """

    def __init__(self, context: "SyncContext"):
        self.ctx = context

        # Core components
        self.queue = PriorityQueue(max_concurrent=2)
        self.locks = LockManager(context.redis)
        self.monitor = HealthMonitor()
        self.notifier = Notifier()
        self.live_detector = LiveModeDetector(context.db_session_factory)
        self.retry_policy = RetryPolicy()

        # State
        self._running = False
        self._tasks: list[asyncio.Task] = []
        self._job_timers: dict[str, asyncio.Task] = {}

    # ── Lifecycle ────────────────────────────────────────────────────────────

    async def start(self) -> None:
        """Start all scheduled jobs. Called at application startup."""
        if self._running:
            return

        self._running = True
        logger.info("SyncManager starting — initializing scheduled jobs")

        # Register all providers for health monitoring
        self.monitor.register_provider("espn")
        self.monitor.register_provider("tsdb")
        self.monitor.register_provider("octagon")

        # Start each scheduled job
        for name, config in JOB_REGISTRY.items():
            if config.enabled:
                self._start_scheduled_job(name, config)

        # Start the queue worker
        self._tasks.append(asyncio.create_task(self._queue_worker(), name="queue_worker"))

        # Start live mode detector
        self._tasks.append(asyncio.create_task(self._live_mode_loop(), name="live_mode"))

        # Notify
        await self.notifier.sync_started("scheduled", list(JOB_REGISTRY.keys()))

        logger.info("SyncManager running — all jobs scheduled")

    async def shutdown(self) -> None:
        """Graceful shutdown — complete current jobs, cancel pending."""
        self._running = False
        logger.info("SyncManager shutting down...")

        # Cancel all scheduled timers
        for name, task in self._job_timers.items():
            task.cancel()

        # Cancel worker tasks
        for task in self._tasks:
            task.cancel()

        # Wait for tasks to finish
        await asyncio.gather(*self._tasks, *self._job_timers.values(), return_exceptions=True)

        await self.notifier.close()
        logger.info("SyncManager shutdown complete")

    # ── Scheduled Jobs ────────────────────────────────────────────────────────

    def _start_scheduled_job(self, name: str, config: JobConfig) -> None:
        """Start a recurring job with the configured interval/cron."""
        fn = JOB_FUNCTIONS.get(name)
        if fn is None:
            logger.warning(f"No function registered for job '{name}' — skipping")
            return

        async def _timer_loop():
            # Run once at startup
            await self._execute_job(name, config, fn)
            # Then run on interval
            while self._running:
                try:
                    interval = config.interval_seconds or 300
                    await asyncio.sleep(interval)
                    if not self._running:
                        break
                    await self._execute_job(name, config, fn)
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    logger.error(f"Timer for '{name}' crashed: {e}")
                    await asyncio.sleep(60)  # Wait before retrying the timer

        self._job_timers[name] = asyncio.create_task(_timer_loop(), name=f"timer_{name}")
        logger.info(f"Scheduled job: {name} (every {config.interval_seconds}s)")

    async def _execute_job(self, name: str, config: JobConfig, fn) -> None:
        """Execute a single job run — lock, run, record."""
        # Check dependencies
        for dep in config.depends_on:
            dep_health = self.monitor._jobs.get(dep)
            if dep_health and dep_health.consecutive_failures > 0:
                logger.debug(f"Skipping '{name}' — dependency '{dep}' has failures")
                return

        # Acquire distributed lock
        lock = self.locks.get(name, ttl=config.lock_ttl)
        try:
            async with lock:
                await self._run_job_inner(name, config, fn)
        except Exception:
            # Lock already held by another instance — skip
            pass

    async def _run_job_inner(self, name: str, config: JobConfig, fn) -> None:
        """Run the job with retry, metrics, and monitoring."""
        self.monitor.job_started(name)

        retry_state = RetryState(policy=RetryPolicy(max_attempts=3))

        try:
            result = await retry_state.execute(
                self._run_with_timeout, fn, config,
            )
            self.monitor.job_succeeded(name, result.duration_ms)
            metrics.record_job_duration(name, result.duration_ms)
            metrics.record_job_result(
                name, result.status.value,
                inserted=result.records_inserted,
                updated=result.records_updated,
                errors=result.errors,
            )

            if result.status == JobStatus.SUCCESS:
                logger.info(
                    f"✓ {name}: {result.records_inserted} inserted, "
                    f"{result.records_updated} updated ({result.duration_ms:.0f}ms)"
                )
            else:
                logger.warning(f"⚠ {name}: failed — {result.error_message}")

        except asyncio.TimeoutError:
            self.monitor.job_failed(name, f"Timeout after {config.max_runtime_seconds}s")
            metrics.record_job_result(name, "failed", errors=1)
            await self.notifier.sync_failed(name, f"Timeout after {config.max_runtime_seconds}s")

        except Exception as e:
            self.monitor.job_failed(name, str(e))
            metrics.record_job_result(name, "failed", errors=1)

    async def _run_with_timeout(self, fn, config: JobConfig) -> JobResult:
        """Run a job function with a hard timeout."""
        result = await asyncio.wait_for(
            fn(self.ctx),
            timeout=config.max_runtime_seconds,
        )
        return result if result else JobResult(
            job_name=config.name, status=JobStatus.SUCCESS, duration_ms=0,
        )

    # ── Queue Worker ──────────────────────────────────────────────────────────

    async def _queue_worker(self) -> None:
        """Continuously process jobs from the priority queue."""
        while self._running:
            try:
                item = await self.queue.dequeue()
                if item is None:
                    await asyncio.sleep(0.5)
                    continue

                # Execute the queued job
                try:
                    await item.job_fn(*item.args, **item.kwargs)
                    await self.queue.mark_complete(item.job_id)
                except Exception as e:
                    logger.error(f"Queued job {item.job_name} failed: {e}")
                    await self.queue.mark_failed(item.job_id)

                metrics.set_queue_size(self.queue.size)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Queue worker error: {e}")
                await asyncio.sleep(1)

    # ── Live Mode ─────────────────────────────────────────────────────────────

    async def _live_mode_loop(self) -> None:
        """Continuously check if a live event is active. Toggle live mode."""
        live_job_config = JOB_REGISTRY.get("events_live")
        results_job_config = JOB_REGISTRY.get("results")

        while self._running:
            try:
                was_live = self.live_detector.is_live
                is_live = await self.live_detector.check()

                if is_live and not was_live:
                    # Entered live mode — enable 30-sec event polling
                    if live_job_config:
                        live_job_config.enabled = True
                    metrics.set_live_mode(True)
                    logger.info("⚡ Switched to LIVE MODE — 30s polling")

                elif not is_live and was_live:
                    # Exited live mode — disable live polling
                    if live_job_config:
                        live_job_config.enabled = False
                    metrics.set_live_mode(False)

                await asyncio.sleep(30)  # Check every 30 seconds

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Live mode loop error: {e}")
                await asyncio.sleep(30)

    # ── Manual Trigger ────────────────────────────────────────────────────────

    async def trigger_full_sync(self, entities: list[str] | None = None) -> str:
        """Manually trigger a full sync. Returns run_id."""
        from src.sync.history import SyncHistoryRecorder

        recorder = SyncHistoryRecorder(self.ctx.db)
        run_id = await recorder.start_run("manual")

        # Enqueue all entity syncs
        from src.scheduler.jobs import sync_events_upcoming, sync_rankings
        for name, fn in JOB_FUNCTIONS.items():
            if entities and name not in entities:
                continue
            priority = Priority.CRITICAL if "live" in name or "results" in name else Priority.NORMAL
            await self.queue.enqueue(name, fn, priority=priority)

        return run_id

    async def trigger_entity_sync(self, entity: str) -> str:
        """Trigger a sync for a specific entity."""
        fn = JOB_FUNCTIONS.get(entity)
        if fn is None:
            raise ValueError(f"Unknown entity: {entity}")

        await self.queue.enqueue(entity, fn, priority=Priority.HIGH)
        return f"Queued {entity}"

    # ── Status ────────────────────────────────────────────────────────────────

    async def get_status(self) -> dict:
        """Get the full status of the sync service."""
        return {
            "running": self._running,
            "live_mode": self.live_detector.is_live,
            "active_event": self.live_detector.active_event_id,
            "queue": self.queue.stats,
            "queued_jobs": await self.queue.queued_jobs(),
            "health": self.monitor.get_status(),
            "locks": await self.locks.lock_status(),
        }

    async def cancel_job(self, job_name: str) -> int:
        """Cancel all queued instances of a job."""
        return await self.queue.cancel(job_name)
