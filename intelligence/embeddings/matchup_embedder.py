"""Matchup Embedder — creates 32-dim vectors for fighter A vs fighter B pairs.

Encodes: style contrast, physical disparities, rank gaps, momentum delta,
historical head-to-head signals.

The matchup embedding is symmetric under (A,B) swap with a sign flip
on the directional dimensions.
"""

import numpy as np
from typing import Optional

from intelligence.embeddings.config import MATCHUP_EMBEDDING_DIM


def embed_matchup(
    emb_a: np.ndarray,
    emb_b: np.ndarray,
    same_weight_class: bool = True,
    h2h_wins_a: int = 0,
    h2h_wins_b: int = 0,
) -> np.ndarray:
    """Create a 32-dim matchup embedding from two fighter embeddings.

    Dimensions:
        [0:8]   Style contrast (element-wise difference of style subvectors)
        [8:12]  Physical disparity (height, reach, age, experience delta)
        [12:16] Record contrast (win%, finish rate, title exp, streak delta)
        [16:20] Ranking delta (rank diff, momentum diff, div strength)
        [20:24] Quality delta (win quality, opp quality diff)
        [24:28] H2H signals (prior matchups, recency-weighted)
        [28:32] Context (same weight class, age advantage, etc.)
    """
    vec = np.zeros(MATCHUP_EMBEDDING_DIM, dtype=np.float32)

    # [0:8] Style contrast (from style subvector [0:16])
    vec[0] = emb_a[0] - emb_b[0]   # striking volume diff
    vec[1] = emb_a[4] - emb_b[4]   # grappling volume diff
    vec[2] = abs(emb_a[1] - emb_b[1])  # accuracy contrast
    vec[3] = abs(emb_a[7] - emb_b[7])  # submission contrast
    vec[4] = emb_a[10] - emb_b[10]  # finishing contrast
    vec[5] = emb_a[8] - emb_b[8]    # pace contrast
    vec[6] = abs(emb_a[14] - emb_b[14])  # aggression contrast
    vec[7] = abs(emb_a[15] - emb_b[15])  # IQ contrast

    # [8:12] Physical disparity
    vec[8] = emb_a[17] - emb_b[17]   # height delta
    vec[9] = emb_a[18] - emb_b[18]   # reach delta
    vec[10] = emb_a[16] - emb_b[16]  # age delta (negative = A younger)
    vec[11] = emb_a[21] - emb_b[21]  # experience delta

    # [12:16] Record contrast
    vec[12] = emb_a[24] - emb_b[24]  # win rate delta
    vec[13] = emb_a[26] - emb_b[26]  # finish rate delta
    vec[14] = emb_a[27] - emb_b[27]  # streak delta
    vec[15] = emb_a[28] - emb_b[28]  # title experience delta

    # [16:20] Ranking delta
    vec[16] = emb_a[32] - emb_b[32]  # rank percentile delta
    vec[17] = emb_a[31] - emb_b[31]  # champion delta
    vec[18] = emb_a[33] - emb_b[33]  # momentum delta
    vec[19] = 0.0  # Reserved

    # [20:24] Quality delta
    vec[20] = emb_a[56] - emb_b[56]  # win quality delta
    vec[21] = emb_a[57] - emb_b[57]  # opp quality delta
    vec[22] = emb_a[58] - emb_b[58]  # composite quality delta
    vec[23] = 0.0  # Reserved

    # [24:28] H2H signals
    total_h2h = h2h_wins_a + h2h_wins_b
    if total_h2h > 0:
        vec[24] = (h2h_wins_a - h2h_wins_b) / total_h2h
        vec[25] = h2h_wins_a / total_h2h
    else:
        vec[24] = 0.0
        vec[25] = 0.5
    vec[26] = np.log1p(total_h2h) / np.log1p(5)  # H2H volume normalized
    vec[27] = 0.0  # Reserved

    # [28:32] Context
    vec[28] = 1.0 if same_weight_class else 0.5
    vec[29] = 1.0 if emb_a[16] < emb_b[16] else 0.0  # A is younger
    vec[30] = 1.0 if emb_a[18] > emb_b[18] else 0.0  # A has reach advantage
    vec[31] = 0.0  # Reserved

    # Normalize
    norm = np.linalg.norm(vec)
    if norm > 0:
        vec = vec / norm

    return vec


def win_probability_heuristic(matchup_vec: np.ndarray) -> float:
    """Quick win probability estimate from matchup embedding — no ML needed.

    Uses a weighted linear combination of the most predictive dimensions.
    Returns probability that fighter A wins.
    """
    weights = np.array([
        0.15, 0.10, -0.05, -0.05, 0.12, 0.05, -0.03, -0.03,  # Style [0:8]
        0.05, 0.08, -0.12, 0.10,  # Physical [8:12]
        0.15, 0.10, 0.08, 0.08,   # Record [12:16]
        0.12, 0.15, 0.08, 0.0,    # Ranking [16:20]
        0.08, 0.05, 0.05, 0.0,    # Quality [20:24]
        0.10, 0.0, 0.0, 0.0,      # H2H [24:28]
        0.03, 0.05, 0.03, 0.0,    # Context [28:32]
    ], dtype=np.float32)

    raw = np.dot(matchup_vec, weights)
    return 1.0 / (1.0 + np.exp(-raw * 3.0))  # Scaled sigmoid
