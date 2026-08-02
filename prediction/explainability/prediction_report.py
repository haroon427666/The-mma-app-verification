"""Prediction Report — generates comprehensive fight prediction reports.

Produces the structured output the frontend consumes.
"""

from prediction.models.confidence import ConfidenceScorer


def generate_report(prediction: dict, fight_context: dict | None = None) -> dict:
    """Generate a full prediction report for a single fight.

    Args:
        prediction: Output from FightPredictor.predict_from_fighters()
        fight_context: Event, weight class, date, etc.

    Returns:
        Structured report with winner, finish, round, methods, confidence.
    """
    prob_a = prediction.get("prob_a", 0.5)
    elo_diff = prediction.get("elo_differential", 0)

    confidence = ConfidenceScorer.get_confidence_breakdown(prob_a, elo_diff)

    report = {
        "fight": {
            "fighter_a": prediction.get("fighter_a", ""),
            "fighter_b": prediction.get("fighter_b", ""),
        },
        "prediction": {
            "winner": prediction["fighter_a"] if prob_a > 0.5 else prediction["fighter_b"],
            "probability_a": round(prob_a, 3),
            "probability_b": round(1 - prob_a, 3),
            "confidence": confidence,
        },
    }

    # Finish info
    if "finish" in prediction:
        report["finish"] = prediction["finish"]

    # Round info
    if "rounds" in prediction:
        report["rounds"] = prediction["rounds"]

    # Method info
    if "methods" in prediction:
        report["methods"] = prediction["methods"]

    # Context
    if fight_context:
        report["context"] = fight_context

    # Key factors
    report["key_factors"] = generate_key_factors(prediction, prob_a)

    return report


def generate_key_factors(prediction: dict, prob_a: float) -> list[dict]:
    """Generate the key factors that drove this prediction.

    Returns ordered list of factor → impact pairs.
    """
    factors = []

    if abs(prediction.get("elo_differential", 0)) > 100:
        edge = "fighter_a" if prediction.get("elo_differential", 0) > 0 else "fighter_b"
        factors.append({
            "factor": "Rating Advantage",
            "impact": round(min(abs(prediction.get("elo_differential", 0)) / 400 * 30, 30), 1),
            "favors": edge,
        })

    if abs(prediction.get("striking_differential", 0)) > 1.0:
        edge = "fighter_a" if prediction.get("striking_differential", 0) > 0 else "fighter_b"
        factors.append({
            "factor": "Striking Advantage",
            "impact": round(min(abs(prediction.get("striking_differential", 0)) / 4 * 20, 20), 1),
            "favors": edge,
        })

    if abs(prediction.get("grappling_differential", 0)) > 1.0:
        edge = "fighter_a" if prediction.get("grappling_differential", 0) > 0 else "fighter_b"
        factors.append({
            "factor": "Grappling Advantage",
            "impact": round(min(abs(prediction.get("grappling_differential", 0)) / 3 * 20, 20), 1),
            "favors": edge,
        })

    if prob_a > 0.55:
        factors.append({"factor": "Championship Experience", "impact": 15, "favors": "fighter_a"})
    elif prob_a < 0.45:
        factors.append({"factor": "Championship Experience", "impact": 15, "favors": "fighter_b"})

    return factors
