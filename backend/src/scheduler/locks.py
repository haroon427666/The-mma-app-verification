"""Distributed Locking — Redis-backed mutex for sync jobs.

Prevents duplicate execution across multiple worker processes.
Locks auto-expire so a crashed worker doesn't hold locks forever.

Degraded mode (T07): when the Redis backend is unreachable, lock
acquisition is SKIPPED — jobs run without cross-worker coordination
instead of crashing. Documented tradeoff: two workers could double-run
a job while Redis is down.
"""

import asyncio
import logging
import time
import uuid
from types import TracebackType
from typing import Any, Self

from redis.exceptions import RedisError

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

    def __init__(self, redis: Any, name: str, ttl_seconds: int = 300):
        self._redis = redis
        self._name = f"mma:lock:{name}"
        self._ttl = ttl_seconds
        self._token: str | None = None

    async def acquire(self, timeout: float = 0) -> bool:
        """Try to acquire the lock. Returns True on success.

        Args:
            timeout: Seconds to wait. 0 = try once, don't wait.

        Degraded mode: if Redis is unreachable the lock is skipped and True
        is returned — the job runs without cross-worker coordination rather
        than crashing the scheduler loop.
        """
        if self._redis is None:
            # No Redis backend — cannot coordinate; skip rather than crash.
            logger.debug(f"Lock '{self._name}' skipped — Redis not configured")
            return False

        self._token = str(uuid.uuid4())
        deadline = time.monotonic() + timeout

        try:
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
        except (RedisError, OSError) as e:
            logger.warning(
                f"Lock '{self._name}' backend unavailable ({e}) — "
                f"running degraded without cross-worker coordination"
            )
            return True

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
        try:
            result = await self._redis.eval(script, 1, self._name, self._token)
        except (RedisError, OSError) as e:
            logger.warning(
                f"Lock '{self._name}' release failed — Redis unavailable ({e})"
            )
            self._token = None
            return False
        released: bool = result == 1
        if released:
            logger.debug(f"Lock released: {self._name}")
        self._token = None
        return released

    async def extend(self, extra_seconds: int = 60) -> bool:
        """Extend the lock TTL. Useful for long-running jobs."""
        if self._redis is None or self._token is None:
            return False
        try:
            current = await self._redis.get(self._name)
            if current is not None and current == self._token:
                await self._redis.expire(self._name, self._ttl + extra_seconds)
                return True
        except (RedisError, OSError) as e:
            logger.warning(
                f"Lock '{self._name}' extend failed — Redis unavailable ({e})"
            )
            return False
        return False

    async def is_locked(self) -> bool:
        if self._redis is None:
            return False
        try:
            exists: int = await self._redis.exists(self._name)
            return exists > 0
        except (RedisError, OSError) as e:
            logger.warning(
                f"Lock '{self._name}' status check failed — Redis unavailable ({e})"
            )
            return False

    async def __aenter__(self) -> Self:
        if not await self.acquire():
            raise LockAcquisitionError(f"Could not acquire lock: {self._name}")
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> bool:
        await self.release()
        return False


class LockAcquisitionError(Exception):
    pass


class LockManager:
    """Manages named locks for all sync jobs."""

    def __init__(self, redis: Any):
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
