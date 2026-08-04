"""Endpoint-level response caching for public list endpoints.

Combines the CacheManager backend (memory/Redis, degrade-to-serve-through) with
ETag/304 headers: a cache hit skips the DB query entirely and still returns a
valid ETag for revalidation.
"""

import logging
from collections.abc import Awaitable, Callable
from typing import Any

from fastapi import Request
from fastapi.responses import JSONResponse

from src.api.etag import conditional_json_response
from src.middleware.cache import default_cache

logger = logging.getLogger(__name__)

API_CACHE_PREFIX = "mma:api:"


async def cached_json_response(
    request: Request,
    cache_key: str,
    ttl: int,
    loader: Callable[[], Awaitable[Any]],
) -> JSONResponse:
    """Return ``loader()`` result, cached under ``cache_key`` for ``ttl`` seconds.

    Cache misses populate the backend; hits bypass the DB. Either way the
    response carries ETag + Cache-Control and honors If-None-Match (304).
    """
    key = f"{API_CACHE_PREFIX}{cache_key}"
    cache = default_cache()
    cached = await cache.get(key)
    if cached is not None:
        return conditional_json_response(request, cached, max_age=min(ttl, 3600))
    payload = await loader()
    await cache.set(key, payload, ttl)
    return conditional_json_response(request, payload, max_age=min(ttl, 3600))


def cache_key(*parts: Any) -> str:
    """Join cache key parts, dropping None values."""
    return ":".join(str(p) for p in parts if p is not None and p != "")
