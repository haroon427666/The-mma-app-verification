"""
Execution lock — prevents concurrent sync runs of the same plan/provider.

Critical for distributed deployments: if two backend instances both run
"full_sync/espn" simultaneously, they'll double-insert and create conflicts.

Protocol interface with three planned implementations:
- InMemoryLock: single-instance (default, zero dependencies)
- DatabaseLock: PostgreSQL advisory lock (multi-instance, same DB)
- RedisLock: Redis SETNX (multi-instance, separate Redis)
"""

import asyncio
import logging
from typing import Protocol, runtime_checkable

logger = logging.getLogger(__name__)


# ── Lock key ──────────────────────────────────────────────────────────────────


def lock_key(plan_name: str, provider_slug: str) -> str:
    """Deterministic lock key for a plan/provider combination."""
    return f"sync:{provider_slug}:{plan_name}"


# ── Execution Lock Protocol ───────────────────────────────────────────────────


@runtime_checkable
class ExecutionLock(Protocol):
    """Distributed lock for preventing concurrent sync executions.

    Usage:
        lock = InMemoryLock()
        acquired = await lock.acquire("full_sync", "espn", ttl=3600)
        if acquired:
            try:
                await engine.execute(plan, provider)
            finally:
                await lock.release("full_sync", "espn")
        else:
            logger.info("Another instance is running this sync — skipping")
    """

    async def acquire(
        self, plan_name: str, provider_slug: str, ttl: int = 3600
    ) -> bool:
        """Try to acquire the lock. Returns True if acquired, False if already held.

        Args:
            plan_name: Sync plan name (e.g. "full_sync").
            provider_slug: Provider slug (e.g. "espn").
            ttl: Time-to-live in seconds. Lock auto-releases after this.
                 Prevents orphaned locks from crashed instances.
        """
        ...

    async def release(self, plan_name: str, provider_slug: str) -> None:
        """Release a previously acquired lock. Idempotent."""
        ...

    async def is_locked(self, plan_name: str, provider_slug: str) -> bool:
        """Check if a lock is currently held. Non-blocking."""
        ...


# ── In-Memory Lock (single instance) ──────────────────────────────────────────


class InMemoryLock:
    """Single-instance lock using an in-memory dict + asyncio.

    Simple, zero dependencies, works for single-backend deployments.
    For multi-instance, use DatabaseLock or RedisLock.
    """

    def __init__(self) -> None:
        self._locks: dict[str, asyncio.Lock] = {}

    async def acquire(
        self, plan_name: str, provider_slug: str, ttl: int = 3600
    ) -> bool:
        key = lock_key(plan_name, provider_slug)

        if key not in self._locks:
            self._locks[key] = asyncio.Lock()

        lock = self._locks[key]

        # Non-blocking try — returns immediately
        if lock.locked():
            return False

        await lock.acquire()
        return True

    async def release(self, plan_name: str, provider_slug: str) -> None:
        key = lock_key(plan_name, provider_slug)
        lock = self._locks.get(key)
        if lock and lock.locked():
            lock.release()

    async def is_locked(self, plan_name: str, provider_slug: str) -> bool:
        key = lock_key(plan_name, provider_slug)
        lock = self._locks.get(key)
        return lock.locked() if lock else False
