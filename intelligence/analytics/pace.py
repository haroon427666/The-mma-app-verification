"""Pace Metrics — fight frequency, activity rate, pressure indicators.

Pace = how often a fighter fights + how active they are during fights.
"""

import numpy as np


def activity_rate(
    total_fights: int,
    years_pro: float,
) -> float:
    """Fights per year. Normalized: 3+ fights/year = 1.0."""
    if years_pro < 0.5:
        return 0.5
    rate = total_fights / years_pro
    return np.clip(rate / 3.0, 0.0, 1.0)


def fight_pace(
    sig_strikes_per_min: float,
    takedowns_per_15: float,
    fight_time_avg_sec: float = 900,
) -> float:
    """In-fight pace: how active the fighter is during a fight.

    Combines striking volume, takedown attempts, and fight duration.
    """
    strike_pace = np.clip(sig_strikes_per_min / 8.0, 0, 1)
    td_pace = np.clip(takedowns_per_15 / 6.0, 0, 1)
    time_factor = np.clip(fight_time_avg_sec / 1500.0, 0, 1)
    return 0.5 * strike_pace + 0.3 * td_pace + 0.2 * time_factor


def pressure_score(
    sig_strikes_landed: float,
    sig_strikes_absorbed: float,
    takedowns_attempted: float,
) -> float:
    """How much pressure does the fighter apply?

    Out-landing + out-grappling = pressure.
    """
    strike_diff = np.clip((sig_strikes_landed - sig_strikes_absorbed) / 4.0 + 0.5, 0, 1)
    td_diff = np.clip(takedowns_attempted / 4.0, 0, 1)
    return 0.6 * strike_diff + 0.4 * td_diff


def cardio_score(
    round_1_2_performance: float,
    round_3_4_5_performance: float,
) -> float:
    """Performance drop-off in later rounds. 1.0 = no drop-off, 0.0 = gasses completely."""
    if round_1_2_performance <= 0:
        return 0.5
    ratio = round_3_4_5_performance / round_1_2_performance
    return np.clip(ratio, 0.0, 1.0)
