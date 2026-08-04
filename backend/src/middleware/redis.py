"""Shared async Redis client — single process-wide connection pool.

Cache, scheduler locks, job queue, and health checks all share one client so
connection limits, decode settings, and timeouts stay consistent.

Everything is optional at runtime: if ``REDIS_URL`` is not configured or the
server is unreachable, callers degrade gracefully (cache-miss, lock-fail).
"""

import logging
from typing import Any

from redis import asyncio as aioredis

from src.config import settings

logger = logging.getLogger(__name__)

_redis_client: Any | None = None


def get_redis() -> Any | None:
    """Return the process-wide Redis client, or ``None`` if Redis is disabled."""
    global _redis_client
    if not settings.redis_url:
        return None
    if _redis_client is None:
        _redis_client = aioredis.from_url(
            settings.redis_url,
            decode_responses=True,
            socket_connect_timeout=2.0,
            socket_timeout=2.0,
            socket_keepalive=True,
        )
        logger.info(f"Redis client initialized: {settings.redis_url.split('@')[-1]}")
    return _redis_client


async def close_redis() -> None:
    """Close the shared client. Call once, at application shutdown."""
    global _redis_client
    if _redis_client is not None:
        try:
            await _redis_client.aclose()
        except Exception:  # pragma: no cover - redis teardown is best-effort
            logger.debug("Redis client close failed", exc_info=True)
        _redis_client = None


async def ping_redis() -> bool:
    """Check Redis connectivity. Never raises."""
    client = get_redis()
    if client is None:
        return False
    try:
        return bool(await client.ping())
    except Exception:
        return False