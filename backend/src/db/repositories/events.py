"""Event, Competition, Promotion, Ranking, Venue, Broadcast, WeightClass repositories."""

from typing import Any

from sqlalchemy import select as sa_select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import insert

from src.db.models.event import Event, Competition, Competitor
from src.db.models.core import Promotion, Venue, WeightClass, Ranking, Broadcast
from src.db.repositories.base import BaseRepository


class EventRepository(BaseRepository[Event]):
    model = Event

    def _dto_to_values(self, dto: Any) -> dict[str, Any]:
        return {
            "provider": getattr(dto, "provider", "espn"),
            "external_id": getattr(dto, "external_id", ""),
            "name": getattr(dto, "name", ""),
            "short_name": getattr(dto, "short_name", None),
            "slug": getattr(dto, "slug", None),
            "date_utc": getattr(dto, "date_utc", None),
            "status": getattr(dto, "status", "SCHEDULED"),
            "season": getattr(dto, "season", None),
            "promotion_id": getattr(dto, "promotion_id", None),
            "venue_id": getattr(dto, "venue_id", None),
        }

    async def list_filtered(
        self,
        *,
        filters: dict[str, object],
        limit: int = 50,
        offset: int = 0,
        sort_by: str | None = None,
        sort_dir: str = "asc",
    ) -> list[Event]:
        stmt = sa_select(Event)
        for field, value in filters.items():
            if value is None:
                continue
            if field == "search":
                stmt = stmt.where(Event.name.ilike(f"%{value}%"))
            elif field == "year":
                stmt = stmt.where(func.extract("year", Event.date_utc) == value)
            elif hasattr(Event, field):
                stmt = stmt.where(getattr(Event, field) == value)
        if sort_by and hasattr(Event, sort_by):
            col = getattr(Event, sort_by)
            stmt = stmt.order_by(col.asc() if sort_dir == "asc" else col.desc())
        else:
            stmt = stmt.order_by(Event.date_utc.desc())
        stmt = stmt.limit(limit).offset(offset)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def count_filtered(self, filters: dict[str, object]) -> int:
        stmt = sa_select(func.count()).select_from(Event)
        for field, value in filters.items():
            if value is None:
                continue
            if field == "search":
                stmt = stmt.where(Event.name.ilike(f"%{value}%"))
            elif field == "year":
                stmt = stmt.where(func.extract("year", Event.date_utc) == value)
            elif hasattr(Event, field):
                stmt = stmt.where(getattr(Event, field) == value)
        result = await self._session.execute(stmt)
        return result.scalar_one()

    async def get_upcoming(self, limit: int = 50) -> list[Event]:
        result = await self._session.execute(
            sa_select(Event).where(Event.status == "SCHEDULED")
            .order_by(Event.date_utc.asc()).limit(limit)
        )
        return list(result.scalars().all())


class CompetitionRepository(BaseRepository[Competition]):
    model = Competition

    def _dto_to_values(self, dto: Any) -> dict[str, Any]:
        return {
            "provider": getattr(dto, "provider", "espn"),
            "external_id": getattr(dto, "external_id", ""),
            "event_id": getattr(dto, "event_id", None),
            "order_num": getattr(dto, "order_num", 0),
            "card_segment": getattr(dto, "card_segment", None),
            "status": getattr(dto, "status", "SCHEDULED"),
            "is_main_event": getattr(dto, "is_main_event", False),
            "is_title_fight": getattr(dto, "is_title_fight", False),
            "weight_class_id": getattr(dto, "weight_class_id", None),
            "weight_class_name": getattr(dto, "weight_class_name", None),
            "result_method": getattr(dto, "result_method", None),
            "result_detail": getattr(dto, "result_detail", None),
            "result_round": getattr(dto, "result_round", None),
            "result_time": getattr(dto, "result_time", None),
        }

    async def upsert_competitor(self, comp_id: str, fighter_id: str, corner: str, outcome: str | None) -> Competitor:
        values = {
            "competition_id": comp_id,
            "fighter_id": fighter_id,
            "corner": corner,
            "outcome": outcome,
        }
        stmt = (
            insert(Competitor)
            .values(**values)
            .on_conflict_do_update(
                constraint="uq_competitors_comp_fighter",
                set_={"corner": corner, "outcome": outcome},
            )
            .returning(Competitor)
        )
        result = await self._session.execute(stmt)
        await self._session.flush()
        return result.scalar_one()


class PromotionRepository(BaseRepository[Promotion]):
    model = Promotion

    def _dto_to_values(self, dto: Any) -> dict[str, Any]:
        return {
            "provider": getattr(dto, "provider", "espn"),
            "external_id": getattr(dto, "external_id", ""),
            "name": getattr(dto, "name", ""),
            "abbreviation": getattr(dto, "abbreviation", None),
            "short_name": getattr(dto, "short_name", None),
            "slug": getattr(dto, "slug", None),
            "season_year": getattr(dto, "season_year", None),
            "gender": getattr(dto, "gender", None),
        }

    async def get_by_slug(self, slug: str) -> Promotion | None:
        result = await self._session.execute(
            sa_select(Promotion).where(Promotion.slug == slug)
        )
        return result.scalar_one_or_none()

    async def list_filtered(
        self, *, filters: dict[str, object] = {},
        limit: int = 50, offset: int = 0,
    ) -> list[Promotion]:
        stmt = sa_select(Promotion).limit(limit).offset(offset)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())


class VenueRepository(BaseRepository[Venue]):
    model = Venue

    def _dto_to_values(self, dto: Any) -> dict[str, Any]:
        return {
            "provider": getattr(dto, "provider", "espn"),
            "external_id": getattr(dto, "external_id", ""),
            "name": getattr(dto, "name", ""),
            "city": getattr(dto, "city", None),
            "state": getattr(dto, "state", None),
            "country": getattr(dto, "country", None),
            "latitude": getattr(dto, "latitude", None),
            "longitude": getattr(dto, "longitude", None),
            "capacity": getattr(dto, "capacity", None),
            "indoor": getattr(dto, "indoor", None),
        }

    async def list_filtered(
        self, *, filters: dict[str, object] = {},
        limit: int = 50, offset: int = 0,
    ) -> list[Venue]:
        stmt = sa_select(Venue).limit(limit).offset(offset)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_events_for_venue(self, venue_id: str, limit: int = 50) -> list[Event]:
        result = await self._session.execute(
            sa_select(Event).where(Event.venue_id == venue_id)
            .order_by(Event.date_utc.desc()).limit(limit)
        )
        return list(result.scalars().all())


class RankingRepository(BaseRepository[Ranking]):
    model = Ranking

    def _dto_to_values(self, dto: Any) -> dict[str, Any]:
        return {
            "provider": getattr(dto, "provider", "espn"),
            "fighter_id": getattr(dto, "fighter_id", None),
            "promotion_id": getattr(dto, "promotion_id", None),
            "category_name": getattr(dto, "category", ""),
            "category_type": getattr(dto, "category_type", None),
            "rank": getattr(dto, "rank", 0),
            "trend": getattr(dto, "trend", None),
            "is_champion": getattr(dto, "is_champion", False),
            "title_defenses": getattr(dto, "title_defenses", None),
            "weight_class_id": getattr(dto, "weight_class_id", None),
            "gender": getattr(dto, "gender", None),
        }

    async def replace_category(
        self, promotion_id: str, category_name: str, dtos: list[Any],
    ) -> int:
        from sqlalchemy import delete
        await self._session.execute(
            delete(Ranking).where(
                Ranking.promotion_id == promotion_id,
                Ranking.category_name == category_name,
            )
        )
        return await self.upsert_batch(dtos)


class WeightClassRepository(BaseRepository[WeightClass]):
    model = WeightClass

    def _dto_to_values(self, dto: Any) -> dict[str, Any]:
        return {
            "provider": getattr(dto, "provider", "espn"),
            "external_id": getattr(dto, "external_id", ""),
            "name": getattr(dto, "name", ""),
            "abbreviation": getattr(dto, "abbreviation", None),
        }


class BroadcastRepository(BaseRepository[Broadcast]):
    model = Broadcast

    def _dto_to_values(self, dto: Any) -> dict[str, Any]:
        return {
            "provider": getattr(dto, "provider", "espn"),
            "event_id": getattr(dto, "event_id", None),
            "network": getattr(dto, "network", ""),
            "region": getattr(dto, "region", None),
            "language": getattr(dto, "language", None),
            "broadcast_type": getattr(dto, "broadcast_type", "TV"),
        }
