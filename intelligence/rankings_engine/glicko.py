"""Glicko Rating System — Elo with rating deviation (RD).

Better for MMA because it models uncertainty.
New fighters have high RD → their rating moves faster.
Inactive fighters' RD increases → their rating becomes less certain.
"""

import math

INITIAL_RATING = 1500.0
INITIAL_RD = 350.0  # Rating deviation (uncertainty)
MIN_RD = 60.0
Q = math.log(10) / 400.0


def expected_score(rating: float, opponent_rating: float, opponent_rd: float) -> float:
    """Probability that the player beats the opponent."""
    g = 1.0 / math.sqrt(1.0 + 3.0 * Q * Q * opponent_rd * opponent_rd / (math.pi * math.pi))
    return 1.0 / (1.0 + math.pow(10, -g * (rating - opponent_rating) / 400.0))


def update_glicko(
    rating: float, rd: float,
    opponent_rating: float, opponent_rd: float,
    won: bool,
) -> tuple[float, float]:
    """Update a single fighter's Glicko rating after a fight.

    Returns: (new_rating, new_rd)
    """
    g = 1.0 / math.sqrt(1.0 + 3.0 * Q * Q * opponent_rd * opponent_rd / (math.pi * math.pi))
    e = expected_score(rating, opponent_rating, opponent_rd)
    actual = 1.0 if won else 0.0

    d_sq = 1.0 / (Q * Q * g * g * e * (1.0 - e) + 1e-10)

    new_rating = rating + (Q / (1.0 / (rd * rd + 1e-10) + 1.0 / d_sq)) * g * (actual - e)
    new_rd = max(MIN_RD, math.sqrt(1.0 / (1.0 / (rd * rd + 1e-10) + 1.0 / d_sq)))

    return new_rating, new_rd


def increase_rd(rd: float, days_inactive: float, decay_rate: float = 0.005) -> float:
    """Increase RD for inactivity. More uncertain = higher RD."""
    return min(math.sqrt(rd * rd + decay_rate * days_inactive), INITIAL_RD)
