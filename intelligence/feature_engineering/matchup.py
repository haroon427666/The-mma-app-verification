"""Matchup features — 12-dimensional head-to-head feature vector.

Combines all feature pipelines for both fighters into a matchup representation.
"""

import numpy as np
from intelligence.feature_engineering.base import FeaturePipeline
from intelligence.feature_engineering.striking import StrikingFeatures
from intelligence.feature_engineering.grappling import GrapplingFeatures
from intelligence.feature_engineering.physical import PhysicalFeatures
from intelligence.feature_engineering.momentum import MomentumFeatures
from intelligence.feature_engineering.career import CareerFeatures


class MatchupFeatures(FeaturePipeline):
    """Produces a 12-dim matchup vector: contrast between two fighters."""

    dim = 12

    def __init__(self):
        self._striking = StrikingFeatures()
        self._grappling = GrapplingFeatures()
        self._physical = PhysicalFeatures()
        self._momentum = MomentumFeatures()
        self._career = CareerFeatures()

    def extract_pair(self, fighter_a: dict, fighter_b: dict) -> np.ndarray:
        """Extract matchup features for A vs B. Directional: A is the reference."""
        sa = self._striking.extract(fighter_a)
        sb = self._striking.extract(fighter_b)
        ga = self._grappling.extract(fighter_a)
        gb = self._grappling.extract(fighter_b)
        pa = self._physical.extract(fighter_a)
        pb = self._physical.extract(fighter_b)
        ma = self._momentum.extract(fighter_a)
        mb = self._momentum.extract(fighter_b)
        ca = self._career.extract(fighter_a)
        cb = self._career.extract(fighter_b)

        v = np.zeros(12, dtype=np.float32)
        v[0:2] = sa[0:2] - sb[0:2]     # striking vol + acc diff
        v[2:4] = ga[0:2] - gb[0:2]     # grappling off + acc diff
        v[4] = pa[0] - pb[0]           # age diff
        v[5] = pa[2] - pb[2]           # reach diff
        v[6] = ma[2] - mb[2]           # momentum diff
        v[7] = ca[0] - cb[0]           # experience diff
        v[8] = ca[2] - cb[2]           # finish rate diff
        v[9] = pa[5]                   # A is southpaw
        v[10] = pb[5]                  # B is southpaw
        v[11] = (sa[5] - sb[5]) / 2.0 + 0.5  # striking differential

        return v

    def extract(self, _fighter: dict) -> np.ndarray:
        raise NotImplementedError("Use extract_pair() for matchup features")
