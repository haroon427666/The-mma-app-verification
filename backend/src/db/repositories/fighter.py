"""FighterRepository — idempotent fighter + record + stats persistence."""

from typing import Any

from sqlalchemy import func
from sqlalchemy import select as sa_select

from src.db.models.fighter import Fighter, FighterRecord
from src.db.repositories.base import BaseRepository


class FighterRepository(BaseRepository[Fighter]):
    model = Fighter

    def _dto_to_values(self, dto: Any) -> dict[str, Any]:
        return {
            "provider": getattr(dto, "provider", "espn"),
            "external_id": getattr(dto, "external_id", ""),
            "first_name": getattr(dto, "first_name", ""),
            "last_name": getattr(dto, "last_name", ""),
            "full_name": getattr(dto, "full_name", None),
            "short_name": getattr(dto, "short_name", None),
            "nickname": getattr(dto, "nickname", None),
            "slug": getattr(dto, "slug", None),
            "weight_kg": getattr(dto, "weight_kg", None),
            "height_cm": getattr(dto, "height_cm", None),
            "reach_cm": getattr(dto, "reach_cm", None),
            "leg_reach_cm": getattr(dto, "leg_reach_cm", None),
            "stance": getattr(dto, "stance", None),
            "weight_class_name": getattr(dto, "weight_class_name", None),
            "nationality": getattr(dto, "nationality", None),
            "birth_date": getattr(dto, "birth_date", None),
            "birth_location": getattr(dto, "birth_location", None),
            "is_active": getattr(dto, "is_active", True),
            "headshot_url": getattr(dto, "headshot_url", None),
            "cutout_url": getattr(dto, "cutout_url", None),
            "render_url": getattr(dto, "render_url", None),
            "biography": getattr(dto, "biography", None),
            "ethnicity": getattr(dto, "ethnicity", None),
            "trains_at": getattr(dto, "trains_at", None),
            "fighting_style": getattr(dto, "fighting_style", None),
            "debut_date": getattr(dto, "debut_date", None),
            "record_wins": getattr(dto, "record_wins", 0),
            "record_losses": getattr(dto, "record_losses", 0),
            "record_draws": getattr(dto, "record_draws", 0),
            "record_no_contests": getattr(dto, "record_no_contests", 0),
            "facebook_url": getattr(dto, "facebook_url", None),
            "instagram_url": getattr(dto, "instagram_url", None),
            "twitter_url": getattr(dto, "twitter_url", None),
            "wikidata_id": getattr(dto, "wikidata_id", None),
            "source_provider": getattr(dto, "provider", "espn"),
        }

    # ── Filtered / Paginated List ────────────────────────────────────────

    async def list_filtered(
        self,
        *,
        filters: dict[str, object],
        limit: int = 50,
        offset: int = 0,
        sort_by: str | None = None,
        sort_dir: str = "asc",
    ) -> list[Fighter]:
        stmt = sa_select(Fighter)

        # Apply filters
        for field, value in filters.items():
            if value is None:
                continue
            if field == "search":
                stmt = stmt.where(
                    Fighter.full_name.ilike(f"%{value}%")
                    | Fighter.last_name.ilike(f"%{value}%")
                )
            elif hasattr(Fighter, field):
                stmt = stmt.where(getattr(Fighter, field) == value)

        # Sorting
        if sort_by and hasattr(Fighter, sort_by):
            col = getattr(Fighter, sort_by)
            stmt = stmt.order_by(col.asc() if sort_dir == "asc" else col.desc())
        else:
            stmt = stmt.order_by(Fighter.last_name.asc())

        stmt = stmt.limit(limit).offset(offset)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def count_filtered(self, filters: dict[str, object]) -> int:
        stmt = sa_select(func.count()).select_from(Fighter)
        for field, value in filters.items():
            if value is None:
                continue
            if field == "search":
                stmt = stmt.where(
                    Fighter.full_name.ilike(f"%{value}%")
                    | Fighter.last_name.ilike(f"%{value}%")
                )
            elif hasattr(Fighter, field):
                stmt = stmt.where(getattr(Fighter, field) == value)
        result = await self._session.execute(stmt)
        return result.scalar_one()

    # ── Record ───────────────────────────────────────────────────────────

    async def get_record(self, fighter_id: str) -> FighterRecord | None:
        result = await self._session.execute(
            sa_select(FighterRecord).where(FighterRecord.fighter_id == fighter_id)
        )
        return result.scalar_one_or_none()

    async def upsert_record(self, fighter_id: str, record: Any) -> FighterRecord:
        from sqlalchemy.dialects.postgresql import insert
        values = {
            "fighter_id": fighter_id,
            "wins": getattr(record, "wins", 0),
            "losses": getattr(record, "losses", 0),
            "draws": getattr(record, "draws", 0),
            "no_contests": getattr(record, "no_contests", 0),
            "ko_tko_wins": getattr(record, "ko_tko_wins", 0),
            "ko_tko_losses": getattr(record, "ko_tko_losses", 0),
            "submission_wins": getattr(record, "submission_wins", 0),
            "submission_losses": getattr(record, "submission_losses", 0),
            "title_wins": getattr(record, "title_wins", 0),
            "title_losses": getattr(record, "title_losses", 0),
            "title_draws": getattr(record, "title_draws", 0),
            "total_fights": getattr(record, "total_fights", 0),
            "win_percentage": getattr(record, "win_percentage", 0.0),
            "finish_rate": getattr(record, "finish_rate", 0.0),
            "record_summary": getattr(record, "record_summary", None),
        }

        stmt = (
            insert(FighterRecord)
            .values(**values)
            .on_conflict_do_update(
                constraint="uq_fighter_records_fighter_id",
                set_={k: v for k, v in values.items() if k != "fighter_id"},
            )
            .returning(FighterRecord)
        )
        result = await self._session.execute(stmt)
        await self._session.flush()
        return result.scalar_one()

    # ── Recent Fights ────────────────────────────────────────────────────

    async def get_recent_fights(self, fighter_id: str, limit: int = 20) -> list[dict[str, Any]]:
        """Get a fighter's recent + upcoming competitions with opponent data."""
        from src.db.models.event import Competition, Competitor
        from src.db.models.fighter import Fighter

        # Find all competitors for this fighter
        comp_result = await self._session.execute(
            sa_select(Competitor).where(Competitor.fighter_id == fighter_id)
        )
        competitors = list(comp_result.scalars().all())
        if not competitors:
            return []

        comp_ids = [c.competition_id for c in competitors]

        # Fetch competitions
        comps_result = await self._session.execute(
            sa_select(Competition).where(Competition.id.in_(comp_ids))
            .order_by(Competition.order_num.desc()).limit(limit)
        )
        competitions = list(comps_result.scalars().all())

        fights = []
        for comp in competitions:
            # Get both competitors for this competition
            both_result = await self._session.execute(
                sa_select(Competitor).where(Competitor.competition_id == comp.id)
            )
            both = list(both_result.scalars().all())

            # Find opponent
            opponent = next((c for c in both if c.fighter_id != fighter_id), None)
            this_corner = next((c for c in both if c.fighter_id == fighter_id), None)

            opponent_fighter = None
            if opponent:
                opp_result = await self._session.execute(
                    sa_select(Fighter).where(Fighter.id == opponent.fighter_id)
                )
                opponent_fighter = opp_result.scalar_one_or_none()

            # Get event name
            event_name = None
            event_date = None
            if comp.event_id:
                from src.db.models.event import Event
                evt_result = await self._session.execute(
                    sa_select(Event).where(Event.id == comp.event_id)
                )
                evt = evt_result.scalar_one_or_none()
                if evt:
                    event_name = evt.name
                    event_date = evt.date_utc

            fights.append({
                "competition": comp,
                "opponent": opponent_fighter,
                "corner": this_corner,
                "event_name": event_name,
                "event_date": event_date,
            })

        return fights

    # ── Simple queries ───────────────────────────────────────────────────

    async def get_active(self, limit: int = 1000) -> list[Fighter]:
        result = await self._session.execute(
            sa_select(Fighter).where(Fighter.is_active == True).limit(limit)
        )
        return list(result.scalars().all())

    async def get_by_weight_class(self, name: str) -> list[Fighter]:
        result = await self._session.execute(
            sa_select(Fighter).where(Fighter.weight_class_name == name)
        )
        return list(result.scalars().all())
