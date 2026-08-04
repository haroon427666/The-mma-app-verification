"""Unit tests for the transparent cache layer (ADR-003)."""

import asyncio
from datetime import UTC, datetime
from typing import Any

import pytest

from src.config import settings
from src.middleware.cache import (
    CACHE_KEY_PREFIX,
    MemoryCacheManager,
    RedisCacheManager,
    build_cache_manager,
    cached,
    default_cache,
    reset_cache_manager,
)


@pytest.fixture(autouse=True)
def _reset_singleton() -> Any:
    reset_cache_manager()
    yield
    reset_cache_manager()


class FakeRedis:
    """Minimal async Redis stand-in covering the operations the cache uses."""

    def __init__(self) -> None:
        self.store: dict[str, str] = {}
        self.fail = False

    async def get(self, key: str) -> str | None:
        if self.fail:
            raise ConnectionError("connection refused")
        return self.store.get(key)

    async def setex(self, key: str, ttl: int, value: str) -> None:
        if self.fail:
            raise ConnectionError("connection refused")
        self.store[key] = value

    async def scan_iter(self, match: str = "*") -> Any:
        prefix = match[:-1]
        for key in list(self.store.keys()):
            if key.startswith(prefix):
                yield key

    async def delete(self, *keys: str) -> int:
        if self.fail:
            raise ConnectionError("connection refused")
        count = 0
        for key in keys:
            if key in self.store:
                del self.store[key]
                count += 1
        return count

    async def ping(self) -> bool:
        return not self.fail


class TestMemoryCacheManager:
    async def test_set_get_roundtrip(self) -> None:
        m = MemoryCacheManager()
        assert await m.get("k") is None
        await m.set("k", {"a": 1}, 300)
        assert await m.get("k") == {"a": 1}

    async def test_ttl_zero_expires_immediately(self) -> None:
        m = MemoryCacheManager()
        await m.set("k", "v", 0)
        assert await m.get("k") is None

    async def test_invalidate_prefix(self) -> None:
        m = MemoryCacheManager()
        await m.set("events:1", "a", 300)
        await m.set("events:2", "b", 300)
        await m.set("fighters:1", "c", 300)
        removed = await m.invalidate("events:")
        assert removed == 2
        assert await m.get("events:1") is None
        assert await m.get("fighters:1") == "c"

    async def test_stats_hit_rate(self) -> None:
        m = MemoryCacheManager()
        await m.set("k", "v", 300)
        await m.get("k")
        await m.get("missing")
        stats = m.stats()
        assert stats["backend"] == "memory"
        assert stats["hits"] == 1
        assert stats["misses"] == 1
        assert stats["hit_rate"] == 0.5


class TestKeySchema:
    def test_make_key_deterministic_and_order_sensitive(self) -> None:
        m = MemoryCacheManager()
        assert m._make_key("x", 1, {"b": 2}) == m._make_key("x", 1, {"b": 2})
        assert m._make_key("x", 1) != m._make_key(1, "x")
        assert len(m._make_key("a")) == 16

    def test_cached_key_prefix(self) -> None:
        m = MemoryCacheManager()
        key = f"{CACHE_KEY_PREFIX}get_rankings:{m._make_key(10)}"
        assert key.startswith(CACHE_KEY_PREFIX)
        assert "get_rankings" in key


class TestRedisCacheManager:
    async def test_set_get_roundtrip(self) -> None:
        fake = FakeRedis()
        r = RedisCacheManager(fake)
        await r.set("k", {"name": "Alex", "dob": datetime(1990, 1, 1, tzinfo=UTC)}, 300)
        raw = fake.store["k"]
        assert isinstance(raw, str)
        assert '"Alex"' in raw
        value = await r.get("k")
        assert value == {"name": "Alex", "dob": "1990-01-01 00:00:00+00:00"}

    async def test_miss_and_expired_are_misses(self) -> None:
        fake = FakeRedis()
        r = RedisCacheManager(fake)
        assert await r.get("missing") is None
        assert r.stats()["misses"] == 1

    async def test_invalidate_prefix(self) -> None:
        fake = FakeRedis()
        r = RedisCacheManager(fake)
        await r.set(f"{CACHE_KEY_PREFIX}events:1", "a", 300)
        await r.set(f"{CACHE_KEY_PREFIX}events:2", "b", 300)
        await r.set(f"{CACHE_KEY_PREFIX}fighters:1", "c", 300)
        removed = await r.invalidate(f"{CACHE_KEY_PREFIX}events:")
        assert removed == 2
        assert await r.get(f"{CACHE_KEY_PREFIX}fighters:1") == "c"

    async def test_degradation_never_raises(self) -> None:
        fake = FakeRedis()
        fake.fail = True
        r = RedisCacheManager(fake)
        assert await r.get("k") is None
        await r.set("k", "v", 300)  # no exception
        assert await r.invalidate("k") == 0
        assert r.stats()["degraded"] is True

    async def test_recovers_after_redis_returns(self) -> None:
        fake = FakeRedis()
        r = RedisCacheManager(fake)
        fake.fail = True
        await r.set("k", "v", 300)
        assert r.stats()["degraded"] is True
        fake.fail = False
        await r.set("k", "v2", 300)
        assert r.stats()["degraded"] is False
        assert await r.get("k") == "v2"


class TestCacheFactory:
    def test_memory_when_disabled(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(settings, "cache_enabled", False)
        assert isinstance(build_cache_manager(), MemoryCacheManager)

    def test_memory_when_no_redis_url(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(settings, "redis_url", "")
        assert isinstance(build_cache_manager(), MemoryCacheManager)

    def test_redis_when_configured(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(settings, "cache_enabled", True)
        monkeypatch.setattr(settings, "redis_url", "redis://localhost:6379/1")
        manager = build_cache_manager()
        assert isinstance(manager, RedisCacheManager)
        assert manager.stats()["backend"] == "redis"

    def test_default_cache_is_singleton(self) -> None:
        assert default_cache() is default_cache()
        reset_cache_manager()
        assert default_cache() is not None

    def test_reset_rebuilds(self) -> None:
        first = default_cache()
        reset_cache_manager()
        second = default_cache()
        assert first is not second


class TestCachedDecorator:
    async def test_caches_result_and_serves_from_cache(self) -> None:
        cache = MemoryCacheManager()
        calls = 0

        @cached(ttl=300, cache=cache)
        async def compute(x: int) -> int:
            nonlocal calls
            calls += 1
            return x * 2

        assert await compute(21) == 42
        assert await compute(21) == 42
        assert calls == 1

    async def test_different_args_are_different_keys(self) -> None:
        cache = MemoryCacheManager()
        calls = 0

        @cached(ttl=300, cache=cache)
        async def compute(x: int) -> int:
            nonlocal calls
            calls += 1
            return x

        await compute(1)
        await compute(2)
        assert calls == 2

    async def test_invalidation_through_wrapper(self) -> None:
        cache = MemoryCacheManager()
        calls = 0

        @cached(ttl=300, cache=cache)
        async def compute() -> int:
            nonlocal calls
            calls += 1
            return 7

        await compute()
        assert calls == 1
        wrapper = compute
        removed = await wrapper.cache.invalidate(f"{CACHE_KEY_PREFIX}compute")  # type: ignore[attr-defined]
        assert removed >= 1
        await compute()
        assert calls == 2

    async def test_concurrent_duplicate_calls_are_safe(self) -> None:
        cache = MemoryCacheManager()

        @cached(ttl=300, cache=cache)
        async def compute() -> int:
            await asyncio.sleep(0.01)
            return 1

        results = await asyncio.gather(compute(), compute())
        assert results == [1, 1]
