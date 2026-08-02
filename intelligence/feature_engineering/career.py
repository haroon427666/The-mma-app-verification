"""Career features — 4-dimensional vector.

Captures: experience, title fight %, finish rate, decision rate.
"""

import numpy as np
from intelligence.feature_engineering.base import FeaturePipeline


class CareerFeatures(FeaturePipeline):
    dim = 4

    def extract(self, f: dict) -> np.ndarray:
        wins = f.get("wins", 0)
        losses = f.get("losses", 0)
        fights = wins + losses + f.get("draws", 0)
        ko_wins = f.get("ko_wins", 0)
        sub_wins = f.get("sub_wins", 0)
        title_wins = f.get("title_wins", 0)
        dec_wins = max(wins - ko_wins - sub_wins, 0)

        v = np.zeros(4, dtype=np.float32)
        v[0] = np.clip(fights / 50.0, 0, 1)
        v[1] = np.clip(title_wins / 10.0, 0, 1)
        v[2] = (ko_wins + sub_wins) / max(wins, 1) if wins > 0 else 0
        v[3] = dec_wins / max(wins, 1) if wins > 0 else 0
        return v
