"""User Profile Builder — creates vector representations of user interests.

Builds profiles from: favorites, watchlist, view history, search history,
click-through data, notification preferences, weight-class affinity.
"""

import numpy as np
from typing import Any


class UserProfile:
    """Represents a user's interests as weighted topic vectors."""

    def __init__(self, user_id: str):
        self.user_id = user_id
        self._fighter_affinity: dict[str, float] = {}
        self._weight_class_affinity: dict[str, float] = {}
        self._promotion_affinity: dict[str, float] = {}
        self._style_affinity: np.ndarray = np.zeros(16, dtype=np.float32)
        self._activity_score: float = 0.5
        self._recency_score: float = 0.5
        self._total_interactions: int = 0

    @property
    def style_vector(self) -> np.ndarray:
        return self._style_affinity

    @property
    def top_weight_classes(self) -> list[str]:
        return sorted(self._weight_class_affinity, key=self._weight_class_affinity.get, reverse=True)[:5]

    @property
    def top_fighters(self) -> list[tuple[str, float]]:
        return sorted(self._fighter_affinity.items(), key=lambda x: x[1], reverse=True)[:10]

    def to_vector(self) -> np.ndarray:
        """Flatten profile into fixed-size vector for similarity."""
        vec = np.zeros(48, dtype=np.float32)
        # Style affinity (first 16 dims)
        vec[:16] = self._style_affinity
        # Top weight classes encoded
        for i, wc in enumerate(self.top_weight_classes[:5]):
            vec[16 + i] = self._weight_class_affinity.get(wc, 0)
        # Activity + recency
        vec[21] = self._activity_score
        vec[22] = self._recency_score
        # Promotion affinity
        for i, (_, score) in enumerate(sorted(self._promotion_affinity.items(),
                                                key=lambda x: x[1], reverse=True)[:3]):
            vec[23 + i] = score
        # Interaction volume
        vec[26] = min(self._total_interactions / 200.0, 1.0)
        n = np.linalg.norm(vec)
        return vec / n if n > 0 else vec


class UserProfileBuilder:
    """Builds UserProfile from activity data."""

    def build(self, user_id: str, interactions: list[dict]) -> UserProfile:
        profile = UserProfile(user_id)
        for event in interactions:
            self._process_event(profile, event)
        return profile

    def update(self, profile: UserProfile, event: dict) -> None:
        self._process_event(profile, event)

    def _process_event(self, profile: UserProfile, event: dict) -> None:
        etype = event.get("type", "")
        weight = event.get("weight", 1.0)
        entity = event.get("entity", {})

        profile._total_interactions += 1

        if etype in ("favorite_fighter", "view_fighter"):
            fid = entity.get("fighter_id", "")
            profile._fighter_affinity[fid] = profile._fighter_affinity.get(fid, 0) + weight * 0.1
            if "style_vector" in entity:
                profile._style_affinity += np.array(entity["style_vector"], dtype=np.float32) * weight * 0.05

        if etype in ("view_event", "watchlist_event", "favorite_event"):
            wc = entity.get("weight_class", "")
            if wc:
                profile._weight_class_affinity[wc] = profile._weight_class_affinity.get(wc, 0) + weight * 0.1
            prom = entity.get("promotion", "")
            if prom:
                profile._promotion_affinity[prom] = profile._promotion_affinity.get(prom, 0) + weight * 0.05

        if etype in ("search", "click"):
            profile._activity_score = min(profile._activity_score + weight * 0.01, 1.0)

        # Normalize style vector
        n = np.linalg.norm(profile._style_affinity)
        if n > 0:
            profile._style_affinity /= n
