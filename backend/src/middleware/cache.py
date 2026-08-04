"""Transparent async cache (ADR-003) — memory and Redis backends.

Services depend on ``CacheManager`` and never know whether values come from
memory or Redis. Redis failures degrade to cache-miss (serve-through): caching
never blocks or breaks the request path.
"""

import functools
import hashlib
import json
import logging
import time
from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import Any

from src.config import settings

logger = logging.getLogger(__name__)

CACHE_KEY_PREFIX = "mma:cache:"


def _record_cache(hit: bool) -> None:
    """Record cache hit/miss to Prometheus (safe — no-ops before setup())."""
    try:
        from src.monitoring.scheduler_metrics import SchedulerMetricsCollector
        SchedulerMetricsCollector().record_cache(hit)
    except Exception:
        pass


class CacheManager(ABC):
    """Async cache backend interface with TTL and stats."""

    @abstractmethod
    async def get(self, key: str) -> Any | None:
        """Return the cached value for ``key``, or None on miss/expiry."""

    @abstractmethod
    async def set(self, key: str, value: Any, ttl_seconds: int) -> None:
        """Store ``value`` under ``key`` for ``ttl_seconds``."""

    @abstractmethod
    async def invalidate(self, key_prefix: str) -> int:
        """Delete all keys starting with ``key_prefix``. Returns count."""

    @abstractmethod
    def stats(self) -> dict[str, int | float | str]:
        """Hits/misses/hit_rate plus backend info."""

    def _make_key(self, *args: Any, **kwargs: Any) -> str:
        raw = json.dumps({"args": args, "kwargs": kwargs}, sort_keys=True, default=str)
        return hashlib.sha256(raw.encode()).hexdigest()[:16]


class MemoryCacheManager(CacheManager):
    """In-process cache with TTL. Used in dev/tests or when Redis is absent."""

    def __init__(self) -> None:
        self._store: dict[str, tuple[Any, float]] = {}
        self._hits = 0
        self._misses = 0

    async def get(self, key: str) -> Any | None:
        if key in self._store:
            value, expires_at = self._store[key]
            if time.monotonic() < expires_at:
                self._hits += 1
                _record_cache(True)
                return value
            del self._store[key]
        self._misses += 1
        _record_cache(False)
        return None

    async def set(self, key: str, value: Any, ttl_seconds: int) -> None:
        self._store[key] = (value, time.monotonic() + ttl_seconds)

    async def invalidate(self, key_prefix: str) -> int:
        removed = 0
        for key in list(self._store.keys()):
            if key.startswith(key_prefix):
                del self._store[key]
                removed += 1
        return removed

    def stats(self) -> dict[str, int | float | str]:
        total = self._hits + self._misses
        return {
            "backend": "memory",
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": self._hits / total if total > 0 else 0,
            "store_size": len(self._store),
        }


class RedisCacheManager(CacheManager):
    """Redis-backed cache. JSON serialization (no pickle), TTL via SETEX.

    Every operation is guarded: on connection errors the manager degrades to
    serve-through (miss) and logs at most once per minute.
    """

    def __init__(self, redis_client: Any) -> None:
        self._redis = redis_client
        self._hits = 0
        self._misses = 0
        self._degraded = False
        self._last_error_logged = 0.0

    def _serialize(self, value: Any) -> str:
        return json.dumps(value, sort_keys=True, default=str)

    def _deserialize(self, raw: str) -> Any:
        return json.loads(raw)

    def _note_error(self) -> None:
        self._degraded = True
        now = time.monotonic()
        if now - self._last_error_logged > 60:
            logger.warning("Redis cache unavailable — serving through (cache-miss)")
            self._last_error_logged = now

    def _note_success(self) -> None:
        self._degraded = False

    async def get(self, key: str) -> Any | None:
        try:
            raw = await self._redis.get(key)
        except Exception:
            self._note_error()
            self._misses += 1
            _record_cache(False)
            return None
        self._note_success()
        if raw is None:
            self._misses += 1
            _record_cache(False)
            return None
        self._hits += 1
        try:
            value = self._deserialize(raw)
        except ValueError:
            logger.debug("Cache corruption — ignoring value", exc_info=True)
            self._misses += 1
            _record_cache(False)
            return None
        _record_cache(True)
        return value

    async def set(self, key: str, value: Any, ttl_seconds: int) -> None:
        try:
            await self._redis.setex(key, ttl_seconds, self._serialize(value))
            self._note_success()
        except Exception:
            self._note_error()

    async def invalidate(self, key_prefix: str) -> int:
        try:
            pattern = f"{key_prefix}*"
            keys = [k async for k in self._redis.scan_iter(match=pattern)]
            if not keys:
                return 0
            deleted: int = await self._redis.delete(*keys)
            self._note_success()
            return deleted
        except Exception:
            self._note_error()
            return 0

    def stats(self) -> dict[str, int | float | str]:
        total = self._hits + self._misses
        return {
            "backend": "redis",
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": self._hits / total if total > 0 else 0,
            "degraded": self._degraded,
        }


# ── Singleton resolution ────────────────────────────────────────────────────

_built_cache: CacheManager | None = None


def build_cache_manager() -> CacheManager:
    """Pick the backend: Redis when configured, memory otherwise."""
    if not settings.cache_enabled or not settings.redis_url:
        return MemoryCacheManager()
    from src.middleware.redis import get_redis

    client = get_redis()
    if client is None:
        return MemoryCacheManager()
    return RedisCacheManager(client)


def default_cache() -> CacheManager:
    """Process-wide cache backend. Replaces itself via ``reset_cache_manager``."""
    global _built_cache
    if _built_cache is None:
        _built_cache = build_cache_manager()
    return _built_cache


def reset_cache_manager() -> None:
    """Drop the cached backend decision (used by tests and config reload)."""
    global _built_cache
    _built_cache = None


def cached(
    ttl: int = 300,
    cache: CacheManager | None = None,
) -> Callable[..., Any]:
    """Decorator: cache async function results with TTL.

    Usage:
        @cached(ttl=600)
        async def get_rankings() -> list[Ranking]:
            ...

        # Invalidation: wrapper.cache.invalidate("get_rankings")
    """
    backend = cache if cache is not None else default_cache()

    def decorator(fn: Callable[..., Any]) -> Callable[..., Any]:
        @functools.wraps(fn)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            key = f"{CACHE_KEY_PREFIX}{fn.__name__}:{backend._make_key(*args, **kwargs)}"
            cached_val = await backend.get(key)
            if cached_val is not None:
                return cached_val
            result = await fn(*args, **kwargs)
            await backend.set(key, result, ttl)
            return result

        setattr(wrapper, "cache", backend)  # noqa: B010  # Expose for invalidation
        return wrapper

    return decorator