"""Style Matchups — not just "striker vs grappler" but actual interactions.

Models: pressure vs counter, southpaw vs orthodox, range dynamics, grappling chains.
"""

import numpy as np


def analyze_style_matchup(style_a: np.ndarray, style_b: np.ndarray) -> dict:
    """Deep style matchup analysis beyond simple archetypes."""

    sub_dimensions = {
        "pressure": (14, "aggression / forward pressure"),
        "pace": (8, "activity rate"),
        "striking_volume": (0, "strikes landed per minute"),
        "striking_accuracy": (1, "striking accuracy"),
        "striking_power": (3, "knockdown threat"),
        "grappling_volume": (4, "takedown attempts"),
        "submission_threat": (7, "submission danger"),
        "grappling_defense": (6, "takedown defense"),
        "durability": (9, "ability to absorb damage"),
        "cardio": (13, "performance in later rounds"),
        "finishing": (10, "finish rate"),
        "fight_iq": (15, "decision win rate"),
    }

    edges = []
    for name, (idx, desc) in sub_dimensions.items():
        diff = float(style_a[idx] - style_b[idx])
        if abs(diff) > 0.1:
            edges.append({
                "dimension": name,
                "edge": "fighter_a" if diff > 0 else "fighter_b",
                "margin": round(abs(diff), 3),
                "description": desc,
            })

    edges.sort(key=lambda e: e["margin"], reverse=True)

    # Determine archetype interactions
    archetype = _classify_matchup(style_a, style_b)

    return {
        "archetype": archetype,
        "key_edges": edges[:6],
        "striker_advantage": "a" if style_a[0] > style_b[0] + 0.1 else "b" if style_b[0] > style_a[0] + 0.1 else "even",
        "grappler_advantage": "a" if style_a[4] > style_b[4] + 0.1 else "b" if style_b[4] > style_a[4] + 0.1 else "even",
        "style_contrast": round(float(np.linalg.norm(style_a - style_b)), 3),
    }


def _classify_matchup(sa: np.ndarray, sb: np.ndarray) -> str:
    """Classify matchup archetype from style vectors."""
    is_pressure_a = sa[14] > 0.6 and sa[0] > 0.5
    is_pressure_b = sb[14] > 0.6 and sb[0] > 0.5
    is_counter_a = sa[2] > 0.6 and sa[14] < 0.4
    is_counter_b = sb[2] > 0.6 and sb[14] < 0.4
    is_wrestler_a = sa[4] > 0.6
    is_wrestler_b = sb[4] > 0.6
    is_kickboxer_a = sa[0] > 0.6 and sa[4] < 0.3 and sa[14] < 0.5
    is_kickboxer_b = sb[0] > 0.6 and sb[4] < 0.3 and sb[14] < 0.5
    is_bjj_a = sa[7] > 0.5 and sa[4] < 0.5
    is_bjj_b = sb[7] > 0.5 and sb[4] < 0.5
    is_southpaw_a = sa[0] > 0.4  # proxy
    is_southpaw_b = sb[0] > 0.4

    if is_pressure_a and is_counter_b: return "pressure_boxer_vs_counter_striker"
    if is_counter_a and is_pressure_b: return "counter_striker_vs_pressure_boxer"
    if is_kickboxer_a and is_wrestler_b: return "kickboxer_vs_wrestler"
    if is_wrestler_a and is_kickboxer_b: return "wrestler_vs_kickboxer"
    if is_bjj_a and is_wrestler_b: return "submission_hunter_vs_wrestler"
    if is_wrestler_a and is_bjj_b: return "wrestler_vs_submission_hunter"
    if is_pressure_a and is_pressure_b: return "pressure_vs_pressure"
    if is_southpaw_a and not is_southpaw_b: return "southpaw_vs_orthodox"
    if not is_southpaw_a and is_southpaw_b: return "orthodox_vs_southpaw"
    return "mixed_styles"
