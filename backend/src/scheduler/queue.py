"""Priority Queue — live data always wins.

Job priority ordering:
    LIVE     = 0  (30-sec polling during active events)
    CRITICAL = 1  (today's events, in-progress fights)
    HIGH     = 2  (upcoming events, rankings)
    NORMAL   = 3  (historical fighters, enrichment)
    LOW      = 4  (cleanup, media refresh)

A priority-0 LIVE job preempts a priority-3 NORMAL job.
"""

import asyncio
import heapq
import logging
import time
from dataclasses import dataclass, field
from enum import IntEnum
from typing import Any, Callable, Optional

logger = logging.getLogger(__name__)


class Priority(IntEnum):
    LIVE = 0       # Active event polling
    CRITICAL = 1    # Today's events, in-progress fights
    HIGH = 2        # Upcoming events, rankings
    NORMAL = 3      # Historical fighters, stats
    LOW = 4         # Cleanup, media refresh


@dataclass(order=True)
class QueueItem:
    """Heap-ordered job. Lower priority number = higher urgency."""
    priority: int
    enqueued_at: float = field(compare=False)
    job_id: str = field(compare=False)
    job_name: str = field(compare=False)
    job_fn: Callable = field(compare=False, repr=False)
    args: tuple = field(default_factory=tuple, compare=False, repr=False)
    kwargs: dict = field(default_factory=dict, compare=False, repr=False)


class PriorityQueue:
    """Thread-safe priority heap for sync jobs.

    Items are dequeued in priority order. LIVE (0) always before LOW (4).
    """

    def __init__(self, max_concurrent: int = 2):
        self._heap: list[QueueItem] = []
        self._lock = asyncio.Lock()
        self._running: set[str] = set()
        self._max_concurrent = max_concurrent
        self._total_enqueued = 0
        self._total_completed = 0
        self._total_failed = 0

    @property
    def size(self) -> int:
        return len(self._heap)

    @property
    def running_count(self) -> int:
        return len(self._running)

    @property
    def stats(self) -> dict:
        return {
            "queued": self.size,
            "running": self.running_count,
            "total_enqueued": self._total_enqueued,
            "total_completed": self._total_completed,
            "total_failed": self._total_failed,
        }

    async def enqueue(
        self, job_name: str, fn: Callable, priority: Priority = Priority.NORMAL,
        *args, **kwargs,
    ) -> str:
        """Add a job to the queue. Returns job_id."""
        import uuid
        job_id = str(uuid.uuid4())[:12]

        item = QueueItem(
            priority=int(priority),
            enqueued_at=time.monotonic(),
            job_id=job_id,
            job_name=job_name,
            job_fn=fn,
            args=args,
            kwargs=kwargs,
        )

        async with self._lock:
            heapq.heappush(self._heap, item)
            self._total_enqueued += 1

        logger.debug(f"Enqueued {job_name} [{job_id}] priority={priority.name}")
        return job_id

    async def dequeue(self) -> Optional[QueueItem]:
        """Pop the highest-priority job. Returns None if at capacity or queue empty."""
        async with self._lock:
            if not self._heap:
                return None
            if self.running_count >= self._max_concurrent:
                return None  # At concurrency limit

            item = heapq.heappop(self._heap)
            self._running.add(item.job_id)
            return item

    async def mark_complete(self, job_id: str) -> None:
        async with self._lock:
            self._running.discard(job_id)
            self._total_completed += 1

    async def mark_failed(self, job_id: str) -> None:
        async with self._lock:
            self._running.discard(job_id)
            self._total_failed += 1

    async def cancel(self, job_name: str) -> int:
        """Remove all queued jobs with this name. Returns count removed."""
        async with self._lock:
            before = len(self._heap)
            self._heap = [item for item in self._heap if item.job_name != job_name]
            heapq.heapify(self._heap)
            removed = before - len(self._heap)
            logger.info(f"Cancelled {removed} queued '{job_name}' jobs")
            return removed

    async def queued_jobs(self) -> list[dict]:
        """List all queued jobs (for dashboard)."""
        async with self._lock:
            return [
                {"job_id": item.job_id, "name": item.job_name,
                 "priority": Priority(item.priority).name}
                for item in sorted(self._heap)
            ]
