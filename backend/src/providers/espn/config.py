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
    # GLOBAL flat listing (research: ~38,006 IDs; MUST NOT be used alone —
    # hidden profiles like DJ/Rousey/Gracie are reachable only via other refs)
    "global_athletes": f"{ESPN_BASE_URL}/athletes",
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
# Research: 49 total (48 enumerated + CES verified separately). The union census
# is 38,014 IDs. ONE Championship's ESPN slug is "ofc" — NOT "one-championship".
# "other" (~27,286 IDs) is compositionally unresolved; excluded from the active set.

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
    "ofc": "ofc",  # ONE Championship (research-verified; NOT "one-championship")
    # 49 total confirmed leagues (48 enumerated + CES). Remaining slugs resolve
    # via the live /leagues listing at sync time.
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
    """Configuration for the ESPN HTTP client.

    Rate envelope from frozen performance research (PERFORMANCE_FINAL_REPORT):
    4–8 workers at 2–5 req/sec sustained. The previous 10 rps / burst 15 was
    more aggressive than the measured safe envelope. Defaults now sit inside it.
    """

    base_url: str = ESPN_BASE_URL
    # Rate limiting — token bucket (research envelope: 2–5 req/sec sustained)
    rate_limit_per_second: float = 3.0
    burst_size: int = 6
    # Bounded concurrency for parallel resolution (research: 4–8 workers)
    max_concurrency: int = 6
    # Response cache (URL-canonicalized, in-flight dedup)
    cache_enabled: bool = True
    cache_ttl_seconds: float = 300.0
    cache_max_entries: int = 10_000
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


# ── SYNC DISCOVERY SCOPE ───────────────────────────────────────────────────────
# Which league rosters the fighter discovery enumerates (in addition to the
# global flat listing). Active/major MMA promotions per research. Overridable
# via ESPN_SYNC_LEAGUES (comma-separated).

DEFAULT_SYNC_LEAGUES: tuple[str, ...] = ("ufc", "bellator", "pfl", "ksw", "ifc", "ofc")

# Eventlog ingestion bounds (read by provider.fetch_eventlog_hooks):
# - ESPN_EVENTLOG_MAX_FIGHTERS: athletes sampled per run (default 50)
# - ESPN_EVENTLOG_MAX_PAGES: pages per athlete's eventlog (default 5 =
#   125 fights at pageSize 25; live-verified veterans span 2+ pages)


def sync_league_slugs() -> tuple[str, ...]:
    """Resolve the league roster set for athlete discovery.

    Env override wins: ESPN_SYNC_LEAGUES="ufc,bellator" etc.
    """
    import os

    raw = os.environ.get("ESPN_SYNC_LEAGUES")
    if raw:
        slugs = [s.strip() for s in raw.split(",") if s.strip()]
        if slugs:
            return tuple(slugs)
    return DEFAULT_SYNC_LEAGUES
