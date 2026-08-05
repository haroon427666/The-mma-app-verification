"""Age Curves — fighter performance vs age analysis.

Models how striking, grappling, durability, and win rate vary with age.
Peak age: 29-32 for MMA. Decline curve modeled with asymmetric sigmoid.
"""

import numpy as np

# Constants derived from UFC fight data analysis
PEAK_AGE_MIN = 29
PEAK_AGE_MAX = 32
DECLINE_START = 34
SHARP_DECLINE = 37


def age_performance_score(age: float) -> float:
    """Returns [0, 1] score for how close a fighter is to their peak age.

    1.0 = at peak (29-32), declining after 34, sharp drop after 37.
    """
    if PEAK_AGE_MIN <= age <= PEAK_AGE_MAX:
        return 1.0

    if age < PEAK_AGE_MIN:
        # Rising: linear from 21 to peak
        return np.clip((age - 18) / (PEAK_AGE_MIN - 18), 0.1, 1.0)
    elif age <= DECLINE_START:
        # Early decline: slight drop
        return 1.0 - 0.05 * (age - PEAK_AGE_MAX)
    elif age <= SHARP_DECLINE:
        # Moderate decline
        return 0.8 - 0.15 * (age - DECLINE_START)
    else:
        # Sharp decline
        return max(0.1, 0.35 - 0.1 * (age - SHARP_DECLINE))


def age_decline_factor(age: float) -> float:
    """Multiplicative factor for stats: 1.0 at peak, <1.0 before/after."""
    return np.clip(age_performance_score(age), 0.3, 1.0)


def adjusted_stat(age: float, raw_stat: float) -> float:
    """Adjust a stat by the age decline factor."""
    return raw_stat * age_decline_factor(age)


def career_stage(age: float) -> str:
    score = age_performance_score(age)
    if score >= 0.95:
        return "Prime"
    if score >= 0.75:
        return "Established"
    if age < PEAK_AGE_MIN:
        return "Rising Prospect" if score >= 0.30 else "Young Prospect"
    return "Veteran" if score >= 0.55 else "Declining"
