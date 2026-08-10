"""ESPN Athlete Eventlog Parser — payload shape from frozen research probes.

Live-verified payload (research live_probes/p19_athlete_eventlog.raw.json,
p21_gracie_eventlog.raw.json):

{
  "$ref": ".../athletes/2563796/eventlog",
  "events": {
    "count": 15, "pageIndex": 1, "pageSize": 25, "pageCount": 1,
    "items": [
      {
        "event":       {"$ref": ".../leagues/{league}/events/{event_id}"},
        "competition": {"$ref": ".../leagues/{league}/events/{event_id}/competitions/{comp_id}"},
        "competitor":  {"$ref": ".../competitions/{comp_id}/competitors/{athlete_id}"},
        "played": true
      }, ...
    ]
  }
}

The eventlog is CONTENT_DEPENDENT (P0): athletes without logged fights return
empty/unavailable. Never fabricate history — absent items → no refs.
"""

import logging
import re
from typing import Any

logger = logging.getLogger(__name__)

# .../leagues/{league}/events/{event_id} — league slug may contain dashes
_EVENT_REF_RE = re.compile(r"/leagues/(?P<league>[^/]+)/events/(?P<event_id>\d+)")

# .../competitions/{comp_id}/competitors/{athlete_id}
_ATHLETE_REF_RE = re.compile(r"/competitors/(\d+)$")


def parse_eventlog_refs(data: dict[str, Any]) -> list[dict[str, str]]:
    """Extract (league, event_id) refs from an athlete eventlog payload.

    Returns a chronological list (payload order) of:
        {"league": str, "event_id": str}
    (The competition $ref carries a competition_id, but consumers only need
    the league + event_id to re-fetch the event — competition detail comes
    embedded in the event resource.)
    Empty list when the payload has no events items (content-dependent).
    """
    refs: list[dict[str, str]] = []

    events = data.get("events", {}) or {}
    items = events.get("items", []) or []
    for item in items:
        if not isinstance(item, dict):
            continue
        event_ref = item.get("event", {}) or {}
        ref_url = event_ref.get("$ref") if isinstance(event_ref, dict) else None
        if not isinstance(ref_url, str):
            continue
        match = _EVENT_REF_RE.search(ref_url)
        if not match:
            continue

        refs.append(
            {
                "league": match.group("league"),
                "event_id": match.group("event_id"),
            }
        )

    return refs


def parse_eventlog_event_ids(data: dict[str, Any]) -> list[str]:
    """Extract just the deduplicated event IDs (convenience)."""
    seen: set[str] = set()
    result: list[str] = []
    for entry in parse_eventlog_refs(data):
        if entry["event_id"] not in seen:
            seen.add(entry["event_id"])
            result.append(entry["event_id"])
    return result


def extract_eventlog_athlete_ids(data: dict[str, Any]) -> list[str]:
    """Competitor athlete IDs from an eventlog payload (competitor $refs).

    Used to feed the discovery registry (source='eventlog') so athletes that
    only appear as eventlog competitors enter the fighter pipeline even if the
    flat listing never surfaces them. Content-dependent: absent items → empty.
    """
    seen: set[str] = set()
    events = data.get("events", {}) or {}
    items = events.get("items", []) or []
    for item in items:
        if not isinstance(item, dict):
            continue
        competitor = item.get("competitor", {}) or {}
        ref_url = (
            competitor.get("$ref") if isinstance(competitor, dict) else None
        )
        if not isinstance(ref_url, str):
            continue
        match = _ATHLETE_REF_RE.search(ref_url)
        if match:
            seen.add(match.group(1))
    return sorted(seen)
