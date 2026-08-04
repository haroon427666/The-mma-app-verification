"""Tests for endpoint response caching (src/api/cache.py)."""

import json

import pytest
from fastapi import Request

from src.api import cache as api_cache
from src.middleware.cache import MemoryCacheManager


def _req(if_none_match: str | None = None) -> Request:
    headers = []
    if if_none_match:
        headers = [(b"if-none-match", if_none_match.encode())]
    scope = {
        "type": "http",
        "method": "GET",
        "path": "/",
        "headers": headers,
        "scheme": "http",
        "server": ("test", 80),
        "client": ("127.0.0.1", 1234),
        "query_string": b"",
    }
    return Request(scope)


@pytest.fixture
def mem_cache(monkeypatch: pytest.MonkeyPatch) -> MemoryCacheManager:
    mem = MemoryCacheManager()
    monkeypatch.setattr(api_cache, "default_cache", lambda: mem)
    return mem


@pytest.mark.asyncio
async def test_miss_populates_cache_and_returns_200(mem_cache: MemoryCacheManager) -> None:
    calls = 0

    async def loader() -> dict:
        nonlocal calls
        calls += 1
        return {"id": "evt-1", "name": "UFC 400"}

    resp = await api_cache.cached_json_response(_req(), "events:detail:evt-1", ttl=300, loader=loader)
    assert resp.status_code == 200
    assert calls == 1
    assert json.loads(resp.body)["name"] == "UFC 400"
    assert resp.headers["Cache-Control"] == "public, max-age=300"
    assert resp.headers["ETag"].startswith('"')
    assert await mem_cache.get("mma:api:events:detail:evt-1") == {"id": "evt-1", "name": "UFC 400"}


@pytest.mark.asyncio
async def test_hit_skips_loader(mem_cache: MemoryCacheManager) -> None:
    await mem_cache.set("mma:api:fighters:detail:abc", {"id": "abc"}, 3600)
    calls = 0

    async def loader() -> dict:
        nonlocal calls
        calls += 1
        return {"id": "wrong"}

    resp = await api_cache.cached_json_response(_req(), "fighters:detail:abc", ttl=3600, loader=loader)
    assert resp.status_code == 200
    assert calls == 0
    assert json.loads(resp.body) == {"id": "abc"}


@pytest.mark.asyncio
async def test_hit_returns_304_when_etag_matches(mem_cache: MemoryCacheManager) -> None:
    payload = {"id": "abc", "name": "UFC 400"}
    await mem_cache.set("mma:api:events:detail:abc", payload, 300)

    async def loader() -> dict:
        raise AssertionError("loader must not run on cache hit")

    first = await api_cache.cached_json_response(_req(), "events:detail:abc", ttl=300, loader=loader)
    etag = first.headers["ETag"]
    second = await api_cache.cached_json_response(_req(if_none_match=etag), "events:detail:abc", ttl=300, loader=loader)
    assert second.status_code == 304
    assert b"{" not in second.body


@pytest.mark.asyncio
async def test_mismatch_etag_returns_200(mem_cache: MemoryCacheManager) -> None:
    await mem_cache.set("mma:api:events:detail:abc", {"id": "abc"}, 300)

    async def loader() -> dict:
        return {"id": "abc"}

    resp = await api_cache.cached_json_response(_req(if_none_match='"stale"'), "events:detail:abc", ttl=300, loader=loader)
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_ttl_capped_max_age_at_one_hour(mem_cache: MemoryCacheManager) -> None:
    async def loader() -> dict:
        return {"id": "x"}

    resp = await api_cache.cached_json_response(_req(), "promotions:list", ttl=86400, loader=loader)
    assert resp.headers["Cache-Control"] == "public, max-age=3600"


def test_cache_key_drops_none_and_empty() -> None:
    assert api_cache.cache_key("fighters:list", 20, None, "", "active") == "fighters:list:20:active"
