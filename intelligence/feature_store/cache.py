"""Feature Store Cache — TTL-based in-memory caching layer.

Prevents recomputation of expensive features (embeddings, rankings).
"""

import time
from typing import Any, Optional


class FeatureCache:
    def __init__(self):
        self._data: dict[str, tuple[Any, float]] = {}

    def get(self, key: str) -> Optional[Any]:
        entry = self._data.get(key)
        if entry is None:
            return None
        value, expires_at = entry
        if time.time() > expires_at:
            del self._data[key]
            return None
        return value

    def set(self, key: str, value: Any, ttl: float) -> None:
        self._data[key] = (value, time.time() + ttl)

    def invalidate(self, prefix: str | None = None) -> int:
        count = 0
        if prefix:
            keys = [k for k in self._data if k.startswith(prefix)]
        else:
            keys = list(self._data.keys())
        for k in keys:
            del self._data[k]
            count += 1
        return count

    @property
    def size(self) -> int:
        return len(self._data)
