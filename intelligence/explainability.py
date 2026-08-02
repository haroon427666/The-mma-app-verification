"""Explainability Engine — WHY does the model predict this?

Answers questions like:
    - Why does Islam have a 72% win probability against Oliveira?
    - Why is Khabib listed as similar to Islam?

Returns feature-level contributions — no black-box predictions.
"""

import numpy as np
from typing import Any


class ExplainabilityEngine:
    """Produces human-readable explanations for predictions and similarities.

    Works by decomposing the contribution of each feature dimension
    to the final prediction score.
    """

    def __init__(self):
        pass

    def explain_win_probability(
        self,
        fighter_a: dict,
        fighter_b: dict,
        matchup_vector: np.ndarray,
        weights: np.ndarray | None = None,
    ) -> dict[str, Any]:
        """Explain a win probability prediction.

        Returns feature-level contributions with human-readable labels.
        """
        if weights is None:
            weights = np.array([
                0.15, 0.10, -0.05, -0.05, 0.12, 0.05, -0.03, -0.03,
                0.05, 0.08, -0.12, 0.10, 0.15, 0.10, 0.08, 0.08,
                0.12, 0.15, 0.08, 0.00, 0.08, 0.05, 0.05, 0.00,
                0.10, 0.00, 0.00, 0.00, 0.03, 0.05, 0.03, 0.00,
            ], dtype=np.float32)

        feature_names = [
            "striking volume edge", "grappling volume edge",
            "striking accuracy contrast", "submission contrast",
            "finishing ability edge", "pace edge",
            "aggression contrast", "fight IQ contrast",
            "height advantage", "reach advantage",
            "age advantage (youth)", "experience edge",
            "win rate edge", "finish rate edge",
            "streak edge", "title experience",
            "rank percentile edge", "champion status",
            "momentum edge", "reserved",
            "win quality edge", "opponent quality edge",
            "composite quality edge", "reserved",
            "H2H edge", "H2H win rate",
            "H2H volume", "reserved",
            "same weight class", "A younger",
            "A reach advantage", "reserved",
        ]

        contributions = []
        for i, name in enumerate(feature_names):
            contrib = float(matchup_vector[i] * weights[i])
            contributions.append({
                "feature": name,
                "contribution": round(contrib, 4),
                "direction": "favors_fighter_a" if contrib > 0 else "favors_fighter_b" if contrib < 0 else "neutral",
                "magnitude": abs(round(contrib, 4)),
            })

        # Sort by impact
        contributions.sort(key=lambda c: c["magnitude"], reverse=True)

        raw = float(np.dot(matchup_vector, weights))
        probability = 1.0 / (1.0 + np.exp(-raw * 3.0))

        # Summarize top factors
        top_favor_a = [c for c in contributions[:6] if c["direction"] == "favors_fighter_a"]
        top_favor_b = [c for c in contributions[:6] if c["direction"] == "favors_fighter_b"]

        summary = []
        for c in top_favor_a[:3]:
            summary.append(f"+{c['magnitude']:.2f} {c['feature']}")
        for c in top_favor_b[:3]:
            summary.append(f"-{c['magnitude']:.2f} {c['feature']}")

        return {
            "probability_a": round(probability, 3),
            "probability_b": round(1.0 - probability, 3),
            "raw_score": round(raw, 4),
            "summary": " ".join(summary),
            "top_contributions": contributions[:10],
            "all_contributions": contributions,
        }

    def explain_similarity(
        self,
        fighter_a: dict,
        fighter_b: dict,
        similarity_score: float,
        embedding_a: np.ndarray,
        embedding_b: np.ndarray,
    ) -> dict[str, Any]:
        """Explain WHY two fighters are similar.

        Breaks down similarity by dimension group rather than individual dims.
        """
        # Group dimensions
        groups = {
            "striking style": (0, 4),
            "grappling style": (4, 8),
            "pace & aggression": (8, 12),
            "finishing & cardio": (12, 16),
            "physical attributes": (16, 24),
            "record & experience": (24, 32),
            "ranking & division": (32, 40),
            "momentum & form": (40, 48),
            "career trajectory": (48, 56),
            "fight quality": (56, 64),
        }

        group_scores = {}
        for name, (start, end) in groups.items():
            sub_a = embedding_a[start:end]
            sub_b = embedding_b[start:end]
            group_sim = float(np.dot(sub_a / (np.linalg.norm(sub_a) + 1e-10),
                                     sub_b / (np.linalg.norm(sub_b) + 1e-10)))
            group_scores[name] = {
                "similarity": round(group_sim, 3),
                "verdict": "similar" if group_sim > 0.7 else "different" if group_sim < 0.4 else "moderate",
            }

        similar = [(k, v["similarity"]) for k, v in group_scores.items() if v["verdict"] == "similar"]
        different = [(k, v["similarity"]) for k, v in group_scores.items() if v["verdict"] == "different"]

        return {
            "overall_similarity": round(similarity_score, 3),
            "verdict": "highly similar" if similarity_score > 0.85 else "similar" if similarity_score > 0.7 else "somewhat similar",
            "similar_traits": [{"trait": k, "score": v} for k, v in sorted(similar, key=lambda x: x[1], reverse=True)],
            "differentiating_traits": [{"trait": k, "score": v} for k, v in sorted(different, key=lambda x: x[1])],
            "group_breakdown": group_scores,
        }
