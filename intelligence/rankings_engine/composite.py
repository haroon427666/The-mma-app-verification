"""Composite Ranking — combines Elo, win quality, momentum, and championship score.

Produces a single ranking score [0, 1000] that can be used to order fighters.
Weights tuned for MMA: recent form + quality of opposition > raw record.
"""

import numpy as np


def composite_ranking_score(
    elo_rating: float = 1500.0,
    win_quality: float = 0.5,
    opp_quality: float = 0.5,
    momentum: float = 0.5,
    championship: float = 0.0,
    finish_rate: float = 0.5,
) -> float:
    """Compute a composite ranking score from multiple signals. [0, 1000] scale."""
    # Normalize Elo to [0, 1]
    elo_norm = (elo_rating - 1200) / 800.0  # 1200→0, 2000→1.0

    weights = {
        "elo": 0.30,
        "win_quality": 0.20,
        "opp_quality": 0.15,
        "momentum": 0.15,
        "championship": 0.10,
        "finish_rate": 0.10,
    }

    score = (
        weights["elo"] * elo_norm +
        weights["win_quality"] * win_quality +
        weights["opp_quality"] * opp_quality +
        weights["momentum"] * momentum +
        weights["championship"] * championship +
        weights["finish_rate"] * finish_rate
    )

    return np.clip(score * 1000.0, 0.0, 1000.0)


def rank_fighters(fighters: list[dict]) -> list[dict]:
    """Rank a list of fighters by composite score. Returns sorted list with ranks."""
    for f in fighters:
        f["_score"] = composite_ranking_score(
            elo_rating=f.get("elo", 1500),
            win_quality=f.get("win_quality", 0.5),
            opp_quality=f.get("opp_quality", 0.5),
            momentum=f.get("momentum", 0.5),
            championship=f.get("championship", 0.0),
            finish_rate=f.get("finish_rate", 0.5),
        )

    fighters.sort(key=lambda f: f["_score"], reverse=True)
    for i, f in enumerate(fighters):
        f["_rank"] = i + 1

    return fighters
