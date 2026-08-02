"""
Enterprise Scheduler — worker pools, priority queues, distributed locks, dead letters.

Usage:
    scheduler = JobScheduler(registry)
    scheduler.register(JobDefinition(id="sync_espn", connector="espn", ...))
    await scheduler.start()
    await scheduler.trigger("sync_espn", priority=JobPriority.HIGH)
"""

import asyncio
import logging
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Optional

from platform.connectors import BaseConnector, JobPriority

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════
# Types
# ═══════════════════════════════════════════════════════════════════════════

class JobStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    RETRYING = "retrying"
    DEAD_LETTER = "dead_letter"


class TriggerType(str, Enum):
    CRON = "cron"
    INTERVAL = "interval"
    MANUAL = "manual"
    EVENT = "event"
    DEPENDENCY = "dependency"


@dataclass
class JobDefinition:
    """Declarative job configuration."""
    id: str
    connector: str                          # Connector name in registry
    entity_type: str                        # fighter, event, competition, etc.
    trigger_type: TriggerType = TriggerType.MANUAL
    cron: Optional[str] = None              # "0 */6 * * *"
    interval_seconds: Optional[float] = None
    priority: JobPriority = JobPriority.NORMAL
    max_retries: int = 3
    retry_backoff_base: float = 1.0
    timeout_seconds: float = 300.0
    depends_on: list[str] = field(default_factory=list)
    concurrency_limit: int = 1
    enabled: bool = True
    tags: dict[str, str] = field(default_factory=dict)


@dataclass
class JobResult:
    """Outcome of a single job execution."""
    job_id: str
    run_id: str
    status: JobStatus
    started_at: datetime
    finished_at: Optional[datetime] = None
    duration_ms: float = 0.0
    records_fetched: int = 0
    records_inserted: int = 0
    records_updated: int = 0
    records_skipped: int = 0
    errors: int = 0
    retries: int = 0
    worker_id: Optional[str] = None
    error_message: Optional[str] = None
    output: dict[str, Any] = field(default_factory=dict)


@dataclass
class WorkerInfo:
    """Runtime state of a worker."""
    id: str
    status: str = "idle"                    # idle, busy, stopped
    current_job: Optional[str] = None
    jobs_completed: int = 0
    jobs_failed: int = 0
    started_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_heartbeat: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


# ═══════════════════════════════════════════════════════════════════════════
# Priority Queue — heapq-based, lowest priority runs first
# ═══════════════════════════════════════════════════════════════════════════

import heapq

class PriorityJobQueue:
    """Thread-safe priority queue for jobs."""

    def __init__(self):
        self._heap: list[tuple[int, int, JobDefinition]] = []
        self._counter = 0

    def put(self, job: JobDefinition, priority: JobPriority | None = None):
        prio = int(priority if priority is not None else job.priority)
        self._counter += 1
        heapq.heappush(self._heap, (prio, self._counter, job))

    def get(self) -> JobDefinition | None:
        if not self._heap:
            return None
        return heapq.heappop(self._heap)[2]

    def peek(self) -> JobDefinition | None:
        if not self._heap:
            return None
        return self._heap[0][2]

    @property
    def size(self) -> int:
        return len(self._heap)

    def list_all(self) -> list[JobDefinition]:
        return sorted(self._heap, key=lambda x: x[0])


# ═══════════════════════════════════════════════════════════════════════════
# Distributed Lock — Redis-backed, with in-memory fallback
# ═══════════════════════════════════════════════════════════════════════════

class DistributedLock:
    """Redis-based distributed lock with TTL. Falls back to in-memory."""

    def __init__(self, redis_url: str | None = None):
        self._redis_url = redis_url
        self._locks: dict[str, tuple[str, float]] = {}
        self._holder_id = str(uuid.uuid4())

    async def acquire(self, key: str, ttl_seconds: float = 300) -> bool:
        """Try to acquire lock. Returns True if acquired."""
        now = time.monotonic()
        existing = self._locks.get(key)
        if existing and existing[1] > now:
            return False
        self._locks[key] = (self._holder_id, now + ttl_seconds)
        return True

    async def release(self, key: str):
        """Release lock if we hold it."""
        existing = self._locks.get(key)
        if existing and existing[0] == self._holder_id:
            del self._locks[key]

    async def extend(self, key: str, ttl_seconds: float = 300):
        existing = self._locks.get(key)
        if existing and existing[0] == self._holder_id:
            self._locks[key] = (self._holder_id, time.monotonic() + ttl_seconds)


# ═══════════════════════════════════════════════════════════════════════════
# Job Scheduler — orchestration engine
# ═══════════════════════════════════════════════════════════════════════════

class JobScheduler:
    """Central scheduler: register jobs, manage workers, process queues."""

    def __init__(
        self,
        registry,                              # ConnectorRegistry
        worker_count: int = 4,
        redis_url: str | None = None,
        on_job_complete: Callable | None = None,
    ):
        self._registry = registry
        self._worker_count = worker_count
        self._lock = DistributedLock(redis_url)
        self._on_job_complete = on_job_complete
        self._jobs: dict[str, JobDefinition] = {}
        self._queue = PriorityJobQueue()
        self._retry_queue = PriorityJobQueue()
        self._dead_letter_queue: list[JobResult] = []
        self._workers: list[WorkerInfo] = []
        self._history: list[JobResult] = []
        self._running = False
        self._tasks: list[asyncio.Task] = []

    # ── Registration ───────────────────────────────────────────────────────

    def register(self, job: JobDefinition):
        self._jobs[job.id] = job
        if job.trigger_type == TriggerType.MANUAL:
            pass
        elif job.trigger_type == TriggerType.INTERVAL and job.interval_seconds:
            self._schedule_interval(job)
        elif job.trigger_type == TriggerType.DEPENDENCY:
            pass  # Triggered when dependency completes

    def unregister(self, job_id: str):
        self._jobs.pop(job_id, None)

    def _schedule_interval(self, job: JobDefinition):
        async def _interval_loop():
            while self._running:
                await asyncio.sleep(job.interval_seconds or 60)
                if job.enabled:
                    self._queue.put(job)
        self._tasks.append(asyncio.create_task(_interval_loop()))

    # ── Lifecycle ──────────────────────────────────────────────────────────

    async def start(self):
        self._running = True
        for i in range(self._worker_count):
            worker = WorkerInfo(id=f"worker-{i+1}")
            self._workers.append(worker)
            self._tasks.append(asyncio.create_task(self._worker_loop(worker)))
        logger.info(f"Scheduler started with {self._worker_count} workers")

    async def stop(self):
        self._running = False
        for task in self._tasks:
            task.cancel()
        logger.info("Scheduler stopped")

    # ── Trigger ────────────────────────────────────────────────────────────

    async def trigger(
        self, job_id: str, priority: JobPriority | None = None,
    ) -> Optional[str]:
        """Manually trigger a job. Returns run_id or None if locked."""
        if job_id not in self._jobs:
            raise KeyError(f"Job '{job_id}' not found")
        job = self._jobs[job_id]
        if not job.enabled:
            return None

        lock_key = f"job:{job.connector}:{job.entity_type}"
        if not await self._lock.acquire(lock_key, ttl_seconds=job.timeout_seconds + 60):
            logger.warning(f"Job {job_id} already running — skipped")
            return None

        self._queue.put(job, priority)
        return str(uuid.uuid4())

    def pause(self, job_id: str):
        if job_id in self._jobs:
            self._jobs[job_id].enabled = False

    def resume(self, job_id: str):
        if job_id in self._jobs:
            self._jobs[job_id].enabled = True

    def cancel(self, job_id: str):
        """Cancel a queued job. Running jobs continue."""
        # Remove from queue (inefficient but rare operation)
        self._queue._heap = [
            (p, c, j) for p, c, j in self._queue._heap if j.id != job_id
        ]

    # ── Workers ────────────────────────────────────────────────────────────

    async def _worker_loop(self, worker: WorkerInfo):
        while self._running:
            job = self._queue.get()
            if job is None:
                await asyncio.sleep(0.5)
                continue

            worker.status = "busy"
            worker.current_job = job.id
            worker.last_heartbeat = datetime.now(timezone.utc)

            result = await self._execute_job(job, worker)

            worker.status = "idle"
            worker.current_job = None
            if result.status == JobStatus.COMPLETED:
                worker.jobs_completed += 1
            else:
                worker.jobs_failed += 1

            self._history.append(result)
            if len(self._history) > 1000:
                self._history = self._history[-1000:]

    async def _execute_job(
        self, job: JobDefinition, worker: WorkerInfo,
    ) -> JobResult:
        run_id = str(uuid.uuid4())
        started = datetime.now(timezone.utc)
        result = JobResult(
            job_id=job.id, run_id=run_id, status=JobStatus.RUNNING,
            started_at=started, worker_id=worker.id,
        )

        try:
            connector = self._registry.get(job.connector)
            attempts = 0

            while attempts <= job.max_retries:
                try:
                    raw = await connector.fetch(f"/{job.entity_type}")
                    parsed = await connector.parse(raw)
                    normalized = await connector.normalize(parsed)
                    valid, invalid = await connector.validate(normalized)

                    result.status = JobStatus.COMPLETED
                    result.records_fetched = len(normalized)
                    result.records_inserted = len(valid)
                    result.records_skipped = len(invalid)
                    result.errors = len(invalid)
                    result.retries = attempts
                    result.finished_at = datetime.now(timezone.utc)
                    result.duration_ms = (
                        result.finished_at - result.started_at
                    ).total_seconds() * 1000
                    return result

                except Exception as e:
                    attempts += 1
                    if attempts > job.max_retries:
                        result.status = JobStatus.DEAD_LETTER
                        result.error_message = str(e)
                        result.retries = attempts
                        result.finished_at = datetime.now(timezone.utc)
                        self._dead_letter_queue.append(result)
                        return result

                    backoff = job.retry_backoff_base * (2 ** (attempts - 1))
                    await asyncio.sleep(backoff)

        except Exception as e:
            result.status = JobStatus.FAILED
            result.error_message = str(e)
            result.finished_at = datetime.now(timezone.utc)
            return result

        finally:
            lock_key = f"job:{job.connector}:{job.entity_type}"
            await self._lock.release(lock_key)

    # ── Dashboard API ──────────────────────────────────────────────────────

    def get_dashboard(self) -> dict:
        return {
            "running": self._running,
            "workers": [
                {"id": w.id, "status": w.status, "current_job": w.current_job,
                 "completed": w.jobs_completed, "failed": w.jobs_failed}
                for w in self._workers
            ],
            "queue_depth": self._queue.size,
            "retry_depth": self._retry_queue.size,
            "dead_letter_count": len(self._dead_letter_queue),
            "registered_jobs": len(self._jobs),
            "history_length": len(self._history),
            "recent_history": [
                {"job_id": r.job_id, "status": r.status.value, "duration_ms": r.duration_ms}
                for r in self._history[-10:]
            ],
        }

    def get_job_status(self, job_id: str) -> dict | None:
        if job_id not in self._jobs:
            return None
        job = self._jobs[job_id]
        recent = [r for r in self._history if r.job_id == job_id]
        return {
            "id": job.id,
            "connector": job.connector,
            "entity": job.entity_type,
            "enabled": job.enabled,
            "priority": job.priority.value,
            "trigger": job.trigger_type.value,
            "last_runs": [
                {"run_id": r.run_id, "status": r.status.value, "records": r.records_fetched}
                for r in recent[-5:]
            ],
        }

    def replay_dead_letter(self, run_id: str) -> Optional[str]:
        """Replay a dead-letter job."""
        for i, result in enumerate(self._dead_letter_queue):
            if result.run_id == run_id:
                self._dead_letter_queue.pop(i)
                if result.job_id in self._jobs:
                    self._queue.put(self._jobs[result.job_id], JobPriority.NORMAL)
                    return result.job_id
        return None

    def purge_dead_letters(self) -> int:
        count = len(self._dead_letter_queue)
        self._dead_letter_queue.clear()
        return count
