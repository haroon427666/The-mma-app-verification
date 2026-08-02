"""Confidence Scorer — how confident is this prediction? 0-100 scale."""

import numpy as np


class ConfidenceScorer:
    """Scores prediction confidence on 0-100 scale."""

    INTERPRETATIONS = {
        (85, 100): "Very High",
        (70, 85): "High",
        (60, 70): "Moderate",
        (50, 60): "Low",
        (0, 50): "Coin Flip",
    }

    @staticmethod
    def score(win_prob: float, elo_diff: float, data_quality: float = 0.8) -> float:
        """Compute confidence score.

        Factors:
            - Win probability margin (how far from 50%)
            - Elo differential (larger gap = more confident)
            - Data quality (how much fight data backs this up)
        """
        margin = abs(win_prob - 0.5) * 2  # 0-1

        elo_confidence = min(abs(elo_diff) / 400.0, 1.0)
        raw = margin * 50 + elo_confidence * 30 + data_quality * 20
        return min(raw, 99.9)

    @staticmethod
    def interpret(score: float) -> str:
        for (lo, hi), label in ConfidenceScorer.INTERPRETATIONS.items():
            if lo <= score <= hi:
                return label
        return "Unknown"

    @staticmethod
    def get_confidence_breakdown(win_prob: float, elo_diff: float) -> dict:
        cs = ConfidenceScorer.score(win_prob, elo_diff)
        return {
            "score": round(cs, 1),
            "level": ConfidenceScorer.interpret(cs),
            "factors": {
                "probability_margin": round(abs(win_prob - 0.5) * 2 * 50, 1),
                "elo_differential": round(min(abs(elo_diff) / 400.0 * 30, 30), 1),
                "data_quality": round(20.0, 1),
            },
        }
