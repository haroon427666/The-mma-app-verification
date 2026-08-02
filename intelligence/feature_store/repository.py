"""Feature Store Repository — centralized storage and retrieval.

Every feature generated anywhere ends here. No recomputation.
Backed by in-memory dict for now, swap to Redis/Feast in production.
"""

import time
from typing import Any, Optional


class FeatureRepository:
    """Single source of truth for all computed features.

    Usage:
        repo = FeatureRepository()
        repo.put("fighter:abc123", {"slpm": 4.5, "elo": 1800})
        features = repo.get("fighter:abc123")
    """

    def __init__(self):
        self._store: dict[str, dict[str, Any]] = {}
        self._timestamps: dict[str, float] = {}
        self._versions: dict[str, int] = {}

    def put(self, entity_id: str, features: dict[str, Any], version: int = 1) -> None:
        if entity_id not in self._store:
            self._store[entity_id] = {}
        self._store[entity_id].update(features)
        self._timestamps[entity_id] = time.time()
        self._versions[entity_id] = version

    def get(self, entity_id: str, feature_names: list[str] | None = None) -> dict[str, Any]:
        data = self._store.get(entity_id, {})
        if feature_names:
            return {k: data[k] for k in feature_names if k in data}
        return dict(data)

    def get_scalar(self, entity_id: str, feature_name: str) -> Optional[Any]:
        return self._store.get(entity_id, {}).get(feature_name)

    def put_batch(self, items: dict[str, dict[str, Any]], version: int = 1) -> None:
        for eid, features in items.items():
            self.put(eid, features, version=version)

    def get_matrix(self, entity_ids: list[str], feature_names: list[str]) -> list[dict[str, Any]]:
        return [self.get(eid, feature_names) for eid in entity_ids]

    def has(self, entity_id: str) -> bool:
        return entity_id in self._store

    def age_seconds(self, entity_id: str) -> float:
        ts = self._timestamps.get(entity_id, 0)
        return time.time() - ts if ts else float("inf")

    def stale(self, entity_id: str, ttl: float) -> bool:
        return self.age_seconds(entity_id) > ttl

    def invalidate(self, entity_id: str | None = None) -> None:
        if entity_id:
            self._store.pop(entity_id, None)
            self._timestamps.pop(entity_id, None)
        else:
            self._store.clear()
            self._timestamps.clear()

    @property
    def size(self) -> int:
        return len(self._store)

    def stats(self) -> dict:
        return {
            "entities": len(self._store),
            "total_features": sum(len(f) for f in self._store.values()),
        }
