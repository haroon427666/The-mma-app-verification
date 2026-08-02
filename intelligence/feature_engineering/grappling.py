"""Grappling features — 6-dimensional vector.

Captures: takedown offense, defense, submission threat, control.
"""

import numpy as np
from intelligence.feature_engineering.base import FeaturePipeline


class GrapplingFeatures(FeaturePipeline):
    dim = 6

    def extract(self, f: dict) -> np.ndarray:
        td_avg = f.get("takedown_avg_per_15min", 0)
        td_acc = f.get("takedown_accuracy_pct", 0)
        td_def = f.get("takedown_defense_pct", 0)
        sub_avg = f.get("submission_avg_per_15min", 0)
        sub_wins = f.get("sub_wins", 0)
        wins = max(f.get("wins", 1), 1)

        v = np.zeros(6, dtype=np.float32)
        v[0] = np.clip(td_avg / 6.0, 0, 1)
        v[1] = td_acc / 100.0
        v[2] = td_def / 100.0
        v[3] = np.clip(sub_avg / 3.0, 0, 1)
        v[4] = sub_wins / wins
        v[5] = (v[0] + v[3]) / 2.0  # Ground threat composite
        return v
