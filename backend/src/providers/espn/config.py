"""
ESPN API Configuration — VERIFIED against live API 2026-08-01.

All URL patterns match the real sports.core.api.espn.com API structure.
See VERIFICATION_REPORT.md for the complete endpoint catalog.
"""

from dataclasses import dataclass

# ── API Base URLs ──────────────────────────────────────────────────────────────

ESPN_BASE_URL = "https://sports.core.api.espn.com/v2/sports/mma"

# ── RESOURCE ENDPOINTS (VERIFIED) ──────────────────────────────────────────────
#
# Pattern: Every list endpoint returns items as $ref URLs.
# Each $ref must be resolved individually to get the full inline data.
# League-scoped: /leagues/{league_slug}/athletes, /leagues/{league_slug}/events
# Non-scoped: /athletes/{id}, /leagues/{slug} (these come from resolved $refs)

ENDPOINTS = {
    # ── Leagues (Promotions) ───────────────────────────────────────────────
    # List: returns 48 leagues as $ref URLs
    "leagues": f"{ESPN_BASE_URL}/leagues",
    # Detail: inline data (name, logos, season, slug, etc.)
    "league": f"{ESPN_BASE_URL}/leagues/{{league_slug}}",

    # ── Athletes (Fighters) ────────────────────────────────────────────────
    # List: league-scoped → returns $ref URLs to /athletes/{id}
    "athletes": f"{ESPN_BASE_URL}/leagues/{{league_slug}}/athletes",
    # Detail: inline data (name, weight, height, reach, weightClass, stance, etc.)
    "athlete": f"{ESPN_BASE_URL}/athletes/{{athlete_id}}",
    # Records: separate $ref → summary "28-1-0" + W/L/D/NC counts
    "athlete_records": f"{ESPN_BASE_URL}/athletes/{{athlete_id}}/records",
    # Statistics: splits.categories[{stats[{name, value, displayValue}]}]
    "athlete_statistics": f"{ESPN_BASE_URL}/athletes/{{athlete_id}}/statistics",
    # Event log: fighter's fight history (list of event appearances)
    "athlete_eventlog": f"{ESPN_BASE_URL}/athletes/{{athlete_id}}/eventlog",

    # ── Events ─────────────────────────────────────────────────────────────
    # List: league-scoped → returns $ref URLs
    "events": f"{ESPN_BASE_URL}/leagues/{{league_slug}}/events",
    # Detail: inline data + EMBEDDED competitions[] array
    "event": f"{ESPN_BASE_URL}/leagues/{{league_slug}}/events/{{event_id}}",

    # ── Competitions (Fights) — EMBEDDED in event, also linked via $ref ────
    "competition": f"{ESPN_BASE_URL}/leagues/{{league_slug}}/events/{{event_id}}/competitions/{{competition_id}}",
    # Status: result method, clock, period
    "competition_status": f"{ESPN_BASE_URL}/leagues/{{league_slug}}/events/{{event_id}}/competitions/{{competition_id}}/status",
    # Broadcasts: items[{market, media, type}]
    "competition_broadcasts": f"{ESPN_BASE_URL}/leagues/{{league_slug}}/events/{{event_id}}/competitions/{{competition_id}}/broadcasts",
    # Competitor stats: per-fight statistics
    "competitor_statistics": f"{ESPN_BASE_URL}/leagues/{{league_slug}}/events/{{event_id}}/competitions/{{competition_id}}/competitors/{{competitor_id}}/statistics",

    # ── Rankings ───────────────────────────────────────────────────────────
    # List: league-scoped → returns $ref URLs to ranking categories
    "rankings": f"{ESPN_BASE_URL}/leagues/{{league_slug}}/rankings",
    # Detail: ranks[{current, trend, athlete.$ref, hasAccolade, defenses}]
    "ranking_category": f"{ESPN_BASE_URL}/leagues/{{league_slug}}/rankings/{{category}}",

    # ── Venues ─────────────────────────────────────────────────────────────
    # Scoped under league, but also embedded in competition data
    "venue": f"{ESPN_BASE_URL}/leagues/{{league_slug}}/venues/{{venue_id}}",
}

# ── VERIFIED ESPN League Slugs ─────────────────────────────────────────────────

ESPN_LEAGUE_SLUGS: dict[str, str] = {
    "ufc": "ufc",
    "bellator": "bellator",
    "pfl": "pfl",
    "absolute": "absolute",
    "affliction": "affliction",
    "bang-fighting": "bang-fighting",
    "cage-warriors": "cage-warriors",
    "ifc": "ifc",
    "ksw": "ksw",
    "lfa": "lfa",
    "one-championship": "one-championship",
    # 48 total confirmed leagues — these are the verified active/major ones
}

# ── STATUS MAPPING (VERIFIED) ──────────────────────────────────────────────────

# From competition status endpoint: status.type.name → internal value
ESPN_STATUS_MAP: dict[str, str] = {
    "STATUS_SCHEDULED": "SCHEDULED",
    "STATUS_FINAL": "FINAL",
    "STATUS_CANCELLED": "CANCELLED",
    "STATUS_POSTPONED": "CANCELLED",
}

# ── CARD SEGMENT MAPPING (VERIFIED) ────────────────────────────────────────────
# cardSegment.name → display value
CARD_SEGMENT_MAP: dict[str, str] = {
    "main": "Main Card",
    "prelims1": "Prelims",
    "prelims2": "Early Prelims",
}

# ── RESULT METHOD MAPPING (VERIFIED from status endpoint) ──────────────────────
# status.result.name → display value (extensible — new values appear as more events sync)
RESULT_METHOD_MAP: dict[str, str] = {
    "submission": "Submission",
    "ko": "KO/TKO",
    "tko": "KO/TKO",
    "decision": "Decision",
}


# ── HTTP CLIENT CONFIGURATION ──────────────────────────────────────────────────


@dataclass
class ESPNClientConfig:
    """Configuration for the ESPN HTTP client."""

    base_url: str = ESPN_BASE_URL
    # Rate limiting — token bucket
    rate_limit_per_second: float = 10.0
    burst_size: int = 15
    # Retry
    max_retries: int = 3
    retry_backoff_base: float = 2.0
    retry_status_codes: tuple[int, ...] = (429, 500, 502, 503, 504)
    # Timeouts
    request_timeout: float = 30.0
    connect_timeout: float = 10.0
    # Circuit breaker
    circuit_breaker_threshold: int = 5
    circuit_breaker_recovery: float = 60.0
    # Pagination
    page_limit: int = 100
    # Misc
    user_agent: str = "MMA-Backend/1.0 (Production Sync Engine)"
    # Default lang/region for all requests
    default_lang: str = "en"
    default_region: str = "us"
