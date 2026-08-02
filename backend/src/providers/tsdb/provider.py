"""TheSportsDB Provider — Media & Bio Enrichment.

Implements the same fetch interface as ESPN but returns enrichment data.
All methods return the same DTO types — no raw JSON escapes this layer.

Design: NEVER creates records. Only enriches existing ESPN-synced records.
"""

import logging
from typing import Any

from src.providers.dto import EventDTO, FighterDTO, PromotionDTO
from src.providers.tsdb.client import TSDBClient
from src.providers.tsdb.config import TSDBClientConfig, ENDPOINTS, ESPN_TO_TSDB_LEAGUE_MAP
from src.providers.tsdb.parsers.promotion import parse_promotion, parse_promotion_enrichment
from src.providers.tsdb.parsers.event import parse_event, parse_event_enrichment
from src.providers.tsdb.parsers.fighter import parse_fighter, parse_fighter_enrichment

logger = logging.getLogger(__name__)


class TSDBProvider:
    """TheSportsDB data provider — media enrichment only."""

    def __init__(self, config: TSDBClientConfig | None = None) -> None:
        self._config = config or TSDBClientConfig()
        self._client = TSDBClient(config=self._config)

    @property
    def name(self) -> str:
        return "TheSportsDB"

    @property
    def provider_slug(self) -> str:
        return "tsdb"

    async def _ensure_started(self) -> None:
        if self._client._http is None:
            await self._client.start()

    async def close(self) -> None:
        await self._client.close()

    # ── Promotions ─────────────────────────────────────────────────────────

    async def fetch_promotions(self) -> list[PromotionDTO]:
        await self._ensure_started()
        path = ENDPOINTS["search_leagues"].format(sport=self._config.sport)
        try:
            data = await self._client.get_json(path)
            leagues = data.get("countries", []) or []
            return [parse_promotion(l) for l in leagues if isinstance(l, dict)]
        except Exception as e:
            logger.error(f"TSDB fetch_promotions failed: {e}")
            return []

    async def fetch_promotion(self, league_id: str) -> PromotionDTO | None:
        await self._ensure_started()
        path = ENDPOINTS["lookup_league"].format(league_id=league_id)
        try:
            data = await self._client.get_json(path)
            leagues = data.get("leagues", [])
            if leagues and isinstance(leagues[0], dict):
                return parse_promotion(leagues[0])
        except Exception as e:
            logger.error(f"TSDB fetch_promotion({league_id}) failed: {e}")
        return None

    async def fetch_promotion_enrichment(self, league_id: str) -> dict | None:
        """Fetch enrichment-only fields for an existing promotion."""
        await self._ensure_started()
        path = ENDPOINTS["lookup_league"].format(league_id=league_id)
        try:
            data = await self._client.get_json(path)
            leagues = data.get("leagues", [])
            if leagues and isinstance(leagues[0], dict):
                return parse_promotion_enrichment(leagues[0])
        except Exception as e:
            logger.error(f"TSDB enrichment for league {league_id} failed: {e}")
        return None

    # ── Events ─────────────────────────────────────────────────────────────

    async def fetch_events(
        self, league_id: str = "4443"  # UFC
    ) -> list[EventDTO]:
        await self._ensure_started()
        events: list[EventDTO] = []
        for endpoint_key in ["events_next_league", "events_past_league"]:
            path = ENDPOINTS[endpoint_key].format(league_id=league_id)
            try:
                data = await self._client.get_json(path)
                items = data.get("events", []) or []
                for item in items:
                    if isinstance(item, dict):
                        events.append(parse_event(item))
            except Exception as e:
                logger.error(f"TSDB {endpoint_key} failed: {e}")
        return events

    async def fetch_event_enrichment(self, event_id: str) -> dict | None:
        await self._ensure_started()
        path = ENDPOINTS["lookup_event"].format(event_id=event_id)
        try:
            data = await self._client.get_json(path)
            events = data.get("events", [])
            if events and isinstance(events[0], dict):
                return parse_event_enrichment(events[0])
        except Exception as e:
            logger.error(f"TSDB event enrichment {event_id} failed: {e}")
        return None

    # ── Fighters ───────────────────────────────────────────────────────────

    async def fetch_fighters(self) -> list[FighterDTO]:
        """Fetch fighters by iterating all UFC weight class teams."""
        await self._ensure_started()
        fighters: list[FighterDTO] = []

        # First get all UFC teams (weight classes)
        teams_path = ENDPOINTS["list_teams"].format(league_name="UFC", sport=self._config.sport)
        try:
            data = await self._client.get_json(teams_path)
            teams = data.get("teams", []) or []
            if not teams:
                logger.warning("TSDB: no UFC teams found")
                return fighters

            for team in teams:
                if not isinstance(team, dict):
                    continue
                team_id = team.get("idTeam", "")
                if not team_id:
                    continue

                # Get players for this weight class
                players_path = ENDPOINTS["list_players"].format(team_id=team_id)
                try:
                    players_data = await self._client.get_json(players_path)
                    players = players_data.get("player", []) or []
                    for p in players:
                        if isinstance(p, dict):
                            fighters.append(parse_fighter(p))
                except Exception:
                    continue  # Skip one team, continue with others
        except Exception as e:
            logger.error(f"TSDB fetch_fighters failed: {e}")

        logger.info(f"TSDB: fetched {len(fighters)} fighters")
        return fighters

    async def fetch_fighter_enrichment(self, player_id: str) -> dict | None:
        await self._ensure_started()
        path = ENDPOINTS["lookup_player"].format(player_id=player_id)
        try:
            data = await self._client.get_json(path)
            players = data.get("player", [])
            if players and isinstance(players[0], dict):
                return parse_fighter_enrichment(players[0])
        except Exception as e:
            logger.error(f"TSDB fighter enrichment {player_id} failed: {e}")
        return None
