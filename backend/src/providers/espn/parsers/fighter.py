"""
ESPN Fighter (Athlete) Parser — VERIFIED against live API 2026-08-01.

Key findings from real API:
- weight is in POUNDS, height in INCHES, reach in INCHES → converted to metric
- weightClass is INLINE {id, text, shortName, slug} — NOT a $ref
- stance is INLINE {id, text} — NOT a $ref
- NO nickname field on athlete resource
- Record is under separate /athletes/{id}/records endpoint
- statistics IS a working $ref
"""

from typing import Any

from src.providers.dto import FighterDTO

# ── Unit conversions ───────────────────────────────────────────────────────────

def _lbs_to_kg(lbs: float | None) -> float | None:
    return round(lbs * 0.453592, 1) if lbs is not None else None


def _inches_to_cm(inches: float | None) -> float | None:
    return round(inches * 2.54, 1) if inches is not None else None


# ── Parser ─────────────────────────────────────────────────────────────────────


def parse_fighter(data: dict[str, Any]) -> FighterDTO:
    """Parse ESPN athlete resource → FighterDTO. All fields verified against live API.

    Args:
        data: Raw JSON from GET /athletes/{id}?lang=en&region=us

    Returns:
        FighterDTO with metric units.
    """
    external_id = str(data.get("id", ""))

    # Name
    first_name = data.get("firstName", "") or ""
    last_name = data.get("lastName", "") or ""
    display_name = data.get("displayName", "")

    # If firstName/lastName are empty, try splitting displayName
    if not first_name and display_name:
        parts = display_name.split(" ", 1)
        first_name = parts[0]
        last_name = parts[1] if len(parts) > 1 else ""

    short_name = data.get("shortName") or None

    # Physical stats → convert from imperial to metric
    weight_lbs = data.get("weight")  # float, pounds
    height_in = data.get("height")   # float, inches
    reach_in = data.get("reach")     # float, inches

    weight_kg = _lbs_to_kg(weight_lbs) if weight_lbs is not None else None
    height_cm = _inches_to_cm(height_in) if height_in is not None else None
    reach_cm = _inches_to_cm(reach_in) if reach_in is not None else None

    # Stance — INLINE object: {id: 75, text: "Orthodox"}
    stance = None
    stance_data = data.get("stance")
    if isinstance(stance_data, dict):
        stance = stance_data.get("text") or stance_data.get("description")

    # Weight class — INLINE object: {id: 970, text: "Bantamweight", shortName: "Bantamweight", slug: "bantamweight"}
    weight_class_external_id = None
    weight_class_name = None
    weight_class_data = data.get("weightClass")
    if isinstance(weight_class_data, dict):
        weight_class_external_id = str(weight_class_data.get("id", ""))
        weight_class_name = weight_class_data.get("text") or weight_class_data.get("shortName")

    # Headshot — NOT a direct field. images[] is usually empty.
    # The headshot URL comes from CDN: https://a.espncdn.com/.../athletes/{id}.png
    # or from the site API. Store a constructed fallback URL.
    headshot_url = None
    images = data.get("images", []) or []
    if images and isinstance(images, list) and len(images) > 0:
        img = images[0]
        if isinstance(img, dict):
            headshot_url = img.get("href") or img.get("url")

    # Nationality — from citizenship
    nationality = None
    citizenship = data.get("citizenship", {})
    if isinstance(citizenship, dict):
        nationality = citizenship.get("country")

    # Birth date
    birth_date = None
    dob = data.get("dateOfBirth")
    if dob:
        from datetime import datetime
        try:
            birth_date = datetime.fromisoformat(dob)
        except (ValueError, TypeError):
            pass

    # Status — presence-guarded: only set when the payload explicitly
    # provides `active` (research: active status is not guaranteed on all
    # athlete resources; a blind default would mislabel every fighter).
    active_raw = data.get("active")
    is_active: bool | None = (
        bool(active_raw) if isinstance(active_raw, bool) else None
    )

    # Record is NOT here — must be fetched from /athletes/{id}/records
    # We set defaults; the sync engine will resolve and update
    return FighterDTO(
        provider="espn",
        external_id=external_id,
        first_name=first_name,
        last_name=last_name,
        nickname=None,  # ESPN athlete resource has NO nickname field
        short_name=short_name,
        record_wins=0,    # Filled by parse_fighter_records()
        record_losses=0,
        record_draws=0,
        record_no_contests=0,
        height_cm=height_cm,
        weight_kg=weight_kg,
        reach_cm=reach_cm,
        stance=stance,
        nationality=nationality,
        birth_date=birth_date,
        headshot_url=headshot_url,
        is_active=is_active,
        weight_class_external_id=weight_class_external_id,
        weight_class_name=weight_class_name,
    )


def parse_fighter_records(records_data: dict[str, Any]) -> dict[str, int]:
    """Parse the /athletes/{id}/records response to extract W/L/D/NC.

    The response has items[{name:"overall", summary:"28-1-0",
        stats[{name:"wins",value:28}, {name:"losses",value:1}, ...]}]

    Returns:
        dict with keys: wins, losses, draws, no_contests
    """
    result = {"wins": 0, "losses": 0, "draws": 0, "no_contests": 0}

    items = records_data.get("items", [])
    for item in items:
        if not isinstance(item, dict):
            continue
        if item.get("name") != "overall":
            continue

        stats = item.get("stats", [])
        for stat in stats:
            if not isinstance(stat, dict):
                continue
            name = stat.get("name", "")
            value = int(stat.get("value", 0))
            if name == "wins":
                result["wins"] = value
            elif name == "losses":
                result["losses"] = value
            elif name == "draws":
                result["draws"] = value
            elif name == "noContests":
                result["no_contests"] = value

    return result
