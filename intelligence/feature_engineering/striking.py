"""Striking features — 8-dimensional vector.

Captures: volume, accuracy, power, defense, diversity, pressure.
"""

import numpy as np
from intelligence.feature_engineering.base import FeaturePipeline


class StrikingFeatures(FeaturePipeline):
    dim = 8

    def extract(self, f: dict) -> np.ndarray:
        slpm = f.get("sig_strikes_landed_per_min", 0)
        sa_pct = f.get("sig_strikes_accuracy_pct", 0)
        sd_pct = f.get("sig_strikes_defense_pct", 0)
        sapm = f.get("sig_strikes_absorbed_per_min", 0)
        kd = f.get("knockdowns_total", 0)
        fights = max(f.get("wins", 0) + f.get("losses", 0), 1)

        v = np.zeros(8, dtype=np.float32)
        v[0] = np.clip(slpm / 8.0, 0, 1)
        v[1] = sa_pct / 100.0
        v[2] = sd_pct / 100.0
        v[3] = 1.0 - np.clip(sapm / 8.0, 0, 1) if sapm > 0 else 1.0
        v[4] = np.clip(kd / max(fights, 1) / 2.0, 0, 1)
        v[5] = max(0, slpm - sapm) / 4.0 if slpm > 0 and sapm > 0 else 0
        v[6] = np.clip(sa_pct / 100.0 * slpm / 4.0, 0, 1)
        v[7] = 0.0  # Reserved for stance-switching / diversity
        return v
