"""Training Dataset Builder — creates feature-label pairs from fight history."""

import numpy as np
from typing import Optional


def build_fight_dataset(
    fights: list[dict],
    fighter_lookup: dict[str, dict],
) -> tuple[np.ndarray, np.ndarray, list[str]]:
    """Build training dataset from fight history.

    Returns (features, labels, feature_names).
    Features are matchup vectors: [streak_diff, elo_diff, age_diff, reach_diff,
    finish_rate_a, finish_rate_b, momentum_a, momentum_b, win_quality_a,
    win_quality_b, championship_a, championship_b, striking_diff, grappling_diff]
    """
    features_list = ["streak_diff", "elo_diff", "age_diff", "reach_diff",
                     "finish_rate_a", "finish_rate_b", "momentum_a", "momentum_b",
                     "win_quality_a", "win_quality_b", "championship_a", "championship_b",
                     "striking_diff", "grappling_diff"]

    n = len(fights)
    X = np.zeros((n, len(features_list)), dtype=np.float32)
    y = np.zeros(n, dtype=np.float32)

    for i, fight in enumerate(fights):
        a = fighter_lookup.get(fight.get("fighter_a_id", ""), {})
        b = fighter_lookup.get(fight.get("fighter_b_id", ""), {})
        if not a or not b:
            continue

        X[i] = [
            a.get("streak", 0) - b.get("streak", 0),
            a.get("elo_rating", 1500) - b.get("elo_rating", 1500),
            a.get("age", 30) - b.get("age", 30),
            a.get("reach_cm", 183) - b.get("reach_cm", 183),
            _finish_rate(a),
            _finish_rate(b),
            a.get("momentum_score", 0.5),
            b.get("momentum_score", 0.5),
            a.get("win_quality", 0.5),
            b.get("win_quality", 0.5),
            a.get("championship_score", 0.0),
            b.get("championship_score", 0.0),
            a.get("sig_strikes_landed_per_min", 0) - b.get("sig_strikes_landed_per_min", 0),
            a.get("takedown_avg_per_15min", 0) - b.get("takedown_avg_per_15min", 0),
        ]

        y[i] = 1.0 if fight.get("winner_id") == fight.get("fighter_a_id") else 0.0

    return X, y, features_list


def _finish_rate(f: dict) -> float:
    w = max(f.get("wins", 1), 1)
    return (f.get("ko_wins", 0) + f.get("sub_wins", 0)) / w
