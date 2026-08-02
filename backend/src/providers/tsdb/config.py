"""TheSportsDB API Configuration.

Sport: "Fighting" (NOT "MMA")
Free API key: "3" (30 req/min)
Premium key: user-specific (100 req/min, $9/mo)
V1 base: https://www.thesportsdb.com/api/v1/json/{key}/
V2 base: https://www.thesportsdb.com/api/v2/json/ (X-API-KEY header)
"""

from dataclasses import dataclass

TSDB_BASE_v1 = "https://www.thesportsdb.com/api/v1/json"
TSDB_BASE_v2 = "https://www.thesportsdb.com/api/v2/json"


@dataclass
class TSDBClientConfig:
    base_url: str = TSDB_BASE_v1
    api_key: str = "3"  # Free test key
    sport: str = "Fighting"
    rate_limit_per_minute: int = 25  # Leave headroom under 30/min free limit
    request_timeout: float = 15.0
    max_retries: int = 3
    retry_backoff_base: float = 2.0
    retry_status_codes: tuple = (429, 500, 502, 503, 504)
    user_agent: str = "MMA-Backend/1.0 (TheSportsDB Enrichment)"


# ── Endpoint patterns ─────────────────────────────────────────────────────────

def build_url(config: TSDBClientConfig, path: str) -> str:
    """Build full v1 URL: {base}/{key}/{path}"""
    return f"{config.base_url}/{config.api_key}/{path}"


# ── Endpoint catalog ──────────────────────────────────────────────────────────

ENDPOINTS = {
    "all_sports": "all_sports.php",
    "search_leagues": "search_all_leagues.php?s={sport}",
    "lookup_league": "lookupleague.php?id={league_id}",
    "lookup_team": "lookupteam.php?id={team_id}",
    "list_teams": "search_all_teams.php?l={league_name}&s={sport}",
    "list_players": "lookup_all_players.php?id={team_id}",
    "lookup_player": "lookupplayer.php?id={player_id}",
    "search_players": "searchplayers.php?p={name}",
    "events_next_league": "eventsnextleague.php?id={league_id}",
    "events_past_league": "eventspastleague.php?id={league_id}",
    "lookup_event": "lookupevent.php?id={event_id}",
    "events_day": "eventsday.php?d={date}&s={sport}",
    "events_season": "eventsseason.php?id={league_id}&s={season}",
    "lookup_venue": "lookupvenue.php?id={venue_id}",
}


# ── League ID mapping (confirmed via live API) ────────────────────────────────

ESPN_TO_TSDB_LEAGUE_MAP: dict[str, str] = {
    "ufc": "4443",  # UFC
    # Add more as discovered
}

TSDB_TO_ESPN_LEAGUE_MAP: dict[str, str] = {
    "4443": "ufc",  # UFC
    "4604": "jungle-fight",  # Jungle Fight (Brazil)
    "5341": "tko-mma",       # TKO MMA (Canada)
    "5702": "oktagon-mma",   # Oktagon MMA (Czechia)
}
