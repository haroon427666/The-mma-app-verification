"""Round Predictor — predicts which round the fight ends.

Returns probability distribution over 5 rounds.
"""

import numpy as np
from typing import Optional, Any


class RoundPredictor:
    """Predicts fight end round (1-5) or decision."""

    ROUNDS = [1, 2, 3, 4, 5]

    def __init__(self, is_title_fight: bool = False):
        self.is_title = is_title_fight

    def predict(self, finish_rate: float, avg_fight_time: float = 900) -> np.ndarray:
        """Predict round-end probabilities.

        Earlier rounds more likely for high-finish-rate fighters.
        """
        max_rounds = 5 if self.is_title else 3
        probs = np.zeros(5, dtype=np.float32)

        # Higher finish rate → earlier finish
        for r in range(max_rounds):
            time_factor = np.exp(-0.3 * r)
            probs[r] = finish_rate * time_factor * (1.0 / max_rounds + 0.05)

        # Normalize, then blend with uniform
        probs = probs / probs.sum()
        probs = probs[:max_rounds] / probs[:max_rounds].sum()
        full = np.zeros(5, dtype=np.float32)
        full[:max_rounds] = probs
        return full

    def predict_from_fighters(self, a: dict, b: dict) -> dict:
        fr_a = a.get("finish_rate", 0.5)
        fr_b = b.get("finish_rate", 0.5)
        combined_fr = 0.6 * max(fr_a, fr_b) + 0.4 * min(fr_a, fr_b)

        probs = self.predict(combined_fr)
        return {
            f"round_{i+1}": round(float(probs[i]), 4) for i in range(5)
        }
