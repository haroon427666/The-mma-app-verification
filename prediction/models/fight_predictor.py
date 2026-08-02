"""Fight Predictor — predicts winner probability using ensemble ML.

Supports: XGBoost, LightGBM, Logistic Regression, Random Forest, ensemble.
Falls back to heuristic if no trained model is available.
"""

import numpy as np
from typing import Optional, Any


class FightPredictor:
    """Predicts fight winner probability.

    Primary: trained XGBoost/LightGBM model
    Fallback: Elo + momentum + quality heuristic
    """

    def __init__(self, model: Optional[Any] = None):
        self.model = model
        self.feature_names: list[str] = []
        self._calibration_curve: Optional[tuple[np.ndarray, np.ndarray]] = None

    def predict(self, features: np.ndarray) -> np.ndarray:
        if self.model is not None:
            return self._predict_ml(features)
        return self._predict_heuristic(features)

    def predict_proba(self, features: np.ndarray) -> np.ndarray:
        """Return [prob_A, prob_B] probabilities."""
        prob_a = self.predict(features)
        prob_a = prob_a.reshape(-1) if prob_a.ndim > 1 else prob_a
        return np.column_stack([prob_a, 1.0 - prob_a])

    def predict_from_fighters(self, fighter_a: dict, fighter_b: dict) -> dict:
        """Predict winner from two fighter dicts. Returns full prediction."""
        features = self._extract_features(fighter_a, fighter_b)
        prob_a = float(self.predict(features.reshape(1, -1))[0])

        elo_diff = fighter_a.get("elo_rating", 1500) - fighter_b.get("elo_rating", 1500)
        return {
            "fighter_a": fighter_a.get("name", fighter_a.get("full_name", "A")),
            "fighter_b": fighter_b.get("name", fighter_b.get("full_name", "B")),
            "prob_a": round(prob_a, 4),
            "prob_b": round(1.0 - prob_a, 4),
            "elo_differential": elo_diff,
            "confidence": self._confidence_level(abs(prob_a - 0.5)),
        }

    def _predict_ml(self, features: np.ndarray) -> np.ndarray:
        raw = self.model.predict(features)
        if raw.ndim == 2 and raw.shape[1] == 2:
            return raw[:, 0]
        return raw.reshape(-1)

    def _predict_heuristic(self, features: np.ndarray) -> np.ndarray:
        """Heuristic: Elo-based with decay for uncertainty."""
        f = features.reshape(-1, 12) if features.ndim == 1 else features
        # feature layout: [streak_diff, elo_diff, age_diff, reach_diff, finish_rate_a, finish_rate_b,
        #                  momentum_a, momentum_b, wq_a, wq_b, title_a, title_b]
        if f.shape[1] >= 2:
            elo_diff = f[:, 1]
            streak_diff = f[:, 0] * 0.3
            momentum_diff = (f[:, 6] - f[:, 7]) * 0.2
            quality_diff = (f[:, 8] - f[:, 9]) * 0.2
            title_diff = (f[:, 10] - f[:, 11]) * 0.15

            raw = elo_diff / 400.0 + streak_diff + momentum_diff + quality_diff + title_diff
            return 1.0 / (1.0 + np.exp(-raw * 2.5))
        return np.full(f.shape[0], 0.5)

    def _extract_features(self, a: dict, b: dict) -> np.ndarray:
        return np.array([
            a.get("streak", 0) - b.get("streak", 0),
            a.get("elo_rating", 1500) - b.get("elo_rating", 1500),
            a.get("age", 30) - b.get("age", 30),
            a.get("reach_cm", 183) - b.get("reach_cm", 183),
            a.get("finish_rate", 0.5),
            b.get("finish_rate", 0.5),
            a.get("momentum_score", 0.5),
            b.get("momentum_score", 0.5),
            a.get("win_quality", 0.5),
            b.get("win_quality", 0.5),
            a.get("championship_score", 0.0),
            b.get("championship_score", 0.0),
        ], dtype=np.float32)

    def _confidence_level(self, margin: float) -> str:
        if margin > 0.25: return "very_high"
        if margin > 0.15: return "high"
        if margin > 0.08: return "medium"
        if margin > 0.03: return "low"
        return "coin_flip"

    def save(self, path: str) -> None:
        import joblib
        joblib.dump({"model": self.model, "features": self.feature_names}, path)

    def load(self, path: str) -> None:
        import joblib
        data = joblib.load(path)
        self.model = data["model"]
        self.feature_names = data["features"]
