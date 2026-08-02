"""Explainability — makes every recommendation human-readable.

Returns structured reasons for recommendations.
"""


def explain_recommendation(result: dict) -> dict:
    """Convert recommendation result to API-friendly explanation."""
    reasons = result.get("reasons", [])
    score = result.get("score", 0)

    # Classify confidence
    if score > 0.85:
        confidence = "high"
    elif score > 0.60:
        confidence = "medium"
    else:
        confidence = "low"

    return {
        "id": result.get("id", ""),
        "name": result.get("name", ""),
        "type": result.get("type", ""),
        "score": round(score, 3),
        "confidence": confidence,
        "reasons": reasons,
        "image_url": result.get("image_url", ""),
        "detail": result.get("record", result.get("weight_class", "")),
    }


def explain_because(entity_name: str, source_name: str, reasons: list[str]) -> str:
    """Generate 'because you like X' explanations."""
    if not reasons:
        return f"Because you viewed {source_name}"
    top_reason = reasons[0]
    return f"Because you follow {entity_name}: {top_reason}"


def generate_contextual_reasons(entity: dict, profile: dict) -> list[str]:
    """Generate reasons based on user context and entity attributes."""
    reasons = []

    if entity.get("is_champion"):
        reasons.append("Current champion")
    if entity.get("is_title_fight"):
        reasons.append("Title fight")
    if entity.get("streak", 0) >= 3:
        reasons.append(f"On a {entity['streak']}-fight win streak")
    if entity.get("finish_rate", 0) > 0.7:
        reasons.append("High finish rate")
    if entity.get("trending_velocity", 0) > 2:
        reasons.append("Trending this week")
    if entity.get("days_until_event", 999) < 7:
        reasons.append(f"Fighting in {entity['days_until_event']} days")

    return reasons
