"""Matchup Engine — win probability, finish probability, style analysis.

Combines Elo, feature pipelines, and heuristic models.
No ML required for the heuristic version. ML pipeline in ml-platform/.
"""

import numpy as np
from intelligence.embeddings.matchup_embedder import win_probability_heuristic


def predict_win_probability(
    emb_a: np.ndarray,
    emb_b: np.ndarray,
    h2h_wins_a: int = 0,
    h2h_wins_b: int = 0,
) -> float:
    """Predict probability that fighter A wins. Returns [0, 1]."""
    from intelligence.embeddings.matchup_embedder import embed_matchup
    matchup = embed_matchup(emb_a, emb_b, h2h_wins_a=h2h_wins_a, h2h_wins_b=h2h_wins_b)
    return win_probability_heuristic(matchup)


def predict_finish_probability(
    finish_rate_a: float,
    finish_rate_b: float,
    opp_durability_a: float = 0.5,
    opp_durability_b: float = 0.5,
) -> tuple[float, float]:
    """Predict finish probability for both fighters. Returns (finish_by_a, finish_by_b)."""
    a_finish = finish_rate_a * (1.0 - opp_durability_b * 0.5)
    b_finish = finish_rate_b * (1.0 - opp_durability_a * 0.5)
    total = a_finish + b_finish + 0.01
    return a_finish / total, b_finish / total


def predict_method_probability(
    ko_rate_a: float, sub_rate_a: float, dec_rate_a: float,
    ko_rate_b: float, sub_rate_b: float, dec_rate_b: float,
) -> dict:
    """Predict probability for each method of victory. Returns dict with method probs."""
    # Weighted by fighter strengths
    a_win_prob = 0.5  # Replace with actual win prob
    b_win_prob = 0.5

    return {
        "a_ko_tko": a_win_prob * ko_rate_a,
        "a_submission": a_win_prob * sub_rate_a,
        "a_decision": a_win_prob * dec_rate_a,
        "b_ko_tko": b_win_prob * ko_rate_b,
        "b_submission": b_win_prob * sub_rate_b,
        "b_decision": b_win_prob * dec_rate_b,
    }


def style_matchup_analysis(
    style_a: np.ndarray,
    style_b: np.ndarray,
) -> dict:
    """Analyze the stylistic matchup between two fighters.

    Returns: dict with keys like "striker_vs_grappler", style contrast, etc.
    """
    from intelligence.embeddings.style_vector import style_label

    is_striker_a = style_a[0] > 0.5 and style_a[4] < 0.3
    is_grappler_a = style_a[4] > 0.5 and style_a[0] < 0.4
    is_striker_b = style_b[0] > 0.5 and style_b[4] < 0.3
    is_grappler_b = style_b[4] > 0.5 and style_b[0] < 0.4

    if is_striker_a and is_grappler_b:
        archetype = "striker_vs_grappler"
    elif is_grappler_a and is_striker_b:
        archetype = "grappler_vs_striker"
    elif is_striker_a and is_striker_b:
        archetype = "striker_vs_striker"
    elif is_grappler_a and is_grappler_b:
        archetype = "grappler_vs_grappler"
    else:
        archetype = "mixed"

    style_diff = float(np.linalg.norm(style_a - style_b))

    return {
        "archetype": archetype,
        "fighter_a_style": style_label(style_a),
        "fighter_b_style": style_label(style_b),
        "style_contrast": round(style_diff, 3),
        "likely_striking_heavy": archetype in ("striker_vs_striker", "striker_vs_grappler"),
        "likely_grappling_heavy": archetype in ("grappler_vs_grappler", "grappler_vs_striker"),
        "striker_advantage": "a" if style_a[0] > style_b[0] else "b" if style_b[0] > style_a[0] else "even",
        "grappler_advantage": "a" if style_a[4] > style_b[4] else "b" if style_b[4] > style_a[4] else "even",
    }
