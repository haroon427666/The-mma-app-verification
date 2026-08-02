"""
ESPN Ranking Parser — VERIFIED against live API 2026-08-01.

Key findings:
- /leagues/{league}/rankings returns categories as $ref URLs
- Each category resolved: {id, name, type, gender, ranks[{current, trend, athlete.$ref, hasAccolade, defenses}]}
- Uses "current" (not "rank") and "hasAccolade" (not "isChampion")
- trend: "-", "+2", etc.
- NO weightClass reference at the ranking entry level
"""

from src.providers.dto import RankingDTO
from src.providers.espn.reference import extract_id_from_ref


def parse_ranking_category(
    data: dict,
    promotion_external_id: str,
) -> list[RankingDTO]:
    """Parse a single ranking category (resolved $ref).

    Category shape (VERIFIED):
    {
        "id": "1", "name": "Men's Pound for Pound Rankings",
        "type": "pound-for-pound", "gender": "MALE",
        "ranks": [
            {"current": 1, "trend": "-", "athlete": {"$ref": "..."},
             "hasAccolade": true, "defenses": 2},
            ...
        ]
    }

    Args:
        data: Resolved JSON for one ranking category.
        promotion_external_id: ESPN league ID.

    Returns:
        List of RankingDTO (one per ranked fighter).
    """
    result: list[RankingDTO] = []

    category_name = data.get("name", "") or data.get("shortName", "")
    category_type = data.get("type", "")  # "pound-for-pound" or weight class slug

    ranks = data.get("ranks", []) or []
    for entry in ranks:
        if not isinstance(entry, dict):
            continue

        # Fighter $ref
        athlete_ref = entry.get("athlete", {}) or {}
        fighter_external_id = ""
        if isinstance(athlete_ref, dict) and "$ref" in athlete_ref:
            fighter_external_id = extract_id_from_ref(athlete_ref["$ref"])

        if not fighter_external_id:
            continue

        current_rank = entry.get("current", 0) or 0
        trend = entry.get("trend") or None  # "-", "+2", etc.
        has_accolade = entry.get("hasAccolade", False)  # champion indicator

        result.append(RankingDTO(
            provider="espn",
            fighter_external_id=fighter_external_id,
            promotion_external_id=promotion_external_id,
            category=category_name,
            rank=int(current_rank),
            trend=trend,
            is_champion=bool(has_accolade),
            weight_class_external_id=None,  # Category name identifies the division
        ))

    return result
