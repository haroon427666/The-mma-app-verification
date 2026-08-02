"""Finish Predictor — multi-class: KO/TKO, Submission, Decision.

Predicts the most likely finish type and probability distribution.
"""

import numpy as np
from typing import Optional, Any


class FinishPredictor:
    """Predicts fight end type: KO/TKO, Submission, or Decision."""

    OUTCOMES = ["KO/TKO", "Submission", "Decision"]

    def __init__(self, model: Optional[Any] = None):
        self.model = model

    def predict_proba(self, features: np.ndarray) -> np.ndarray:
        if self.model is not None:
            return self.model.predict_proba(features)
        return self._heuristic_proba(features)

    def predict_from_fighters(self, fighter_a: dict, fighter_b: dict) -> dict:
        """Predict finish probabilities for a matchup."""
        f = self._features(fighter_a, fighter_b).reshape(1, -1)
        probs = self.predict_proba(f)[0]
        return {
            "ko_tko": round(float(probs[0]), 4),
            "submission": round(float(probs[1]), 4),
            "decision": round(float(probs[2]), 4),
            "most_likely": self.OUTCOMES[int(np.argmax(probs))],
        }

    def _heuristic_proba(self, features: np.ndarray) -> np.ndarray:
        """Heuristic based on finish rates and opponent durability."""
        n = features.shape[0]
        probs = np.zeros((n, 3), dtype=np.float32)

        for i in range(n):
            fr_a = features[i, 4] if features.shape[1] > 4 else 0.5
            fr_b = features[i, 5] if features.shape[1] > 5 else 0.5
            # Blend both fighters' finish rates
            p_ko = fr_a * 0.6 * 0.45 + (1 - fr_b) * 0.4 * 0.45
            p_sub = (0.25 if fr_a > 0.5 else 0.35)
            p_dec = 1.0 - p_ko - p_sub
            probs[i] = [p_ko, p_sub, p_dec]

        probs = np.abs(probs) / probs.sum(axis=1, keepdims=True)
        return probs

    def _features(self, a: dict, b: dict) -> np.ndarray:
        return np.array([
            a.get("finish_rate", 0.5), b.get("finish_rate", 0.5),
            a.get("ko_rate", 0.3), b.get("ko_rate", 0.3),
            a.get("sub_rate", 0.2), b.get("sub_rate", 0.2),
        ], dtype=np.float32)
