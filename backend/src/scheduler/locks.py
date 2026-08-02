"""Distributed Locking — Redis-backed mutex for sync jobs.

Prevents duplicate execution across multiple worker processes.
Locks auto-expire so a crashed worker doesn't hold locks forever.
"""

import asyncio
import logging
import time
import uuid
from contextlib import asynccontextmanager
from typing import Optional

logger = logging.getLogger(__name__)


class RedisLock:
    """Redis-backed distributed lock with TTL-based expiry.

    If a worker crashes, the lock auto-expires after `ttl_seconds`,
    allowing another worker to take over.

    Usage:
        lock = RedisLock(redis, "sync:fighters")
        async with lock:
            await sync_fighters()
    """

    def __init__(self, redis, name: str, ttl_seconds: int = 300):
        self._redis = redis
        self._name = f"mma:lock:{name}"
        self._ttl = ttl_seconds
        self._token: Optional[str] = None

    async def acquire(self, timeout: float = 0) -> bool:
        """Try to acquire the lock. Returns True on success.

        Args:
            timeout: Seconds to wait. 0 = try once, don't wait.
        """
        self._token = str(uuid.uuid4())
        deadline = time.monotonic() + timeout

        while True:
            acquired = await self._redis.set(
                self._name, self._token, nx=True, ex=self._ttl,
            )
            if acquired:
                logger.debug(f"Lock acquired: {self._name}")
                return True

            if timeout == 0 or time.monotonic() >= deadline:
                return False

            await asyncio.sleep(0.1)

    async def release(self) -> bool:
        """Release the lock. Only succeeds if we still own it."""
        if self._token is None:
            return False

        # Lua script: delete only if token matches (prevents deleting someone else's lock)
        script = """
        if redis.call("GET", KEYS[1]) == ARGV[1] then
            return redis.call("DEL", KEYS[1])
        else
            return 0
        end
        """
        result = await self._redis.eval(script, 1, self._name, self._token)
        released = result == 1
        if released:
            logger.debug(f"Lock released: {self._name}")
        self._token = None
        return released

    async def extend(self, extra_seconds: int = 60) -> bool:
        """Extend the lock TTL. Useful for long-running jobs."""
        if self._token is None:
            return False
        current = await self._redis.get(self._name)
        if current and current.decode() == self._token:
            await self._redis.expire(self._name, self._ttl + extra_seconds)
            return True
        return False

    async def is_locked(self) -> bool:
        return await self._redis.exists(self._name) > 0

    async def __aenter__(self):
        if not await self.acquire():
            raise LockAcquisitionError(f"Could not acquire lock: {self._name}")
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.release()
        return False


class LockAcquisitionError(Exception):
    pass


class LockManager:
    """Manages named locks for all sync jobs."""

    def __init__(self, redis):
        self._redis = redis
        self._locks: dict[str, RedisLock] = {}

    def get(self, job_name: str, ttl: int = 300) -> RedisLock:
        if job_name not in self._locks:
            self._locks[job_name] = RedisLock(self._redis, job_name, ttl)
        return self._locks[job_name]

    async def lock_status(self) -> dict[str, bool]:
        """Report which jobs are currently locked."""
        status = {}
        for name, lock in self._locks.items():
            status[name] = await lock.is_locked()
        return status
