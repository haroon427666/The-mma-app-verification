"""
ESPN Competition (Fight) Parser — VERIFIED against live API 2026-08-01.

Key findings:
- Competitions EMBEDDED in event response (not separate $refs)
- cardSegment: {id, description:"Main Card"|"Prelims"|"Early Prelims", name:"main"|"prelims1"|"prelims2"}
- type (weight class): INLINE {id, text:"Lightweight", abbreviation:"Lightweight"}
- competitors: [{order:1|2, winner:true|false, athlete.$ref}]
- Result comes from competition status endpoint (separate fetch)
"""

from typing import Any

from src.providers.dto import CompetitionDTO, CompetitorDTO
from src.providers.espn.config import CARD_SEGMENT_MAP
from src.providers.espn.reference import extract_id_from_ref


def parse_competition(
    comp_data: dict[str, Any],
    event_external_id: str = "",
    league_slug: str = "ufc",
) -> CompetitionDTO:
    """Parse an embedded competition from an event response.

    Args:
        comp_data: Raw competition dict from event.competitions[].
        event_external_id: ESPN event ID this competition belongs to.
        league_slug: ESPN league slug (e.g. "ufc").

    Returns:
        CompetitionDTO with embedded CompetitorDTOs.
    """
    external_id = str(comp_data.get("id", ""))
    match_number = comp_data.get("matchNumber", 0) or 0

    # Card segment — map name code → display
    card_segment_raw = comp_data.get("cardSegment", {}) or {}
    card_segment = None
    if isinstance(card_segment_raw, dict):
        name_code = card_segment_raw.get("name", "")
        card_segment = CARD_SEGMENT_MAP.get(name_code, card_segment_raw.get("description"))

    # Weight class — INLINE object {id, text:"Lightweight", abbreviation:"Lightweight"}
    weight_class_data = comp_data.get("type", {}) or {}
    weight_class_external_id = None
    weight_class_name = None
    if isinstance(weight_class_data, dict):
        weight_class_external_id = str(weight_class_data.get("id", ""))
        weight_class_name = weight_class_data.get("text") or weight_class_data.get("abbreviation")

    # Title fight detection: types[] contains entries like {text:"UFC Bantamweight Title"}
    is_title_fight = False
    types = comp_data.get("types", []) or []
    for t in types:
        if isinstance(t, dict) and "title" in (t.get("text", "") or "").lower():
            is_title_fight = True
            break

    # Status — will be resolved from competition status endpoint by sync engine
    status = "SCHEDULED"
    status_data = comp_data.get("status", {}) or {}
    if isinstance(status_data, dict):
        type_data = status_data.get("type", {}) or {}
        if isinstance(type_data, dict):
            status_name = type_data.get("name", "")
            if "FINAL" in status_name:
                status = "FINAL"

    # Description: "3 Rnd (5-5-5)" or "5 Rnd (5-5-5-5-5)"
    comp_data.get("description", "")

    # Competitors
    competitors = _parse_competitors(comp_data.get("competitors", []))

    return CompetitionDTO(
        provider="espn",
        external_id=external_id,
        event_external_id=event_external_id,
        order_num=match_number,
        card_segment=card_segment,
        status=status,
        is_main_event=(match_number == 1),  # Main event is match 1
        is_title_fight=is_title_fight,
        weight_class_external_id=weight_class_external_id,
        weight_class_name=weight_class_name,
        # Result fields — filled by parse_competition_status()
        result_method=None,
        result_detail=None,
        result_round=None,
        result_time=None,
        competitors=competitors,
    )


def parse_competition_status(status_data: dict[str, Any], comp_dto: CompetitionDTO) -> CompetitionDTO:
    """Enrich a CompetitionDTO with result data from the competition status endpoint.

    Called after fetching: /competitions/{id}/status

    Status response shape (VERIFIED):
    {
        "clock": 245.0, "displayClock": "4:05", "period": 1,
        "type": {"name": "STATUS_FINAL", "completed": true},
        "result": {
            "name": "submission", "displayName": "Submission",
            "description": "D'Arce Choke"
        }
    }
    """
    if not isinstance(status_data, dict):
        return comp_dto

    # Status
    type_data = status_data.get("type", {}) or {}
    if isinstance(type_data, dict):
        name = type_data.get("name", "")
        if "FINAL" in name:
            comp_dto.status = "FINAL"
        elif "SCHEDULED" in name:
            comp_dto.status = "SCHEDULED"

    # Result
    result = status_data.get("result", {}) or {}
    if isinstance(result, dict) and result:
        comp_dto.result_method = result.get("displayName") or result.get("name")
        comp_dto.result_detail = result.get("description")
        comp_dto.result_round = status_data.get("period")
        comp_dto.result_time = status_data.get("displayClock")

    return comp_dto


def _parse_competitors(competitors_data: list[dict[str, Any]]) -> list[CompetitorDTO]:
    """Parse competitors from an embedded competition.

    Each competitor (VERIFIED):
    {
        "id": "4294924", "order": 1, "winner": true,
        "athlete": {"$ref": "http://.../athletes/4294924"}
    }
    """
    result: list[CompetitorDTO] = []

    for comp in competitors_data:
        if not isinstance(comp, dict):
            continue

        # Fighter reference — $ref URL
        athlete_ref = comp.get("athlete", {}) or {}
        fighter_external_id = ""
        if isinstance(athlete_ref, dict) and "$ref" in athlete_ref:
            fighter_external_id = extract_id_from_ref(athlete_ref["$ref"])
        elif isinstance(athlete_ref, dict) and "id" in athlete_ref:
            fighter_external_id = str(athlete_ref["id"])

        if not fighter_external_id:
            continue

        # Corner: order=1 → RED, order=2 → BLUE
        order = comp.get("order", 0)
        corner = "RED" if order == 1 else "BLUE" if order == 2 else "UNKNOWN"

        # Outcome from winner flag
        winner = comp.get("winner")
        outcome = None
        if winner is True:
            outcome = "WIN"
        elif winner is False:
            outcome = "LOSS"

        result.append(CompetitorDTO(
            fighter_external_id=fighter_external_id,
            corner=corner,
            outcome=outcome,
        ))

    return result


def extract_weight_class_from_comp(comp_data: dict[str, Any]) -> dict[str, Any] | None:
    """Extract weight class info from embedded competition type field.

    Returns dict with keys: external_id, name, abbreviation — or None.
    """
    wc = comp_data.get("type", {}) or {}
    if isinstance(wc, dict) and wc.get("id"):
        return {
            "external_id": str(wc["id"]),
            "name": wc.get("text", ""),
            "abbreviation": wc.get("abbreviation", ""),
        }
    return None
