"""Career Trajectory — where is this fighter in their career arc?

Combines age, experience, recent form, and division context.
"""

import numpy as np


def career_phase(
    age: float,
    total_fights: int,
    recent_win_rate: float,
    is_champion: bool = False,
) -> str:
    """Classify career phase: prospect, contender, prime, veteran, gatekeeper, champion."""
    if is_champion:
        return "Champion"

    if age < 26 and total_fights < 15:
        return "Rising Prospect" if recent_win_rate > 0.6 else "Developing Prospect"

    if age <= 32 and recent_win_rate > 0.7:
        return "Contender"
    if age <= 32:
        return "Prime"

    if recent_win_rate > 0.6:
        return "Veteran Contender"
    if recent_win_rate > 0.4:
        return "Veteran"
    return "Gatekeeper"


def trajectory_score(
    age: float,
    total_fights: int,
    recent_results: list[int],
    win_quality: float = 0.5,
) -> float:
    """Overall career trajectory score [0, 1]. Higher = ascending."""
    from intelligence.analytics.age_curves import age_performance_score

    age_score = age_performance_score(age)
    exp_score = np.clip(total_fights / 30.0, 0, 1)
    form = sum(recent_results[-4:]) / max(len(recent_results[-4:]), 1) if recent_results else 0.5

    return 0.3 * age_score + 0.15 * exp_score + 0.35 * form + 0.2 * win_quality
