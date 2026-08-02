"""
ESPN Venue Parser — VERIFIED against live API 2026-08-01.

Venues are embedded in competition data within events:
    venue: {id, fullName, address: {city, state, country}, indoor, grass}

They can also be resolved from event.venues[] $ref array.
"""

from src.providers.dto import VenueDTO


def parse_venue(data: dict) -> VenueDTO:
    """Parse venue from embedded competition data or resolved $ref.

    Args:
        data: Raw JSON — either embedded venue or resolved venue $ref.

    Returns:
        VenueDTO.
    """
    external_id = str(data.get("id", ""))
    name = data.get("fullName", "") or data.get("name", "") or data.get("displayName", "")

    # Address
    address = data.get("address", {}) or {}
    city = address.get("city") if isinstance(address, dict) else None
    state = address.get("state") if isinstance(address, dict) else None
    country = address.get("country") if isinstance(address, dict) else None

    # Coordinates — may not be in embedded data
    latitude = None
    longitude = None
    geo = data.get("geometry", {}) or data.get("coordinates", {}) or {}
    if isinstance(geo, dict):
        lat = geo.get("latitude")
        lng = geo.get("longitude")
        latitude = float(lat) if lat is not None else None
        longitude = float(lng) if lng is not None else None

    capacity = data.get("capacity")

    return VenueDTO(
        provider="espn",
        external_id=external_id,
        name=name,
        city=city,
        state=state,
        country=country,
        latitude=latitude,
        longitude=longitude,
        capacity=int(capacity) if capacity is not None else None,
    )
