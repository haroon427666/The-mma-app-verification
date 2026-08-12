"""FighterRepository — idempotent fighter + record + stats persistence."""

from typing import Any

from sqlalchemy import func
from sqlalchemy import select as sa_select

from src.db.models.fighter import Fighter, FighterRecord
from src.db.models.support import FighterProviderRecordStatus
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

    # ── Record-fetch status (Phase D) ────────────────────────────────────

    async def get_record_fetch_status(
        self, fighter_id: str, provider: str = "espn",
    ) -> FighterProviderRecordStatus | None:
        """Persisted record-fetch outcome for one fighter+provider, or None.

        None means either HAS_RECORD (a fighter_records row is the canonical
        signal) or NOT_CHECKED — the API layer decides via the record field.
        """
        result = await self._session.execute(
            sa_select(FighterProviderRecordStatus).where(
                FighterProviderRecordStatus.fighter_id == fighter_id,
                FighterProviderRecordStatus.provider == provider,
            )
        )
        return result.scalar_one_or_none()

    async def get_record_fetch_statuses(
        self, fighter_ids: list[str], provider: str = "espn",
    ) -> dict[str, FighterProviderRecordStatus]:
        """Batch lookup of persisted outcomes — one query, no N+1."""
        if not fighter_ids:
            return {}
        result = await self._session.execute(
            sa_select(FighterProviderRecordStatus).where(
                FighterProviderRecordStatus.fighter_id.in_(fighter_ids),
                FighterProviderRecordStatus.provider == provider,
            )
        )
        return {row.fighter_id: row for row in result.scalars().all()}

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

    async def get_next_fight(self, fighter_id: str) -> dict[str, Any] | None:
        """Nearest upcoming competition for the fighter (FTR-107).

        Semantics: the earliest bout on an event that has not finished and is
        not cancelled, ordered by event date ascending (null dates last), then
        card order. Past-dated but still-SCHEDULED events are excluded so the
        home countdown row (FTR-1508/1602) never shows a stale bout.
        """
        from datetime import UTC, datetime

        from sqlalchemy import or_

        from src.db.models.event import Competition, Competitor, Event
        from src.db.models.fighter import Fighter

        now_utc = datetime.now(UTC)
        result = await self._session.execute(
            sa_select(Competition, Event)
            .join(Event, Competition.event_id == Event.id)
            .join(Competitor, Competitor.competition_id == Competition.id)
            .where(Competitor.fighter_id == fighter_id)
            .where(Event.status.not_in(["FINAL", "CANCELLED"]))
            .where(or_(Event.date_utc >= now_utc, Event.date_utc.is_(None)))
            .order_by(Event.date_utc.asc().nulls_last(), Competition.order_num.asc())
            .limit(1)
        )
        row = result.first()
        if row is None:
            return None
        comp, event = row

        both_result = await self._session.execute(
            sa_select(Competitor).where(Competitor.competition_id == comp.id)
        )
        both = list(both_result.scalars().all())

        this_corner = next((c for c in both if c.fighter_id == fighter_id), None)
        opponent = next((c for c in both if c.fighter_id != fighter_id), None)

        opponent_fighter = None
        if opponent:
            opp_result = await self._session.execute(
                sa_select(Fighter).where(Fighter.id == opponent.fighter_id)
            )
            opponent_fighter = opp_result.scalar_one_or_none()

        return {
            "competition": comp,
            "event_id": event.id,
            "event_name": event.name,
            "event_date": event.date_utc,
            "event_status": event.status,
            "opponent": opponent_fighter,
            "corner": this_corner,
        }

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

    # ── Compare (FTR-1905/1906/1907) ────────────────────────────────────

    async def get_compare(self, fighter_a_id: str, fighter_b_id: str) -> dict[str, Any]:
        """Head-to-head bouts + common opponents for two fighters.

        Both fighters are expected to exist (the route 404s earlier). A
        competition always belongs to an event, so joins are safe.
        """
        from datetime import UTC, datetime

        from src.db.models.event import Competition, Competitor, Event

        async def fetch_rows(fighter_id: str) -> list[Any]:
            result = await self._session.execute(
                sa_select(Competitor, Competition, Event)
                .join(Competition, Competitor.competition_id == Competition.id)
                .join(Event, Competition.event_id == Event.id)
                .where(Competitor.fighter_id == fighter_id)
            )
            return list(result.all())

        rows_a = await fetch_rows(fighter_a_id)
        rows_b = await fetch_rows(fighter_b_id)

        comps_a = {r[1].id for r in rows_a}
        comps_b = {r[1].id for r in rows_b}

        # ── Head-to-head: bouts where both competed ────────────────────
        h2h_comp_ids = comps_a & comps_b
        by_comp: dict[str, dict[str, Competitor]] = {}
        for row in rows_a + rows_b:
            comp_id = row[1].id
            by_comp.setdefault(comp_id, {})[row[0].fighter_id] = row[0]

        h2h: list[dict[str, Any]] = []
        for row in rows_a:
            comp, event = row[1], row[2]
            if comp.id not in h2h_comp_ids:
                continue
            corners = by_comp[comp.id]
            h2h.append({
                "competition_id": comp.id,
                "event_id": event.id,
                "event_name": event.name,
                "event_date": event.date_utc,
                "weight_class": comp.weight_class_name,
                "is_title_fight": comp.is_title_fight or False,
                "method": comp.result_method,
                "round": comp.result_round,
                "result_a": corners[fighter_a_id].outcome,
                "result_b": corners[fighter_b_id].outcome,
            })
        h2h.sort(
            key=lambda e: (e["event_date"] is None, e["event_date"] or datetime.min.replace(tzinfo=UTC)),
            reverse=True,
        )

        # ── Common opponents: fighters who faced both ──────────────────
        common: list[dict[str, Any]] = []
        if comps_a and comps_b:
            others = list(
                (
                    await self._session.execute(
                        sa_select(Competitor, Competition, Event)
                        .join(Competition, Competitor.competition_id == Competition.id)
                        .join(Event, Competition.event_id == Event.id)
                        .where(Competition.id.in_(comps_a | comps_b))
                        .where(Competitor.fighter_id.not_in([fighter_a_id, fighter_b_id]))
                    )
                ).all()
            )

            opps_of_a = {r[0].fighter_id for r in others if r[1].id in comps_a}
            opps_of_b = {r[0].fighter_id for r in others if r[1].id in comps_b}
            common_ids = opps_of_a & opps_of_b

            if common_ids:
                fighters_result = await self._session.execute(
                    sa_select(Fighter).where(Fighter.id.in_(common_ids))
                )
                fighters_by_id = {f.id: f for f in fighters_result.scalars().all()}

                def outcomes_for(vs_side: set[str], fighter_id: str) -> list[str]:
                    bouts = [
                        (r[2].date_utc or datetime.min.replace(tzinfo=UTC), r[0].outcome)
                        for r in others
                        if r[1].id in vs_side and r[0].fighter_id == fighter_id
                    ]
                    bouts.sort(key=lambda b: b[0])
                    return [o for _, o in bouts if o]

                ordered_ids = sorted(common_ids, key=lambda i: (
                    (fighters_by_id[i].last_name or "").lower(),
                    (fighters_by_id[i].first_name or "").lower(),
                ))
                common = [
                    {
                        "fighter": fighters_by_id[fid],
                        "vs_a": outcomes_for(comps_a, fid),
                        "vs_b": outcomes_for(comps_b, fid),
                    }
                    for fid in ordered_ids
                ]
        return {"head_to_head": h2h, "common_opponents": common}
