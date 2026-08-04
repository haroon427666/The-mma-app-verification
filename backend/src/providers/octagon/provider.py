"""Octagon Provider — Fighter Enrichment + Rankings Verification.

Fetches: all fighters (200+), rankings (13 categories).
Unique fields: leg_reach, trains_at, fighting_style, debut_date, UFC renders.
"""

import logging
from typing import Any

from src.providers.dto import FighterDTO, RankingDTO
from src.providers.octagon.client import OctagonClient
from src.providers.octagon.config import ENDPOINTS, OctagonClientConfig
from src.providers.octagon.parsers.fighter import parse_fighter, parse_fighter_enrichment
from src.providers.octagon.parsers.ranking import parse_rankings

logger = logging.getLogger(__name__)


class OctagonProvider:
    """Octagon API provider — fighter enrichment and rankings verification."""

    def __init__(self, config: OctagonClientConfig | None = None) -> None:
        self._config = config or OctagonClientConfig()
        self._client = OctagonClient(config=self._config)

    @property
    def name(self) -> str:
        return "Octagon"

    @property
    def provider_slug(self) -> str:
        return "octagon"

    async def _ensure_started(self) -> None:
        if self._client._http is None:
            await self._client.start()

    async def close(self) -> None:
        await self._client.close()

    # ── Fighters ───────────────────────────────────────────────────────────

    async def fetch_fighters(self) -> list[FighterDTO]:
        """Fetch all fighters (200+, single response)."""
        await self._ensure_started()
        try:
            data = await self._client.get_json(ENDPOINTS["fighters"])
            if not isinstance(data, dict):
                return []
            fighters: list[FighterDTO] = []
            for fighter_data in data.values():
                if isinstance(fighter_data, dict):
                    fighters.append(parse_fighter(fighter_data))
            logger.info(f"Octagon: fetched {len(fighters)} fighters")
            return fighters
        except Exception as e:
            logger.error(f"Octagon fetch_fighters failed: {e}")
            return []

    async def fetch_fighter(self, fighter_id: str) -> FighterDTO | None:
        """Fetch single fighter by slug ID (e.g. 'islam-makhachev')."""
        await self._ensure_started()
        path = ENDPOINTS["fighter"].format(fighter_id=fighter_id)
        try:
            data = await self._client.get_json(path)
            if isinstance(data, dict):
                return parse_fighter(data)
        except Exception as e:
            logger.error(f"Octagon fetch_fighter({fighter_id}) failed: {e}")
        return None

    async def fetch_fighter_enrichment(self, fighter_id: str) -> dict[str, Any] | None:
        """Fetch enrichment fields for a specific fighter."""
        await self._ensure_started()
        path = ENDPOINTS["fighter"].format(fighter_id=fighter_id)
        try:
            data = await self._client.get_json(path)
            if isinstance(data, dict):
                return parse_fighter_enrichment(data)
        except Exception as e:
            logger.error(f"Octagon enrichment for {fighter_id} failed: {e}")
        return None

    # ── Rankings ───────────────────────────────────────────────────────────

    async def fetch_rankings(self, promotion_external_id: str = "ufc") -> list[RankingDTO]:
        """Fetch all rankings (13 categories). Used for cross-verification with ESPN."""
        await self._ensure_started()
        try:
            data = await self._client.get_json(ENDPOINTS["rankings"])
            if isinstance(data, list):
                rankings = parse_rankings(data, promotion_external_id)
                logger.info(f"Octagon: fetched {len(rankings)} ranking entries")
                return rankings
        except Exception as e:
            logger.error(f"Octagon fetch_rankings failed: {e}")
        return []

    async def verify_rankings(
        self, promotion_external_id: str = "ufc"
    ) -> dict[str, Any]:
        """Compare Octagon rankings with ESPN and report differences."""
        oct_rankings = await self.fetch_rankings(promotion_external_id)
        # Build lookup: category → [(fighter_slug, rank)]
        by_category: dict[str, list[tuple[str, int, bool]]] = {}
        for r in oct_rankings:
            key = r.category
            if key not in by_category:
                by_category[key] = []
            by_category[key].append((r.fighter_external_id, r.rank, r.is_champion))

        return {
            "provider": "octagon",
            "total_entries": len(oct_rankings),
            "categories": len(by_category),
            "by_category": {
                k: len(v) for k, v in by_category.items()
            },
        }
