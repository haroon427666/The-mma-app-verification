"""Physical features — 6-dimensional vector.

Captures: age, height, reach, ape index, weight, stance advantage.
"""

import numpy as np
from intelligence.feature_engineering.base import FeaturePipeline


class PhysicalFeatures(FeaturePipeline):
    dim = 6

    def extract(self, f: dict) -> np.ndarray:
        age = f.get("age", 30)
        height = f.get("height_cm", 178)
        reach = f.get("reach_cm", 183)
        weight = f.get("weight_kg", 77)
        stance = f.get("stance", "")

        v = np.zeros(6, dtype=np.float32)
        v[0] = np.clip(age / 45.0, 0, 1)
        v[1] = np.clip((height - 155) / 50.0, 0, 1)
        v[2] = np.clip((reach - 155) / 50.0, 0, 1)
        v[3] = (reach - height) / 20.0 + 0.5
        v[4] = np.clip(weight / 120.0, 0, 1)
        v[5] = 1.0 if stance.lower() == "southpaw" else 0.0
        return v
