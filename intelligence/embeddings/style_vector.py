"""Style Vector — numeric representation of fighting style.

A 16-dimensional vector categorizing a fighter's style across:
    striking, grappling, pressure, pace, defense, finishing.

Each dimension is a float in [0, 1] representing dominance in that facet.

Dimensions:
    0: striking_volume      — strikes landed per minute (normalized)
    1: striking_accuracy    — % of strikes that land
    2: striking_defense     — % of opponent strikes avoided
    3: striking_power       — knockdowns per fight
    4: grappling_offense    — takedowns per 15 min
    5: grappling_accuracy   — takedown success %
    6: grappling_defense    — takedown defense %
    7: submission_threat    — submission attempts per 15 min
    8: pace                 — activity rate (strikes + takedown attempts)
    9: durability           — strikes absorbed / still winning
   10: finishing_ability    — finish rate (KO + sub wins / total wins)
   11: clinch_control       — control time in clinch
   12: ground_control       — control time on ground
   13: cardio               — performance drop-off rounds 3-5 vs 1-2
   14: aggression           — forward pressure / advancing metrics
   15: fight_iq             — decision win rate when fight goes distance
"""

import numpy as np

DIM = 16


def empty() -> np.ndarray:
    """Return an empty (zero) style vector."""
    return np.zeros(DIM, dtype=np.float32)


def from_stats(
    sig_strikes_landed_per_min: float = 0.0,
    sig_strikes_accuracy_pct: float = 0.0,
    sig_strikes_defense_pct: float = 0.0,
    knockdowns_per_fight: float = 0.0,
    takedown_avg_per_15: float = 0.0,
    takedown_accuracy_pct: float = 0.0,
    takedown_defense_pct: float = 0.0,
    submission_avg_per_15: float = 0.0,
    finish_rate: float = 0.0,
    decision_win_rate: float = 0.0,
) -> np.ndarray:
    """Create a style vector from UFC-statistic-style inputs."""
    vec = np.zeros(DIM, dtype=np.float32)
    # Normalize each to [0,1]
    vec[0] = min(sig_strikes_landed_per_min / 8.0, 1.0)
    vec[1] = sig_strikes_accuracy_pct / 100.0
    vec[2] = sig_strikes_defense_pct / 100.0
    vec[3] = min(knockdowns_per_fight / 2.0, 1.0)
    vec[4] = min(takedown_avg_per_15 / 6.0, 1.0)
    vec[5] = takedown_accuracy_pct / 100.0
    vec[6] = takedown_defense_pct / 100.0
    vec[7] = min(submission_avg_per_15 / 3.0, 1.0)
    # Derived
    vec[8] = (vec[0] + vec[4]) / 2.0  # pace
    vec[9] = 0.5  # durability (default, updated from fight data)
    vec[10] = finish_rate
    vec[11] = vec[4] * 0.7  # clinch control proxy
    vec[12] = vec[7] * 0.8  # ground control proxy
    vec[13] = 0.5  # cardio (default)
    vec[14] = (vec[3] + vec[0]) / 2.0  # aggression proxy
    vec[15] = decision_win_rate
    return vec


def style_label(vec: np.ndarray) -> str:
    """Human-readable style category from vector."""
    if vec[10] > 0.7 and vec[3] > 0.5:
        return "Knockout Artist"
    if vec[10] > 0.7 and vec[7] > 0.4:
        return "Submission Specialist"
    if vec[0] > 0.6 and vec[4] < 0.3:
        return "Striker"
    if vec[4] > 0.6 and vec[0] < 0.4:
        return "Grappler"
    if vec[1] > 0.5 and vec[2] > 0.5 and vec[0] > 0.5:
        return "Technical Striker"
    if vec[0] > 0.5 and vec[4] > 0.4:
        return "Well-Rounded"
    if vec[14] > 0.7:
        return "Pressure Fighter"
    if vec[15] > 0.6:
        return "Decision Specialist"
    return "Balanced"
