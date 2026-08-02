"""Method Predictor — specific submission/KO methods (RNC, guillotine, etc.)."""

import numpy as np


class MethodPredictor:
    """Predicts specific finish methods."""

    METHODS = [
        "Rear Naked Choke", "Guillotine", "Arm Triangle", "Armbar",
        "Triangle Choke", "D'Arce", "Kimura", "Ground and Pound",
        "Head Kick KO", "Punch KO", "Knee KO", "Decision",
    ]

    def predict(self, fighter: dict) -> dict[str, float]:
        """Predict method probabilities for a specific fighter."""
        is_grappler = fighter.get("sub_avg_per_15", 0) > 1.0
        is_striker = fighter.get("sig_strikes_landed_per_min", 0) > 5.0

        probs = {
            "Rear Naked Choke": 0.12 if is_grappler else 0.04,
            "Guillotine": 0.08 if is_grappler else 0.03,
            "Arm Triangle": 0.06 if is_grappler else 0.02,
            "Armbar": 0.04, "Triangle Choke": 0.03,
            "D'Arce": 0.04 if is_grappler else 0.01,
            "Kimura": 0.03,
            "Ground and Pound": 0.12 if is_striker else 0.06,
            "Head Kick KO": 0.06 if is_striker else 0.02,
            "Punch KO": 0.15 if is_striker else 0.08,
            "Knee KO": 0.04,
            "Decision": 0.23 if not is_grappler and not is_striker else 0.15,
        }

        total = sum(probs.values())
        return {k: round(v / total, 3) for k, v in sorted(probs.items(), key=lambda x: x[1], reverse=True)}
