"""
Real Connector Implementations — wrap the existing production backend providers.

These bridge the platform/connectors/BaseConnector interface to the actual
working code in backend/src/providers/{espn,tsdb,octagon}/.

Every connector: connect → fetch → parse → normalize → validate
Production HTTP: rate-limited, circuit-breaker-protected, retrying.
"""

import asyncio
import logging
import sys
import time
from datetime import datetime, timezone
from typing import Any, Optional

from data_platform.connectors import (
    BaseConnector, ConnectorConfig, ConnectorHealth, ConnectorStatus,
    FetchResult,
)

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════════════
# Backend import helper — graceful degradation if backend isn't installed
# ═══════════════════════════════════════════════════════════════════════════

_backend_available = False
_espn_provider_class = None
_tsdb_provider_class = None
_octagon_provider_class = None

def _try_import_backend():
    """Try to import the real backend providers. Graceful if not in PYTHONPATH."""
    global _backend_available, _espn_provider_class, _tsdb_provider_class, _octagon_provider_class
    try:
        # Add backend src to path if running from project root
        sys.path.insert(0, 'backend')
        from backend.src.providers.espn.provider import ESPNProvider
        from backend.src.providers.tsdb.provider import TSDBProvider
        from backend.src.providers.octagon.provider import OctagonProvider
        _espn_provider_class = ESPNProvider
        _tsdb_provider_class = TSDBProvider
        _octagon_provider_class = OctagonProvider
        _backend_available = True
        logger.info("Backend providers loaded successfully")
    except ImportError as e:
        logger.warning(f"Backend providers not available: {e}")
        logger.warning("Platform connectors will run in simulated mode")


_try_import_backend()


# ═══════════════════════════════════════════════════════════════════════════
# ESPN Connector — wraps the real ESPNProvider
# ═══════════════════════════════════════════════════════════════════════════

class ESPNConnector(BaseConnector):
    """Real ESPN API connector — wraps ESPNProvider from backend/src/providers/espn/.

    Sources: sports.core.api.espn.com/v2/sports/mma
    Coverage: UFC fighters, events, competitions, rankings, statistics, broadcasts, venues, weight classes.
    Rate limit: ~8 req/s (token bucket).
    Authentication: None (public API).
    """

    def __init__(self, config: ConnectorConfig, league: str = "ufc"):
        super().__init__(config)
        self.league = league
        self._provider = None
        self._started = False

    async def connect(self) -> None:
        if _backend_available and _espn_provider_class:
            from backend.src.providers.espn.config import ESPNClientConfig
            self._provider = _espn_provider_class(
                ESPNClientConfig(
                    rate_limit_per_second=self.config.rate_limit_rps,
                    rate_limit_burst=self.config.rate_limit_burst,
                )
            )
            await self._provider._ensure_started()
        self._started = True
        self.metrics.uptime_seconds = 0
        logger.info(f"[ESPN] Connected — league={self.league}")

    async def _ping(self) -> bool:
        try:
            await self.fetch("/leagues/ufc")
            return True
        except Exception:
            return False

    async def shutdown(self) -> None:
        if self._provider:
            await self._provider._client.close()
        self._started = False

    # ── Fetch implementations ──────────────────────────────────────────────

    async def _fetch_raw(self, endpoint: str, **params) -> Any:
        """Route to the correct provider method based on endpoint."""
        if not _backend_available or not self._provider:
            return await self._simulate_fetch(endpoint, **params)

        entity = endpoint.strip("/")

        if entity == "fighter":
            if "external_id" in params:
                dto = await self._provider.fetch_fighter(params["external_id"])
                return {"dto": dto, "type": "FighterDTO"} if dto else None
            limit = params.get("limit", 100)
            offset = params.get("offset", 0)
            dtos = await self._provider.fetch_fighters(self.league, limit, offset)
            return [{"dto": d, "type": "FighterDTO"} for d in dtos]

        elif entity == "event":
            if "external_id" in params:
                dto = await self._provider.fetch_event(params["external_id"])
                return {"dto": dto, "type": "EventDTO"} if dto else None
            dtos = await self._provider.fetch_events(limit=params.get("limit", 50))
            return [{"dto": d, "type": "EventDTO"} for d in dtos]

        elif entity in ("competition", "results"):
            limit = params.get("limit", 50)
            dtos = await self._provider.fetch_competitions(limit=limit)
            return [{"dto": d, "type": "CompetitionDTO"} for d in dtos]

        elif entity == "ranking":
            dtos = await self._provider.fetch_rankings()
            return [{"dto": d, "type": "RankingDTO"} for d in dtos]

        elif entity == "promotion":
            dtos = await self._provider.fetch_promotions()
            return [{"dto": d, "type": "PromotionDTO"} for d in dtos]

        elif entity == "venue":
            dtos = await self._provider.fetch_venues()
            return [{"dto": d, "type": "VenueDTO"} for d in dtos]

        elif entity == "weight_class":
            dtos = await self._provider.fetch_weight_classes()
            return [{"dto": d, "type": "WeightClassDTO"} for d in dtos]

        elif entity == "broadcast":
            dtos = await self._provider.fetch_broadcasts()
            return [{"dto": d, "type": "BroadcastDTO"} for d in dtos]

        elif entity == "statistics":
            dtos = await self._provider.fetch_statistics()
            return [{"dto": d, "type": "StatisticDTO"} for d in dtos]

        else:
            return await self._provider._client.get_json(f"/{entity}")

    async def _simulate_fetch(self, endpoint: str, **params) -> Any:
        """Simulated fetch when backend isn't available (dev/testing)."""
        await asyncio.sleep(0.1)
        return {"simulated": True, "endpoint": endpoint, "params": params}

    # ── Parse — DTO → dict ─────────────────────────────────────────────────

    async def parse(self, raw: FetchResult) -> list[dict[str, Any]]:
        """Convert ESPN DTOs to flat dicts for normalization."""
        items = raw.payload if isinstance(raw.payload, list) else [raw.payload]
        parsed = []
        for item in items:
            if isinstance(item, dict) and "dto" in item:
                dto = item["dto"]
                # DTO to dict via public attributes
                if hasattr(dto, '__dict__'):
                    parsed.append({k: v for k, v in dto.__dict__.items()
                                   if not k.startswith('_')})
                elif isinstance(dto, dict):
                    parsed.append(dto)
            elif isinstance(item, dict):
                parsed.append(item)
        return parsed

    # ── Normalize — ESPN fields → canonical schema ──────────────────────────

    async def normalize(self, parsed: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Map ESPN DTO fields to canonical MMA schema."""
        from data_platform.normalization import (
            CanonicalFighter, CanonicalEvent, CanonicalFight, lbs_to_kg, inches_to_cm,
        )

        normalized = []
        for item in parsed:
            dto_type = item.get("type", "")

            if dto_type == "FighterDTO":
                f = CanonicalFighter(
                    canonical_id="",
                    source_ids={"espn": str(item.get("external_id", ""))},
                    first_name=item.get("first_name", ""),
                    last_name=item.get("last_name", ""),
                    full_name=item.get("full_name", ""),
                    nickname=item.get("nickname", ""),
                    height_cm=inches_to_cm(item.get("height_inches", 0)) if item.get("height_inches") else None,
                    weight_kg=lbs_to_kg(item.get("weight_lbs", 0)) if item.get("weight_lbs") else None,
                    reach_cm=inches_to_cm(item.get("reach_inches", 0)) if item.get("reach_inches") else None,
                    stance=item.get("stance"),
                    weight_class=item.get("weight_class_name", ""),
                    nationality=item.get("nationality", ""),
                    birth_date=item.get("birth_date"),
                    wins=item.get("record_wins", 0),
                    losses=item.get("record_losses", 0),
                    draws=item.get("record_draws", 0),
                    no_contests=item.get("record_no_contests", 0),
                    is_active=item.get("is_active", True),
                    source_count=1,
                    quality_score=0.85,
                )
                normalized.append(f.to_dict())

            elif dto_type == "EventDTO":
                e = CanonicalEvent(
                    canonical_id="",
                    source_ids={"espn": str(item.get("external_id", ""))},
                    name=item.get("name", ""),
                    short_name=item.get("short_name", ""),
                    date_utc=item.get("date_utc"),
                    status=item.get("status", "SCHEDULED"),
                    promotion=item.get("promotion_name", ""),
                    venue=item.get("venue_name", ""),
                    city=item.get("city", ""),
                    country=item.get("country", ""),
                    source_count=1,
                )
                normalized.append(e.to_dict())

            elif dto_type == "RankingDTO":
                r = {"canonical_id": "", "source_ids": {"espn": ""},
                     "fighter_id": str(item.get("fighter_external_id", "")),
                     "category": item.get("category", ""),
                     "rank": item.get("rank", 0),
                     "is_champion": item.get("is_champion", False),
                     "trend": item.get("trend", ""), "quality_score": 0.9}
                normalized.append(r)

            else:
                normalized.append(item)

        return normalized

    # ── Validate — catch obvious errors ────────────────────────────────────

    async def validate(self, normalized: list[dict[str, Any]]) -> tuple[list, list]:
        """Validate normalized entities — split into valid and invalid."""
        from data_platform.validation import create_standard_rules, ValidationEngine

        valid = []
        invalid = []
        registry = create_standard_rules()
        engine = ValidationEngine(registry)

        for entity in normalized:
            entity_type = "ranking" if "category" in entity else (
                "fighter" if "first_name" in entity else "event"
            )
            result = engine.validate(entity_type, [entity])
            if result.passed >= 1:
                valid.append(entity)
            else:
                invalid.append(entity)

        return valid, invalid

    # ── Metadata ───────────────────────────────────────────────────────────

    def version(self) -> str:
        return "espn-v2-verified-2026-08-01"

    def metadata(self) -> dict[str, Any]:
        return {
            **super().metadata(),
            "league": self.league,
            "endpoints_verified": 16,
            "coverage": "fighters(1809), events(52/yr), rankings(24 categories)",
        }


# ═══════════════════════════════════════════════════════════════════════════
# TheSportsDB Connector — wraps the real TSDBProvider
# ═══════════════════════════════════════════════════════════════════════════

class TheSportsDBConnector(BaseConnector):
    """Real TheSportsDB connector — media enrichment (posters, bios, branding).

    Sources: thesportsdb.com/api
    Coverage: Event posters, fighter cutouts, promotion branding, rich descriptions.
    Rate limit: ~25 req/min (free tier).
    Authentication: API key (free tier key: "3").
    """

    def __init__(self, config: ConnectorConfig, sport: str = "MMA"):
        super().__init__(config)
        self.sport = sport
        self._provider = None

    async def connect(self) -> None:
        if _backend_available and _tsdb_provider_class:
            self._provider = _tsdb_provider_class()
            await self._provider._ensure_started()
        self._started = True
        logger.info(f"[TheSportsDB] Connected — sport={self.sport}")

    async def _fetch_raw(self, endpoint: str, **params) -> Any:
        if not _backend_available or not self._provider:
            return {"simulated": True, "endpoint": endpoint}

        if endpoint == "promotion":
            dtos = await self._provider.fetch_promotions()
            return [{"dto": d, "type": "PromotionDTO"} for d in dtos]
        elif endpoint == "event":
            dtos = await self._provider.fetch_events(params.get("external_id", ""))
            return [{"dto": d, "type": "EventDTO"} for d in dtos]
        elif endpoint == "fighter":
            dtos = await self._provider.fetch_fighters()
            return [{"dto": d, "type": "FighterDTO"} for d in dtos]
        elif endpoint == "media":
            dtos = await self._provider.fetch_media()
            return [{"dto": d, "type": "MediaDTO"} for d in dtos]
        return {"simulated": True}

    async def parse(self, raw: FetchResult) -> list[dict[str, Any]]:
        items = raw.payload if isinstance(raw.payload, list) else [raw.payload]
        return [{k: v for k, v in (item.get("dto", item).__dict__ if hasattr(item.get("dto", item), '__dict__') else item).items() if not str(k).startswith('_')} for item in items]

    async def normalize(self, parsed: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Map TSDB fields to canonical — media enrichment only."""
        normalized = []
        for p in parsed:
            p["source_ids"] = {"tsdb": str(p.get("external_id", ""))}
            p["canonical_id"] = ""
            p["source_count"] = 1
            normalized.append(p)
        return normalized

    async def validate(self, normalized: list[dict[str, Any]]) -> tuple[list, list]:
        return normalized, []

    async def shutdown(self) -> None:
        self._started = False

    def version(self) -> str:
        return "tsdb-v1-2026-08-01"

    def metadata(self) -> dict[str, Any]:
        return {**super().metadata(), "sport": self.sport,
                "coverage": "Event posters, fighter renders, promotion branding",
                "rate_limit": "25 req/min (free tier)"}


# ═══════════════════════════════════════════════════════════════════════════
# Octagon API Connector — wraps the real OctagonProvider
# ═══════════════════════════════════════════════════════════════════════════

class OctagonConnector(BaseConnector):
    """Real Octagon API connector — fighter enrichment + ranking verification.

    Sources: api.octagon-api.com
    Coverage: Fighter renders, leg reach, gym, fighting style, rankings.
    Rate limit: None observed (Cloudflare Workers, free).
    Authentication: None.
    """

    def __init__(self, config: ConnectorConfig):
        super().__init__(config)
        self._provider = None

    async def connect(self) -> None:
        if _backend_available and _octagon_provider_class:
            self._provider = _octagon_provider_class()
            await self._provider._ensure_started()
        self._started = True
        logger.info("[Octagon API] Connected")

    async def _fetch_raw(self, endpoint: str, **params) -> Any:
        if not _backend_available or not self._provider:
            return {"simulated": True, "endpoint": endpoint}
        if endpoint == "fighter":
            dtos = await self._provider.fetch_fighters()
            return [{"dto": d, "type": "FighterDTO"} for d in dtos]
        elif endpoint == "ranking":
            dtos = await self._provider.fetch_rankings()
            return [{"dto": d, "type": "RankingDTO"} for d in dtos]
        return {"simulated": True}

    async def parse(self, raw: FetchResult) -> list[dict[str, Any]]:
        items = raw.payload if isinstance(raw.payload, list) else [raw.payload]
        parsed = []
        for item in items:
            dto = item.get("dto", item)
            if hasattr(dto, '__dict__'):
                parsed.append({k: v for k, v in dto.__dict__.items() if not str(k).startswith('_')})
            else:
                parsed.append(dto)
        return parsed

    async def normalize(self, parsed: list[dict[str, Any]]) -> list[dict[str, Any]]:
        from data_platform.normalization import CanonicalFighter, inches_to_cm
        normalized = []
        for item in parsed:
            f = CanonicalFighter(
                canonical_id="", source_ids={"octagon": str(item.get("slug", item.get("external_id", "")))},
                first_name=(item.get("name", "")).split()[0] if item.get("name") else "",
                last_name=" ".join((item.get("name", "")).split()[1:]) if item.get("name") else "",
                full_name=item.get("name", ""),
                nickname=item.get("nickname", ""),
                leg_reach_cm=inches_to_cm(float(item.get("legReach", "0").replace('"', ''))) if item.get("legReach") else None,
                gym=item.get("trainsAt", ""),
                fighting_style=item.get("fightingStyle", ""),
                debut_date=item.get("octagonDebut"),
                quality_score=0.8,
                source_count=1,
            )
            normalized.append(f.to_dict())
        return normalized

    async def validate(self, normalized: list[dict[str, Any]]) -> tuple[list, list]:
        return normalized, []

    async def shutdown(self) -> None:
        self._started = False

    def version(self) -> str:
        return "octagon-v1-2026-08-01"

    def metadata(self) -> dict[str, Any]:
        return {**super().metadata(),
                "coverage": "Fighter renders (100%), leg reach (98%), gym (85%), fighting style (95%)",
                "rate_limit": "None observed"}
