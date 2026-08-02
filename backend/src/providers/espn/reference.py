"""
ESPN $ref Reference Resolver.

ESPN's API uses $ref extensively. Instead of embedding nested objects,
it returns links that must be followed:

    "athlete": {"$ref": "https://.../athletes/12345"}

This module provides:
1. A caching resolver (avoids following the same $ref multiple times in one sync run)
2. Utility functions to extract $ref URLs, resolve lists of $refs, etc.
"""

import logging
from typing import Any

from src.providers.espn.client import ESPNClient

logger = logging.getLogger(__name__)


# ── Utility Functions ──────────────────────────────────────────────────────────


def is_ref(obj: Any) -> bool:
    """Check if an object is an ESPN $ref."""
    return isinstance(obj, dict) and "$ref" in obj


def extract_ref(obj: Any) -> str | None:
    """Extract the $ref URL from an object, or None if it's not a $ref."""
    if is_ref(obj):
        return obj["$ref"]
    return None


def extract_id_from_ref(ref_url: str) -> str:
    """Extract the numeric or string ID from a $ref URL.

    Strips query parameters (?lang=en&region=us) before extracting.

    Examples:
        ".../athletes/12345" → "12345"
        ".../leagues/9?lang=en&region=us" → "9"
        ".../venues/3115?lang=en&region=us" → "3115"
    """
    # Strip query string
    url = ref_url.split("?")[0]
    return url.rstrip("/").rsplit("/", 1)[-1]


# ── Resolver ───────────────────────────────────────────────────────────────────


class RefResolver:
    """Cached $ref resolver.

    During a sync run, the same entities are often referenced multiple times
    (e.g. the same fighter appears in multiple competitions). This resolver
    caches resolved data within one run to avoid redundant HTTP calls.

    The cache is intentionally NOT shared across sync runs — ESPN data may
    change between runs, so we want fresh data each time.
    """

    def __init__(self, client: ESPNClient) -> None:
        self._client = client
        self._cache: dict[str, dict[str, Any]] = {}
        self._hits = 0
        self._misses = 0

    async def resolve(self, ref_obj: Any) -> dict[str, Any]:
        """Resolve a $ref object to its full JSON payload.

        Args:
            ref_obj: Either a $ref dict: {"$ref": "https://..."}
                     Or a regular object (returned as-is).

        Returns:
            The full JSON payload, or the original object if it wasn't a $ref.
        """
        if not is_ref(ref_obj):
            return ref_obj

        ref_url: str = ref_obj["$ref"]

        if ref_url in self._cache:
            self._hits += 1
            return self._cache[ref_url]

        self._misses += 1
        logger.debug(f"Resolving $ref: {ref_url}")
        data = await self._client.resolve_ref(ref_url)
        self._cache[ref_url] = data
        return data

    async def resolve_all(self, ref_list: list[Any]) -> list[dict[str, Any]]:
        """Resolve a list of $ref objects in parallel.

        Args:
            ref_list: List of $ref dicts (or already-resolved objects).

        Returns:
            List of resolved JSON payloads in the same order.
        """
        import asyncio

        tasks = [self.resolve(item) for item in ref_list]
        return await asyncio.gather(*tasks)

    @property
    def stats(self) -> dict[str, int]:
        """Cache statistics for logging."""
        return {
            "hits": self._hits,
            "misses": self._misses,
            "size": len(self._cache),
            "hit_rate": round(self._hits / max(self._hits + self._misses, 1), 3),
        }

    def clear(self) -> None:
        """Clear the cache. Call between sync runs."""
        self._cache.clear()
        self._hits = 0
        self._misses = 0


# ── Bulk Resolution Helpers ────────────────────────────────────────────────────


async def resolve_items_paginated(
    client: ESPNClient,
    path: str,
    resolver: RefResolver,
    params: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """Fetch all items from a paginated endpoint, resolving each one.

    Covers the common ESPN pattern: list endpoint returns items as $refs,
    each must be resolved individually to get the full detail.

    Args:
        client: ESPN HTTP client.
        path: API path for the list endpoint.
        resolver: RefResolver instance for caching.
        params: Query parameters.

    Returns:
        List of fully-resolved item JSON payloads.
    """
    all_items: list[dict[str, Any]] = []
    async for page in client.paginate(path, params=params):
        items = page.get("items", [])
        resolved = await resolver.resolve_all(items)
        all_items.extend(resolved)
    return all_items
