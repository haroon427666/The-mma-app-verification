"""Trending Engine — identifies what's hot right now.

Uses view velocity, interaction rate, and recency to compute trending scores.
"""

import math
import time
from collections import defaultdict


class TrendingEngine:
    """Tracks and ranks entities by trending velocity."""

    def __init__(self, window_days: float = 7.0, min_views: int = 10):
        self.window = window_days * 86400
        self.min_views = min_views
        self._events: dict[str, list[float]] = defaultdict(list)

    def record_view(self, entity_id: str, weight: float = 1.0) -> None:
        self._events[entity_id].append(time.time())
        # Keep only recent
        cutoff = time.time() - self.window
        self._events[entity_id] = [t for t in self._events[entity_id] if t > cutoff]

    def velocity(self, entity_id: str) -> float:
        events = self._events.get(entity_id, [])
        if len(events) < self.min_views:
            return 0.0
        now = time.time()
        recent = [t for t in events if t > now - self.window]
        if len(recent) < 2:
            return 0.0
        # Views per hour
        span_hours = max((now - min(recent)) / 3600.0, 0.1)
        return len(recent) / span_hours

    def top_trending(self, entity_ids: list[str], k: int = 20) -> list[tuple[str, float]]:
        scored = [(eid, self.velocity(eid)) for eid in entity_ids]
        scored.sort(key=lambda x: x[1], reverse=True)
        return [(eid, v) for eid, v in scored[:k] if v > 0]

    def get_trending_data(self) -> dict[str, dict]:
        return {
            eid: {"velocity": self.velocity(eid), "total_views": len(v)}
            for eid, v in self._events.items()
        }

    def decay(self) -> None:
        cutoff = time.time() - self.window * 4
        self._events = {k: [t for t in v if t > cutoff]
                       for k, v in self._events.items()}


class FighterTrending(TrendingEngine):
    def top(self, fighters: list[dict], k: int = 10) -> list[dict]:
        ids = [f.get("id", "") for f in fighters]
        trending_ids = {eid for eid, _ in self.top_trending(ids, k)}
        result = [f for f in fighters if f.get("id") in trending_ids]
        for f in result:
            f["trending_velocity"] = self.velocity(f["id"])
        result.sort(key=lambda f: f.get("trending_velocity", 0), reverse=True)
        return result[:k]
