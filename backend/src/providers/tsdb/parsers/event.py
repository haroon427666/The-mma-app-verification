"""TheSportsDB Event Parser.

Maps TSDB event fields → EventDTO. TSDB provides: posters, fanart,
thumbnails, banners, descriptions, local times, spectators.
"""

from datetime import datetime
from typing import Any

from src.providers.dto import EventDTO


def parse_event(data: dict[str, Any]) -> EventDTO:
    external_id = str(data.get("idEvent", ""))
    name = data.get("strEvent", "") or data.get("strEventAlternate", "")
    date = None
    raw_date = data.get("dateEvent") or data.get("strTimestamp")
    if raw_date:
        try:
            date = datetime.fromisoformat(raw_date)
        except (ValueError, TypeError):
            try:
                date = datetime.fromisoformat(raw_date[:10])
            except (ValueError, TypeError):
                pass

    status = "SCHEDULED"
    if data.get("strStatus"):
        status = data["strStatus"].upper()
    if data.get("strPostponed") == "yes":
        status = "CANCELLED"

    return EventDTO(
        provider="tsdb",
        external_id=external_id,
        name=name,
        date=date,
        status=status,
        season=str(data.get("strSeason", "")),
        short_name=None,
        slug=None,
        promotion_external_id=str(data.get("idLeague", "")),
        venue_external_id=str(data.get("idVenue", "")),
    )


def parse_event_enrichment(data: dict[str, Any]) -> dict[str, Any]:
    """Enrichment-only fields for events."""
    return {
        "poster_url": data.get("strPoster"),
        "square_url": data.get("strSquare"),
        "fanart_url": data.get("strFanart"),
        "thumbnail_url": data.get("strThumb"),
        "banner_url": data.get("strBanner"),
        "description": data.get("strDescriptionEN"),
        "spectators": data.get("intSpectators"),
        "time_local": data.get("strTimeLocal"),
        "time_utc": data.get("strTime"),
        "venue_name_inline": data.get("strVenue"),
        "city_inline": data.get("strCity"),
        "country_inline": data.get("strCountry"),
    }
