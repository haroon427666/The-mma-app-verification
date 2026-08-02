"""Redis cache middleware + utility."""

import functools
import hashlib
import json
import logging
from typing import Any, Callable, Optional

logger = logging.getLogger(__name__)


class CacheManager:
    """Simple async cache with TTL. Production: replace with Redis."""

    def __init__(self):
        self._store: dict[str, tuple[Any, float]] = {}
        self._hits = 0
        self._misses = 0

    def _make_key(self, *args, **kwargs) -> str:
        raw = json.dumps({"args": args, "kwargs": kwargs}, sort_keys=True, default=str)
        return hashlib.sha256(raw.encode()).hexdigest()[:16]

    async def get(self, key: str) -> Optional[Any]:
        if key in self._store:
            value, expires_at = self._store[key]
            import time
            if time.monotonic() < expires_at:
                self._hits += 1
                return value
            del self._store[key]
        self._misses += 1
        return None

    async def set(self, key: str, value: Any, ttl_seconds: int = 300) -> None:
        import time
        self._store[key] = (value, time.monotonic() + ttl_seconds)

    async def invalidate(self, key_prefix: str) -> int:
        removed = 0
        for key in list(self._store.keys()):
            if key.startswith(key_prefix):
                del self._store[key]
                removed += 1
        return removed

    @property
    def stats(self) -> dict:
        total = self._hits + self._misses
        return {
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": self._hits / total if total > 0 else 0,
            "store_size": len(self._store),
        }


# Production: replace with RedisCacheManager
# class RedisCacheManager(CacheManager):
#     def __init__(self, redis_url: str):
#         import redis.asyncio as aioredis
#         self._redis = aioredis.from_url(redis_url)
#     ...


def cached(ttl: int = 300):
    """Decorator: cache function results with TTL.

    Usage:
        @cached(ttl=600)
        async def get_rankings():
            ...
    """
    def decorator(fn: Callable):
        cache = CacheManager()

        @functools.wraps(fn)
        async def wrapper(*args, **kwargs):
            key = f"{fn.__name__}:{cache._make_key(*args, **kwargs)}"
            cached_val = await cache.get(key)
            if cached_val is not None:
                return cached_val
            result = await fn(*args, **kwargs)
            await cache.set(key, result, ttl)
            return result

        wrapper.cache = cache  # Expose for invalidation
        return wrapper
    return decorator
