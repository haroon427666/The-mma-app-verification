"""Elo Rating System — for MMA fighters.

Standard Elo with K-factor that adjusts for:
- Experience (higher K for newer fighters)
- Fight type (title fights have higher K)
- Finish bonus (KOs/subs get extra rating transfer)
"""

import math


INITIAL_ELO = 1500.0
BASE_K = 32
TITLE_K = 48
PROSPECT_K = 64


def expected_score(rating_a: float, rating_b: float) -> float:
    """Probability that A beats B."""
    return 1.0 / (1.0 + math.pow(10, (rating_b - rating_a) / 400.0))


def k_factor(total_fights: int, is_title_fight: bool = False) -> float:
    if total_fights < 5:
        return PROSPECT_K
    if is_title_fight:
        return TITLE_K
    return BASE_K


def update_elo(
    rating_a: float,
    rating_b: float,
    a_won: bool,
    a_fights: int = 10,
    b_fights: int = 10,
    is_title: bool = False,
    is_finish: bool = False,
) -> tuple[float, float]:
    """Update Elo ratings after a fight.

    Returns: (new_rating_a, new_rating_b)
    """
    expected_a = expected_score(rating_a, rating_b)
    expected_b = 1.0 - expected_a

    actual_a = 1.0 if a_won else 0.0
    actual_b = 0.0 if a_won else 1.0

    k_a = k_factor(a_fights, is_title)
    k_b = k_factor(b_fights, is_title)

    # Finish bonus: winner gets 25% extra rating transfer
    finish_mult = 1.25 if is_finish else 1.0

    new_a = rating_a + k_a * (actual_a - expected_a) * finish_mult
    new_b = rating_b + k_b * (actual_b - expected_b) * finish_mult

    return new_a, new_b
