"""
ESPN Event Parser — VERIFIED against live API 2026-08-01.

Key finding: competitions[] is EMBEDDED in the event response (not separate $refs).
Each competition has full inline data with: competitors, cardSegment, type (weight class), venue.
"""

from datetime import datetime

from src.providers.dto import EventDTO
from src.providers.espn.config import ESPN_STATUS_MAP
from src.providers.espn.reference import extract_id_from_ref


def parse_event(data: dict) -> EventDTO:
    """Parse ESPN event resource → EventDTO.

    Args:
        data: Raw JSON from GET /leagues/{league}/events/{id}?lang=en&region=us

    Returns:
        EventDTO. Competitors are parsed separately via parse_competition().
    """
    external_id = str(data.get("id", ""))
    name = data.get("name", "") or data.get("shortName", "")
    short_name = data.get("shortName") or None

    # Date — UTC timestamp string
    date = None
    raw_date = data.get("date")
    if raw_date:
        try:
            date = datetime.fromisoformat(raw_date.replace("Z", "+00:00"))
        except (ValueError, TypeError):
            pass

    # Status — event.status.type.name
    status = "SCHEDULED"
    status_data = data.get("status", {})
    if isinstance(status_data, dict):
        type_data = status_data.get("type", {})
        if isinstance(type_data, dict):
            espn_status = type_data.get("name", "")
            status = ESPN_STATUS_MAP.get(espn_status, "SCHEDULED")

    # Slug — from the $ref URL or construct
    slug = data.get("slug", "")
    if not slug:
        slug = _build_slug(name, date)

    # Promotion reference
    promotion_external_id = None
    league_data = data.get("league", {})
    if isinstance(league_data, dict) and "$ref" in league_data:
        promotion_external_id = extract_id_from_ref(league_data["$ref"])

    # Venue reference (from event.venues[] — first venue)
    venue_external_id = None
    venues = data.get("venues", [])
    if venues and isinstance(venues, list):
        first_venue = venues[0]
        if isinstance(first_venue, dict) and "$ref" in first_venue:
            venue_external_id = extract_id_from_ref(first_venue["$ref"])

    return EventDTO(
        provider="espn",
        external_id=external_id,
        name=name,
        short_name=short_name,
        date=date,
        status=status,
        slug=slug,
        promotion_external_id=promotion_external_id,
        venue_external_id=venue_external_id,
    )


def _build_slug(name: str, date: datetime | None) -> str:
    """Build a URL-safe slug from event name and year."""
    year = date.year if date else "unknown"
    base = name.lower().replace(" ", "-").replace(":", "").replace(".", "")
    return f"{base}-{year}"


def extract_competitions_from_event(event_data: dict) -> list[dict]:
    """Extract the embedded competitions array from an event response.

    Args:
        event_data: Full event JSON response.

    Returns:
        List of raw competition dicts from the event's competitions[] array.
    """
    return event_data.get("competitions", []) or []


def extract_venue_id_from_competition(comp_data: dict) -> str | None:
    """Extract venue external ID from an embedded competition.

    Venue is embedded in each competition: venue.{id, fullName, address}
    We use the id field as the external_id.
    """
    venue = comp_data.get("venue", {})
    if isinstance(venue, dict) and "id" in venue:
        return str(venue["id"])
    return None
