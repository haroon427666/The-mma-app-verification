"""Octagon API Fighter Parser.

Maps Octagon fighter fields → FighterDTO.
Octagon provides unique fields: leg_reach, trains_at, fighting_style, debut_date.
Also provides higher-quality official UFC renders (imgUrl).
"""

from datetime import datetime
from typing import Any

from src.providers.dto import FighterDTO


def _str_to_int(s: str | None) -> int:
    try:
        return int(s) if s else 0
    except (ValueError, TypeError):
        return 0


def _inches_to_cm(inches_str: str | None) -> float | None:
    try:
        return round(float(inches_str) * 2.54, 1) if inches_str else None
    except (ValueError, TypeError):
        return None


def _lbs_to_kg(lbs_str: str | None) -> float | None:
    try:
        return round(float(lbs_str) * 0.453592, 1) if lbs_str else None
    except (ValueError, TypeError):
        return None


def parse_date(date_str: str | None) -> datetime | None:
    if not date_str:
        return None
    for fmt in ["%b. %d, %Y", "%Y-%m-%d", "%B %d, %Y"]:
        try:
            return datetime.strptime(date_str, fmt)  # noqa: DTZ007 — date-only inputs, no zone
        except ValueError:
            continue
    return None


def parse_fighter(data: dict[str, Any]) -> FighterDTO:
    external_id = data.get("name", "")  # Octagon uses name as ID (no numeric IDs)
    full_name = data.get("name", "")
    parts = full_name.split(" ", 1)
    first_name = parts[0] if parts else ""
    last_name = parts[1] if len(parts) > 1 else ""

    return FighterDTO(
        provider="octagon",
        external_id=external_id,
        first_name=first_name,
        last_name=last_name,
        nickname=data.get("nickname") or None,
        weight_kg=_lbs_to_kg(data.get("weight")),
        height_cm=_inches_to_cm(data.get("height")),
        reach_cm=_inches_to_cm(data.get("reach")),
        headshot_url=data.get("imgUrl"),
        is_active=(data.get("status", "") == "Active"),
        record_wins=_str_to_int(data.get("wins")),
        record_losses=_str_to_int(data.get("losses")),
        record_draws=_str_to_int(data.get("draws")),
        record_no_contests=0,  # Octagon doesn't track NCs separately
    )


def parse_fighter_enrichment(data: dict[str, Any]) -> dict[str, Any]:
    """Extract Octagon-unique enrichment fields."""
    debut_date = parse_date(data.get("octagonDebut"))
    return {
        "nickname": data.get("nickname") or None,
        "birth_location": data.get("placeOfBirth"),
        "trains_at": data.get("trainsAt"),
        "fighting_style": data.get("fightingStyle"),
        "leg_reach_cm": _inches_to_cm(data.get("legReach")),
        "debut_date": debut_date.isoformat() if debut_date else None,
        "headshot_url": data.get("imgUrl"),
        "weight_kg": _lbs_to_kg(data.get("weight")),
        "height_cm": _inches_to_cm(data.get("height")),
        "reach_cm": _inches_to_cm(data.get("reach")),
        "age": _str_to_int(data.get("age")),
        "is_active": data.get("status") == "Active",
        "record_wins": _str_to_int(data.get("wins")),
        "record_losses": _str_to_int(data.get("losses")),
        "record_draws": _str_to_int(data.get("draws")),
    }
