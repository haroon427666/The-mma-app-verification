"""Fighter Embedder — creates 64-dim vectors representing every fighter.

Combines: physical attributes, style vector, record stats, ranking info,
momentum indicators, and division context into a single embedding.

The vector encodes:
    [0:16]   Style vector (from style_vector.py)
    [16:24]  Physical attributes (age, height, reach, weight normalized)
    [24:32]  Record stats (win%, finish rate, title fights)
    [32:40]  Ranking & division (rank percentile, divisional strength)
    [40:48]  Momentum (streak, recent form, activity)
    [48:56]  Career trajectory (age curve position, experience)
    [56:64]  Quality scores (win quality, opponent quality)

All values normalized to [0,1] for cosine similarity.
"""

import numpy as np
from typing import Optional

from intelligence.embeddings.config import FIGHTER_EMBEDDING_DIM
from intelligence.embeddings.style_vector import from_stats, DIM as STYLE_DIM


def embed_fighter(
    style_vec: np.ndarray,
    age: float = 30.0,
    height_cm: float = 178.0,
    reach_cm: float = 183.0,
    weight_kg: Optional[float] = None,
    wins: int = 0,
    losses: int = 0,
    draws: int = 0,
    ko_wins: int = 0,
    sub_wins: int = 0,
    title_wins: int = 0,
    streak: int = 0,
    current_rank: Optional[int] = None,
    ranking_total: int = 15,
    is_champion: bool = False,
    win_quality: float = 0.5,
    opp_quality: float = 0.5,
    activity_rate: float = 0.5,
    momentum_score: float = 0.5,
    age_score: float = 0.5,
) -> np.ndarray:
    """Create a 64-dimensional fighter embedding.

    Args:
        style_vec: 16-dim style vector from style_vector.from_stats()
        age: Fighter age
        height_cm: Height in centimeters
        reach_cm: Reach in centimeters
        weight_kg: Weight in kilograms (optional, used for weight class)
        wins/losses/draws: Career record
        ko_wins: KO/TKO wins
        sub_wins: Submission wins
        title_wins: Championship fight wins
        streak: Current win/loss streak (positive=win streak, negative=loss streak)
        current_rank: Current division ranking (1-15, None=unranked)
        ranking_total: Number of ranked fighters in division
        is_champion: Whether fighter is current champion
        win_quality: Average quality of opponents beaten [0,1]
        opp_quality: Average quality of opponents faced [0,1]
        activity_rate: Fights per year normalized [0,1]
        momentum_score: Recent form indicator [0,1]
        age_score: Age curve percentile [0,1] — 1.0=peak age
    """
    vec = np.zeros(FIGHTER_EMBEDDING_DIM, dtype=np.float32)

    # [0:16] Style vector
    vec[:STYLE_DIM] = style_vec[:STYLE_DIM]

    # [16:24] Physical attributes
    total_fights = wins + losses + draws
    vec[16] = np.clip(age / 45.0, 0.0, 1.0)
    vec[17] = np.clip((height_cm - 155) / 50.0, 0.0, 1.0)
    vec[18] = np.clip((reach_cm - 155) / 50.0, 0.0, 1.0)
    vec[19] = (reach_cm - height_cm) / 20.0 + 0.5  # Ape index
    vec[20] = np.clip((weight_kg or 77) / 120.0, 0.0, 1.0)
    vec[21] = np.clip(total_fights / 50.0, 0.0, 1.0)  # Experience
    vec[22] = np.clip(age_score, 0.0, 1.0)
    vec[23] = 0.0  # Reserved

    # [24:32] Record stats
    if total_fights > 0:
        vec[24] = wins / total_fights
        vec[25] = losses / total_fights
    if wins > 0:
        vec[26] = (ko_wins + sub_wins) / max(wins, 1)
    vec[27] = min(streak / 10.0 + 0.5, 1.0) if streak >= 0 else max(1.0 + streak / 10.0, 0.0)
    vec[28] = min(title_wins / 10.0, 1.0)
    vec[29] = np.clip(activity_rate, 0.0, 1.0)
    vec[30] = 0.0  # Reserved
    vec[31] = 1.0 if is_champion else 0.0

    # [32:40] Ranking & Division
    if current_rank is not None and ranking_total > 0:
        vec[32] = 1.0 - (current_rank / ranking_total)
    else:
        vec[32] = 0.0
    vec[33] = np.clip(momentum_score, 0.0, 1.0)
    vec[34] = 0.0  # Division strength (populated from weight class data)
    vec[35] = 0.0  # Reserved
    vec[36] = 0.0  # Reserved
    vec[37] = 0.0  # Reserved
    vec[38] = 0.0  # Reserved
    vec[39] = 0.0  # Reserved

    # [40:48] Momentum
    vec[40] = np.clip(momentum_score, 0.0, 1.0)
    vec[41] = np.clip(activity_rate, 0.0, 1.0)
    vec[42] = max(streak, 0) / 10.0 if streak > 0 else 0.0
    vec[43] = 0.0  # Reserved
    vec[44] = 0.0  # Reserved
    vec[45] = 0.0  # Reserved
    vec[46] = 0.0  # Reserved
    vec[47] = 0.0  # Reserved

    # [48:56] Career trajectory
    vec[48] = np.clip(age_score, 0.0, 1.0)
    vec[49] = np.clip(total_fights / 50.0, 0.0, 1.0)
    vec[50] = 0.0  # Recent trajectory slope
    vec[51:56] = 0.0  # Reserved

    # [56:64] Quality scores
    vec[56] = np.clip(win_quality, 0.0, 1.0)
    vec[57] = np.clip(opp_quality, 0.0, 1.0)
    vec[58] = (win_quality + opp_quality) / 2.0
    vec[59:64] = 0.0  # Reserved

    # Normalize
    norm = np.linalg.norm(vec)
    if norm > 0:
        vec = vec / norm

    return vec


def embed_fighter_batch(
    fighters: list[dict],
) -> np.ndarray:
    """Batch embed multiple fighters. Returns (N, 64) array."""
    embeddings = np.zeros((len(fighters), FIGHTER_EMBEDDING_DIM), dtype=np.float32)
    for i, f in enumerate(fighters):
        style = from_stats(
            sig_strikes_landed_per_min=f.get("slpm", 0),
            sig_strikes_accuracy_pct=f.get("str_acc", 0),
            sig_strikes_defense_pct=f.get("str_def", 0),
            takedown_avg_per_15=f.get("td_avg", 0),
            takedown_accuracy_pct=f.get("td_acc", 0),
            takedown_defense_pct=f.get("td_def", 0),
            submission_avg_per_15=f.get("sub_avg", 0),
            finish_rate=f.get("finish_rate", 0),
        )
        embeddings[i] = embed_fighter(
            style_vec=style,
            age=f.get("age", 30),
            height_cm=f.get("height_cm", 178),
            reach_cm=f.get("reach_cm", 183),
            wins=f.get("wins", 0),
            losses=f.get("losses", 0),
            draws=f.get("draws", 0),
            ko_wins=f.get("ko_wins", 0),
            sub_wins=f.get("sub_wins", 0),
            title_wins=f.get("title_wins", 0),
            streak=f.get("streak", 0),
            current_rank=f.get("rank"),
            is_champion=f.get("is_champion", False),
            win_quality=f.get("win_quality", 0.5),
            opp_quality=f.get("opp_quality", 0.5),
        )
    return embeddings
