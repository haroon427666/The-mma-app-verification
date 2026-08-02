"""Quality Scores — win quality, opponent quality, championship pedigree.

Win quality: how good were the opponents you beat?
Opponent quality: how good were all opponents you faced?
"""

import numpy as np


def opponent_quality_score(
    opponent_win_rates: list[float],
    opponent_ranks: list[int | None] | None = None,
) -> float:
    """Average quality of opponents faced: [0, 1]."""
    if not opponent_win_rates:
        return 0.5

    wr_score = np.mean([np.clip(r, 0.3, 1.0) for r in opponent_win_rates])

    if opponent_ranks:
        rank_scores = []
        for r in opponent_ranks:
            if r is None:
                rank_scores.append(0.2)
            else:
                rank_scores.append(1.0 - r / 15.0)
        rank_score = np.mean(rank_scores)
    else:
        rank_score = 0.5

    return 0.6 * wr_score + 0.4 * rank_score


def win_quality_score(
    beaten_opponent_quality: list[float],
    finish_wins: int = 0,
    total_wins: int = 1,
) -> float:
    """Quality of wins: weighted by finish rate. [0, 1]."""
    if not beaten_opponent_quality:
        return 0.5

    avg_quality = np.mean(beaten_opponent_quality)
    finish_bonus = min(finish_wins / max(total_wins, 1) * 0.2, 0.2)
    return np.clip(avg_quality + finish_bonus, 0.0, 1.0)


def championship_score(
    title_fights: int,
    title_wins: int,
    title_defenses: int,
) -> float:
    """Championship pedigree: [0, 1]. 1.0 = dominant champion."""
    if title_fights == 0:
        return 0.0
    win_rate = title_wins / title_fights
    defense_bonus = np.clip(title_defenses / 10.0, 0.0, 0.3)
    return np.clip(0.7 * win_rate + defense_bonus, 0.0, 1.0)
