"""
ESPN Broadcast Parser — VERIFIED against live API 2026-08-01.

Broadcasts are at competition level: /competitions/{id}/broadcasts

Response shape (VERIFIED):
{
    "items": [{
        "market": {"id": "1", "type": "National"},
        "media": {"id": "403", "name": "PPV", "callLetters": "PPV", "shortName": "PPV"},
        "type": {"id": "2", "shortName": "PPV", "longName": "Pay-Per-View"},
        "lang": "en", "region": "us"
    }]
}
"""

from typing import Any

from src.providers.dto import BroadcastDTO


def parse_broadcast(data: dict[str, Any], event_external_id: str) -> BroadcastDTO:
    """Parse a single ESPN broadcast entry.

    Args:
        data: Raw JSON for one broadcast item.
        event_external_id: ESPN event ID.

    Returns:
        BroadcastDTO.
    """
    # Network name from media
    media = data.get("media", {}) or {}
    network = (
        media.get("name")
        or media.get("callLetters")
        or media.get("shortName")
        or data.get("name", "")
    )

    # Market/region
    market = data.get("market", {}) or {}
    region = market.get("type") or data.get("region")

    language = data.get("lang")

    # Broadcast type from type.shortName or type.longName
    btype_data = data.get("type", {}) or {}
    broadcast_type = "TV"
    short_name = (btype_data.get("shortName") or "").upper()
    if "PPV" in short_name:
        broadcast_type = "PPV"
    elif "STREAM" in short_name or "ONLINE" in short_name:
        broadcast_type = "STREAMING"

    return BroadcastDTO(
        provider="espn",
        event_external_id=event_external_id,
        network=network,
        region=region,
        language=language,
        broadcast_type=broadcast_type,
    )


def parse_broadcast_list(data: dict[str, Any], event_external_id: str) -> list[BroadcastDTO]:
    """Parse broadcast items from competition broadcasts response."""
    items = data.get("items", [])
    return [parse_broadcast(item, event_external_id) for item in items]
