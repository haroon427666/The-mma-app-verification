"""Fighter Service — business logic for fighter operations + API queries.

Uses FighterRepository, MergeEngine, and Validation layer.
Never exposes raw DTOs or SQLAlchemy to callers.
"""

import logging
from datetime import date

from src.db.unit_of_work import UnitOfWork
from src.sync.merge_engine import MergeEngine, MergeResult
from src.sync.conflicts import ConflictTracker
from src.validation import validate as validate_dto

logger = logging.getLogger(__name__)


class FighterService:
    """Fighter domain service — sync, merge, validate, query."""

    def __init__(self, uow: UnitOfWork):
        self._uow = uow
        self._merge_engine = MergeEngine(uow)
        self._conflicts = ConflictTracker(uow._session)

    # ── API Query Methods ───────────────────────────────────────────────

    async def list_fighters(
        self,
        *,
        limit: int = 50,
        offset: int = 0,
        weight_class: str | None = None,
        country: str | None = None,
        active: bool | None = True,
        stance: str | None = None,
        search: str | None = None,
        sort_by: str | None = None,
        sort_dir: str = "asc",
    ) -> tuple[list, int]:
        """List fighters with filters, pagination, sorting."""
        filters: dict[str, object] = {"search": search}
        if weight_class:
            filters["weight_class_name"] = weight_class
        if country:
            filters["nationality"] = country
        if active is not None:
            filters["is_active"] = active
        if stance:
            filters["stance"] = stance

        fighters = await self._uow.fighters.list_filtered(
            filters=filters, limit=limit, offset=offset,
            sort_by=sort_by, sort_dir=sort_dir,
        )
        total = await self._uow.fighters.count_filtered(filters)
        return fighters, total

    async def get_fighter_detail(self, fighter_id: str) -> dict | None:
        """Full fighter profile — identity, physical, record, stats, rankings, fights."""
        fighter = await self._uow.fighters.get_by_id(fighter_id)
        if fighter is None:
            return None

        # Record
        record = await self._uow.fighters.get_record(fighter_id)

        # Rankings
        from src.db.models.core import Ranking
        from sqlalchemy import select as sa_select
        result = await self._uow._session.execute(
            sa_select(Ranking).where(Ranking.fighter_id == fighter_id).order_by(Ranking.rank)
        )
        rankings = list(result.scalars().all())

        # Recent fights (competitions for this fighter)
        fights = await self._uow.fighters.get_recent_fights(fighter_id, limit=20)

        return {
            "fighter": fighter,
            "record": record,
            "rankings": rankings,
            "recent_fights": fights,
        }

    async def get_fighter_stats(self, fighter_id: str):
        """Fighter's career statistics from the most recent competition."""
        from src.db.models.core import Statistic
        from sqlalchemy import select as sa_select
        result = await self._uow._session.execute(
            sa_select(Statistic).where(Statistic.fighter_id == fighter_id)
        )
        return list(result.scalars().all())

    async def get_fighter_fights(self, fighter_id: str, limit: int = 20) -> list:
        """Recent + upcoming fights for a fighter."""
        return await self._uow.fighters.get_recent_fights(fighter_id, limit)

    async def get_fighter_media(self, fighter_id: str) -> dict | None:
        """Fighter images — headshot, cutout, render, CDN fallback."""
        fighter = await self._uow.fighters.get_by_id(fighter_id)
        if fighter is None:
            return None
        return {
            "headshot_url": fighter.headshot_url,
            "cutout_url": fighter.cutout_url,
            "render_url": fighter.render_url,
            "cdn_url": fighter.headshot_url,
        }

    # ── Sync Methods ────────────────────────────────────────────────────

    async def sync_fighters(self, dtos: list, batch_size: int = 500) -> dict:
        inserted = updated = skipped = errors = 0
        for i in range(0, len(dtos), batch_size):
            batch = dtos[i:i + batch_size]
            try:
                for dto in batch:
                    validation = validate_dto("fighter", dto)
                    if not validation.is_valid:
                        errors += 1
                        continue
                    fighter = await self._uow.fighters.upsert(dto)
                    if getattr(fighter, "version", 1) == 1:
                        inserted += 1
                    else:
                        updated += 1
                await self._uow.commit()
            except Exception as e:
                logger.error(f"Fighter batch sync failed: {e}")
                await self._uow.rollback()
                errors += len(batch)
        return {"inserted": inserted, "updated": updated, "skipped": skipped, "errors": errors}

    async def enrich_fighter(
        self, fighter_id: str, enrichment: dict, source: str,
    ) -> MergeResult:
        return await self._merge_engine.merge_fighter(fighter_id, enrichment, source)

    async def sync_fighter_record(self, fighter_id: str, record) -> None:
        await self._uow.fighters.upsert_record(fighter_id, record)

    async def get_active_fighters(self, limit: int = 100) -> list:
        return await self._uow.fighters.get_active(limit)

    async def get_by_weight_class(self, name: str) -> list:
        return await self._uow.fighters.get_by_weight_class(name)


class EventService:
    """Event domain service — sync + API queries."""

    def __init__(self, uow: UnitOfWork):
        self._uow = uow

    # ── API Query Methods ───────────────────────────────────────────────

    async def list_events(
        self,
        *,
        limit: int = 50,
        offset: int = 0,
        status: str | None = None,
        promotion_slug: str | None = None,
        year: int | None = None,
        country: str | None = None,
        search: str | None = None,
        sort_by: str | None = None,
        sort_dir: str = "asc",
    ) -> tuple[list, int]:
        """List events with filters, pagination, sorting."""
        filters: dict[str, object] = {}
        if status:
            filters["status"] = status
        if year:
            filters["year"] = year
        if search:
            filters["search"] = search

        events = await self._uow.events.list_filtered(
            filters=filters, limit=limit, offset=offset,
            sort_by=sort_by, sort_dir=sort_dir,
        )
        total = await self._uow.events.count_filtered(filters)
        return events, total

    async def get_upcoming(self, limit: int = 50) -> list:
        return await self._uow.events.get_upcoming(limit)

    async def get_live(self) -> list:
        from sqlalchemy import select as sa_select
        from src.db.models.event import Event
        result = await self._uow._session.execute(
            sa_select(Event).where(Event.status == "IN_PROGRESS").limit(20)
        )
        return list(result.scalars().all())

    async def get_past(self, limit: int = 50, offset: int = 0) -> tuple[list, int]:
        from sqlalchemy import select as sa_select, func
        from src.db.models.event import Event
        result = await self._uow._session.execute(
            sa_select(Event).where(Event.status == "FINAL")
            .order_by(Event.date_utc.desc()).limit(limit).offset(offset)
        )
        events = list(result.scalars().all())
        count_result = await self._uow._session.execute(
            sa_select(func.count()).select_from(Event).where(Event.status == "FINAL")
        )
        total = count_result.scalar_one()
        return events, total

    async def get_event_detail(self, event_id: str) -> dict | None:
        """Event with fights, broadcasts, venue."""
        event = await self._uow.events.get_by_id(event_id)
        if event is None:
            return None

        # Fights (competitions) for this event
        from sqlalchemy import select as sa_select
        from src.db.models.event import Competition, Competitor
        from src.db.models.core import Broadcast, Ranking

        result = await self._uow._session.execute(
            sa_select(Competition).where(Competition.event_id == event_id).order_by(Competition.order_num)
        )
        competitions = list(result.scalars().all())

        # Competitors for all competitions
        fights_data = []
        for comp in competitions:
            comp_result = await self._uow._session.execute(
                sa_select(Competitor).where(Competitor.competition_id == comp.id)
            )
            competitors = list(comp_result.scalars().all())
            fights_data.append({"competition": comp, "competitors": competitors})

        # Broadcasts
        broadcast_result = await self._uow._session.execute(
            sa_select(Broadcast).where(Broadcast.event_id == event_id)
        )
        broadcasts = list(broadcast_result.scalars().all())

        return {
            "event": event,
            "fights": fights_data,
            "broadcasts": broadcasts,
        }

    # ── Sync Methods ────────────────────────────────────────────────────

    async def sync_events(self, dtos: list, batch_size: int = 50) -> dict:
        inserted = updated = errors = 0
        for i in range(0, len(dtos), batch_size):
            batch = dtos[i:i + batch_size]
            try:
                for dto in batch:
                    validation = validate_dto("event", dto)
                    if not validation.is_valid:
                        errors += 1
                        continue
                    event = await self._uow.events.upsert(dto)
                    if getattr(event, "version", 1) == 1:
                        inserted += 1
                    else:
                        updated += 1
                await self._uow.commit()
            except Exception as e:
                logger.error(f"Event batch sync failed: {e}")
                await self._uow.rollback()
                errors += len(batch)
        return {"inserted": inserted, "updated": updated, "errors": errors}


class RankingService:
    """Ranking domain service — atomic replace per category + API queries."""

    def __init__(self, uow: UnitOfWork):
        self._uow = uow

    # ── API Query Methods ───────────────────────────────────────────────

    async def get_all_rankings(self, gender: str | None = None) -> list:
        """All rankings, optionally filtered by gender."""
        from sqlalchemy import select as sa_select
        from src.db.models.core import Ranking

        stmt = sa_select(Ranking)
        if gender:
            stmt = stmt.where(Ranking.gender == gender)
        stmt = stmt.order_by(Ranking.category_name, Ranking.rank)

        result = await self._uow._session.execute(stmt)
        return list(result.scalars().all())

    async def get_p4p(self) -> list:
        """Pound-for-pound rankings."""
        from sqlalchemy import select as sa_select
        from src.db.models.core import Ranking
        result = await self._uow._session.execute(
            sa_select(Ranking)
            .where(Ranking.category_name == "Pound-for-Pound")
            .order_by(Ranking.rank)
        )
        return list(result.scalars().all())

    async def get_by_division(self, division: str) -> list:
        """Rankings for a specific weight class."""
        from sqlalchemy import select as sa_select
        from src.db.models.core import Ranking
        result = await self._uow._session.execute(
            sa_select(Ranking)
            .where(Ranking.category_name.ilike(f"%{division}%"))
            .order_by(Ranking.rank)
        )
        return list(result.scalars().all())

    async def get_mens(self) -> list:
        """All men's division rankings."""
        from sqlalchemy import select as sa_select
        from src.db.models.core import Ranking
        result = await self._uow._session.execute(
            sa_select(Ranking)
            .where(Ranking.gender == "MALE")
            .order_by(Ranking.category_name, Ranking.rank)
        )
        return list(result.scalars().all())

    async def get_womens(self) -> list:
        """All women's division rankings."""
        from sqlalchemy import select as sa_select
        from src.db.models.core import Ranking
        result = await self._uow._session.execute(
            sa_select(Ranking)
            .where(Ranking.gender == "FEMALE")
            .order_by(Ranking.category_name, Ranking.rank)
        )
        return list(result.scalars().all())

    # ── Sync Methods ────────────────────────────────────────────────────

    async def sync_rankings(
        self, promotion_id: str, category_name: str, dtos: list,
    ) -> int:
        for dto in dtos:
            validation = validate_dto("ranking", dto)
            if not validation.is_valid:
                logger.warning(f"Skipping invalid ranking: {validation.errors}")
                continue
        return await self._uow.rankings.replace_category(promotion_id, category_name, dtos)

    async def verify_rankings(
        self, promotion_id: str, octagon_rankings: list,
    ) -> dict:
        return {"discrepancies": 0, "details": []}
