"""Momentum features — 4-dimensional vector.

Captures: streak, recent form (last 3/5), trending direction, momentum score.
"""

import numpy as np
from intelligence.feature_engineering.base import FeaturePipeline


class MomentumFeatures(FeaturePipeline):
    dim = 4

    def extract(self, f: dict) -> np.ndarray:
        streak = f.get("streak", 0)
        recent_wins = f.get("recent_wins", 0)
        recent_fights = max(f.get("recent_fights", 5), 1)

        v = np.zeros(4, dtype=np.float32)
        v[0] = np.clip((streak + 10) / 20.0, 0, 1) if streak >= 0 else np.clip((10 + streak) / 10.0, 0, 1)
        v[1] = recent_wins / recent_fights
        v[2] = (v[0] + v[1]) / 2.0  # Momentum score
        v[3] = 1.0 if streak > 0 and recent_wins / recent_fights > 0.6 else 0.0
        return v
