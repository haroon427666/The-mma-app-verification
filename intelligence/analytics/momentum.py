"""Momentum Scoring — recent form, streak quality, trajectory direction.

Momentum = weighted combination of current streak, recent win rate (last 5),
and quality of recent opponents.
"""

import numpy as np


def momentum_score(
    streak: int,
    recent_results: list[int] | None = None,
    recent_opp_quality: list[float] | None = None,
) -> float:
    """Compute momentum score [0,1] from streak + recent results.

    Args:
        streak: Current win streak (positive) or loss streak (negative)
        recent_results: List of [1=win, 0=loss, 0.5=draw] for last N fights
        recent_opp_quality: Opponent quality scores [0,1] for last N fights
    """
    if recent_results is None or len(recent_results) == 0:
        return np.clip((streak + 5) / 15.0, 0.0, 1.0)

    n = len(recent_results)

    # Time-decay weights (more recent = higher weight)
    weights = np.exp(np.linspace(0, 1, n)) / np.exp(np.linspace(0, 1, n)).sum()

    # Win rate weighted by recency
    weighted_wr = np.dot(np.array(recent_results, dtype=np.float32), weights)

    # Opponent quality weighted by recency
    if recent_opp_quality and len(recent_opp_quality) == n:
        weighted_opp = np.dot(np.array(recent_opp_quality, dtype=np.float32), weights)
    else:
        weighted_opp = 0.5

    # Streak contribution
    streak_score = np.clip((streak + 5) / 10.0, 0.0, 1.0)

    # Composite
    return 0.4 * weighted_wr + 0.2 * weighted_opp + 0.4 * streak_score


def trajectory_slope(
    career_results: list[int],
    window: int = 5,
) -> float:
    """Compute career trajectory slope: positive = improving, negative = declining.

    Uses rolling win rate with linear regression on last N fights.
    """
    if len(career_results) < window:
        return 0.0

    recent = career_results[-window:]
    x = np.arange(window, dtype=np.float32)
    y = np.array(recent, dtype=np.float32)
    slope, _ = np.polyfit(x, y, 1)
    return np.clip(slope * 5, -1.0, 1.0)  # Normalize
