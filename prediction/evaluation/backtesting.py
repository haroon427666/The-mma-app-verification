"""Backtesting — replay historical predictions to evaluate model performance.

Takes every UFC fight and simulates what the model would have predicted
BEFORE the fight happened, using only data available at that time.
"""

import numpy as np
from datetime import datetime
from typing import Any


def run_backtest(
    fights: list[dict],
    fighter_lookup: dict[str, dict],
    predictor: Any = None,
) -> dict:
    """Run chronological backtest on historical fights.

    Returns accuracy, log loss, calibration, and fight-by-fight results.
    """
    fights_sorted = sorted(fights, key=lambda f: f.get("date", "2000-01-01"))
    results = []
    correct = 0
    total = 0
    probs = []
    actuals = []

    for fight in fights_sorted:
        a = fighter_lookup.get(fight.get("fighter_a_id", ""), {})
        b = fighter_lookup.get(fight.get("fighter_b_id", ""), {})
        if not a or not b:
            continue

        if predictor is not None:
            pred = predictor.predict_from_fighters(a, b)
            prob_a = pred["prob_a"]
        else:
            elo_diff = a.get("elo_rating", 1500) - b.get("elo_rating", 1500)
            prob_a = 1.0 / (1.0 + np.exp(-elo_diff / 250.0))

        actual = 1.0 if fight.get("winner_id") == fight.get("fighter_a_id") else 0.0
        is_correct = (prob_a >= 0.5) == (actual == 1.0)

        correct += int(is_correct)
        total += 1
        probs.append(prob_a)
        actuals.append(actual)

        results.append({
            "event": fight.get("event_name", ""),
            "fighter_a": a.get("name", a.get("full_name", "A")),
            "fighter_b": b.get("name", b.get("full_name", "B")),
            "predicted_prob_a": round(prob_a, 3),
            "actual_winner": "A" if actual == 1 else "B",
            "correct": is_correct,
        })

    probs_arr = np.array(probs)
    actuals_arr = np.array(actuals)
    acc = correct / max(total, 1)
    eps = 1e-10
    logloss = float(-np.mean(actuals_arr * np.log(probs_arr + eps) +
                             (1 - actuals_arr) * np.log(1 - probs_arr + eps)))
    brier = float(np.mean((probs_arr - actuals_arr) ** 2))

    return {
        "total_fights": total,
        "correct": correct,
        "accuracy": round(acc, 4),
        "log_loss": round(logloss, 4),
        "brier_score": round(brier, 4),
        "calibration": _calibrate_bins(probs_arr, actuals_arr),
        "recent_results": results[-20:],
    }


def _calibrate_bins(probs: np.ndarray, actuals: np.ndarray) -> list[dict]:
    bins = [(0, 0.2), (0.2, 0.4), (0.4, 0.6), (0.6, 0.8), (0.8, 1.0)]
    calibration = []
    for lo, hi in bins:
        mask = (probs >= lo) & (probs < hi)
        if mask.sum() > 0:
            calibration.append({
                "bin": f"{lo}-{hi}",
                "count": int(mask.sum()),
                "predicted_rate": round(float(probs[mask].mean()), 3),
                "actual_rate": round(float(actuals[mask].mean()), 3),
            })
    return calibration
