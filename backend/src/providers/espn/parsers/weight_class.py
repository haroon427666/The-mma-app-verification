"""
ESPN Weight Class Parser — VERIFIED against live API 2026-08-01.

Weight classes are extracted from INLINE data in:
- athlete.weightClass: {id, text, shortName, slug}
- competition.type: {id, text, abbreviation}

There is no dedicated weight class endpoint; they're collected during sync.
"""

from typing import Any

from src.providers.dto import WeightClassDTO


def parse_weight_class(data: dict[str, Any]) -> WeightClassDTO:
    """Parse weight class from inline data (athlete or competition).

    Args:
        data: Dict with keys: id, text (or name), abbreviation (or shortName).

    Returns:
        WeightClassDTO.
    """
    external_id = str(data.get("id", ""))
    name = data.get("text") or data.get("name") or ""
    abbreviation = data.get("abbreviation") or data.get("shortName") or name[:5]

    return WeightClassDTO(
        provider="espn",
        external_id=external_id,
        name=name,
        abbreviation=abbreviation,
        min_weight_kg=None,   # Not exposed in ESPN inline data
        max_weight_kg=None,
        gender=None,           # Only available in ranking category context
    )


def parse_weight_class_from_athlete(athlete_data: dict[str, Any]) -> WeightClassDTO | None:
    """Extract weight class from athlete.weightClass inline object."""
    wc = athlete_data.get("weightClass", {}) or {}
    if isinstance(wc, dict) and wc.get("id"):
        return parse_weight_class(wc)
    return None


def parse_weight_class_from_competition(comp_data: dict[str, Any]) -> WeightClassDTO | None:
    """Extract weight class from competition.type inline object."""
    wc = comp_data.get("type", {}) or {}
    if isinstance(wc, dict) and wc.get("id"):
        return parse_weight_class(wc)
    return None
