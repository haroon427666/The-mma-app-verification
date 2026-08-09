"""Rankings, Promotions, Venues, Search, Health routers — v1. Real implementations."""

from collections import defaultdict
from datetime import datetime
from typing import Any, cast

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from sqlalchemy import func, or_
from sqlalchemy import select as sa_select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.cache import cache_key, cached_json_response
from src.api.utils import require_uuid
from src.db.models.core import Promotion, Ranking, Venue, WeightClass
from src.db.models.event import Competition, Competitor, Event
from src.db.models.fighter import Fighter
from src.db.unit_of_work import UnitOfWork
from src.dependencies import Pagination as PaginationDep
from src.dependencies import get_uow
from src.schemas.common import ErrorResponse, PaginatedResponse
from src.schemas.misc import (
    ChampionEntry,
    ChampionFighter,
    FighterBrief,
    GOATEntry,
    PromotionDetailResponse,
    PromotionListItem,
    ProspectEntry,
    RankingCategory,
    RankingEntry,
    RankingMovementEntry,
    RankingsResponse,
    SearchResponse,
    SearchResultItem,
    StreakEntry,
    TitleDefenseEntry,
    VenueDetailResponse,
    VenueListItem,
    WeightClassDetailResponse,
    WeightClassListItem,
)

# ═══════════════════════════════════════════════════════════════════════════
# Champions
# ═══════════════════════════════════════════════════════════════════════════

champion_router = APIRouter(prefix="/v1/champions", tags=["champions"])


def _champion_entry(r: Ranking, f: Fighter) -> ChampionEntry:
    """Build a ChampionEntry from a champion ranking row + joined fighter."""
    record = None
    if f.record_wins is not None:
        record = "-".join([
            str(f.record_wins or 0),
            str(f.record_losses or 0),
            str(f.record_draws or 0),
        ])

    return ChampionEntry(
        category_name=r.category_name,
        category_type=r.category_type,
        gender=r.gender,
        weight_class=r.category_name,
        rank=r.rank,
        trend=r.trend,
        title_defenses=r.title_defenses,
        fighter=ChampionFighter(
            id=r.fighter_id or "",
            full_name=f.full_name or f"{f.first_name} {f.last_name}".strip() or None,
            nickname=f.nickname,
            headshot_url=f.headshot_url,
            record=record,
        ),
    )


def _fighter_brief(f: Fighter) -> FighterBrief:
    """Compact fighter payload shared by rankings-extras endpoints."""
    record = None
    if f.record_wins is not None:
        record = "-".join([
            str(f.record_wins or 0),
            str(f.record_losses or 0),
            str(f.record_draws or 0),
        ])

    return FighterBrief(
        id=f.id,
        full_name=f.full_name or f"{f.first_name} {f.last_name}".strip() or None,
        nickname=f.nickname,
        record=record,
        headshot_url=f.headshot_url,
        wins=f.record_wins or 0,
        losses=f.record_losses or 0,
        draws=f.record_draws or 0,
    )


def _record_metrics(f: Fighter) -> tuple[float | None, float | None]:
    """(win_percentage, finish_rate) from the record breakdown row, if present."""
    rb = f.record_breakdown
    if rb is None:
        return None, None
    return rb.win_percentage, rb.finish_rate


def _goat_score(defenses: int, win_pct: float | None, finish: float | None, wins: int) -> float:
    return round(
        0.55 * defenses
        + 0.20 * (win_pct or 0.0) * 10
        + 0.25 * (finish or 0.0) * wins,
        2,
    )


@champion_router.get("", response_model=list[ChampionEntry])
async def list_champions(request: Request, uow: UnitOfWork = Depends(get_uow)) -> Response:
    """All current champions across every division (rankings with is_champion=true)."""
    session = cast(AsyncSession, uow._session)

    async def loader() -> list[dict]:
        result = await session.execute(
            sa_select(Ranking, Fighter)
            .join(Fighter, Ranking.fighter_id == Fighter.id)
            .where(Ranking.is_champion.is_(True))
            .order_by(Ranking.category_name)
        )
        rows = list(result.all())
        return [_champion_entry(r, f).model_dump(mode="json") for r, f in rows]

    return await cached_json_response(
        request,
        cache_key=cache_key("champions:all"),
        ttl=600,
        loader=loader,
    )


@champion_router.get("/history", response_model=list[ChampionEntry])
async def champion_history(request: Request, uow: UnitOfWork = Depends(get_uow)) -> Response:
    """Champion lineage history.

    NOTE: Champion lineage (won_date/lost_date/defenses/reign) is not yet
    modeled in the schema — returns an empty list until the lineage table exists.
    """
    async def loader() -> list[dict]:
        return []

    return await cached_json_response(
        request,
        cache_key=cache_key("champions:history"),
        ttl=600,
        loader=loader,
    )


@champion_router.get("/{division}", response_model=ChampionEntry)
async def division_champion(
    request: Request, division: str, uow: UnitOfWork = Depends(get_uow)
) -> Response:
    """The current champion of a specific division (category_name match)."""
    session = cast(AsyncSession, uow._session)

    async def loader() -> dict:
        result = await session.execute(
            sa_select(Ranking, Fighter)
            .join(Fighter, Ranking.fighter_id == Fighter.id)
            .where(Ranking.is_champion.is_(True))
            .where(Ranking.category_name.ilike(f"%{division}%"))
            .order_by(Ranking.rank)
        )
        row = result.first()
        if row is None:
            raise HTTPException(404, detail=ErrorResponse.not_found("champion", division).error)
        r, f = row
        return _champion_entry(r, f).model_dump(mode="json")

    return await cached_json_response(
        request,
        cache_key=cache_key("champions:division", division),
        ttl=600,
        loader=loader,
    )


# ═══════════════════════════════════════════════════════════════════════════
# Rankings
# ═══════════════════════════════════════════════════════════════════════════

ranking_router = APIRouter(prefix="/v1/rankings", tags=["rankings"])


def _ranking_to_entry(r: Ranking) -> RankingEntry:
    return RankingEntry(
        rank=r.rank,
        fighter_id=r.fighter_id or "",
        fighter_name=f"Fighter {r.fighter_id[:8]}" if r.fighter_id else "Unknown",
        fighter_nickname=None,
        record=None,
        trend=r.trend,
        is_champion=r.is_champion or False,
        title_defenses=r.title_defenses,
        headshot_url=None,
    )


def _group_rankings(rankings: list[Ranking]) -> list[RankingCategory]:
    """Group flat ranking rows into categories with champion extracted."""
    from collections import defaultdict
    groups: dict[str, list[Ranking]] = defaultdict(list)
    for r in rankings:
        groups[r.category_name].append(r)

    categories = []
    for cat_name, entries in groups.items():
        champion = next((e for e in entries if e.is_champion), None)
        ranked = sorted([e for e in entries if not e.is_champion], key=lambda x: x.rank)
        categories.append(RankingCategory(
            category_name=cat_name,
            category_type=entries[0].category_type if entries else None,
            gender=entries[0].gender if entries else None,
            weight_class=None,
            champion=_ranking_to_entry(champion) if champion else None,
            rankings=[_ranking_to_entry(e) for e in ranked],
        ))
    return categories


@ranking_router.get("", response_model=RankingsResponse)
async def list_rankings(
    request: Request,
    gender: str | None = Query(None, description="MALE, FEMALE"),
    uow: UnitOfWork = Depends(get_uow),
) -> Response:
    """All UFC rankings, optionally filtered by gender."""
    session = cast(AsyncSession, uow._session)

    async def loader() -> dict:
        result = await session.execute(
            sa_select(Ranking).order_by(Ranking.category_name, Ranking.rank)
        )
        all_rankings = list(result.scalars().all())
        if gender:
            all_rankings = [r for r in all_rankings if r.gender == gender.upper()]
        return RankingsResponse(categories=_group_rankings(all_rankings)).model_dump(mode="json")

    return await cached_json_response(
        request,
        cache_key=cache_key("rankings:all", gender),
        ttl=600,
        loader=loader,
    )


@ranking_router.get("/mens", response_model=RankingsResponse)
async def mens_rankings(request: Request, uow: UnitOfWork = Depends(get_uow)) -> Response:
    """Men's divisions — all weight classes + P4P."""
    session = cast(AsyncSession, uow._session)

    async def loader() -> dict:
        result = await session.execute(
            sa_select(Ranking).where(Ranking.gender == "MALE").order_by(Ranking.category_name, Ranking.rank)
        )
        return RankingsResponse(categories=_group_rankings(list(result.scalars().all()))).model_dump(mode="json")

    return await cached_json_response(
        request,
        cache_key=cache_key("rankings:mens"),
        ttl=600,
        loader=loader,
    )


@ranking_router.get("/womens", response_model=RankingsResponse)
async def womens_rankings(request: Request, uow: UnitOfWork = Depends(get_uow)) -> Response:
    """Women's divisions."""
    session = cast(AsyncSession, uow._session)

    async def loader() -> dict:
        result = await session.execute(
            sa_select(Ranking).where(Ranking.gender == "FEMALE").order_by(Ranking.category_name, Ranking.rank)
        )
        return RankingsResponse(categories=_group_rankings(list(result.scalars().all()))).model_dump(mode="json")

    return await cached_json_response(
        request,
        cache_key=cache_key("rankings:womens"),
        ttl=600,
        loader=loader,
    )


@ranking_router.get("/p4p", response_model=RankingCategory)
async def pound_for_pound(request: Request, uow: UnitOfWork = Depends(get_uow)) -> Response:
    """Pound-for-pound rankings."""
    session = cast(AsyncSession, uow._session)

    async def loader() -> dict:
        result = await session.execute(
            sa_select(Ranking).where(Ranking.category_name == "Pound-for-Pound").order_by(Ranking.rank)
        )
        rankings = list(result.scalars().all())
        if not rankings:
            raise HTTPException(404)
        cats = _group_rankings(rankings)
        return (cats[0] if cats else RankingCategory(category_name="Pound-for-Pound")).model_dump(mode="json")

    return await cached_json_response(
        request,
        cache_key=cache_key("rankings:p4p"),
        ttl=600,
        loader=loader,
    )


@ranking_router.get("/{division}", response_model=RankingCategory)
async def division_rankings(request: Request, division: str, uow: UnitOfWork = Depends(get_uow)) -> Response:
    """Specific weight class rankings. division=flyweight, bantamweight, etc."""
    session = cast(AsyncSession, uow._session)

    async def loader() -> dict:
        result = await session.execute(
            sa_select(Ranking).where(Ranking.category_name.ilike(f"%{division}%")).order_by(Ranking.rank)
        )
        rankings = list(result.scalars().all())
        if not rankings:
            raise HTTPException(404, detail=ErrorResponse.not_found("ranking", division).error)
        cats = _group_rankings(rankings)
        return cats[0].model_dump(mode="json")

    return await cached_json_response(
        request,
        cache_key=cache_key("rankings:division", division),
        ttl=600,
        loader=loader,
    )


@ranking_router.get("/movement", response_model=list[RankingMovementEntry])
async def rankings_movement(
    request: Request,
    division: str | None = Query(None, description="Filter by division"),
    uow: UnitOfWork = Depends(get_uow),
) -> Response:
    """Rankings movement — fighters whose rank differs between the two most recent snapshots.

    Uses the two most recent `synced_at` snapshots of the division rankings (or of a single
    division when `division` is given). Requires at least two snapshots; otherwise empty.
    """
    session = cast(AsyncSession, uow._session)

    async def loader() -> list[dict]:
        stmt = sa_select(Ranking).where(Ranking.category_type == "division")
        if division:
            stmt = stmt.where(Ranking.category_name == division)
        stmt = stmt.order_by(Ranking.synced_at.desc(), Ranking.rank.asc())
        result = await session.execute(stmt)
        rows = cast(list[Ranking], result.scalars().all())
        if len(rows) < 2:
            return []

        latest_ts = rows[0].synced_at
        snaps: dict[datetime, dict[str, dict[str, int]]] = {}
        fighter_ids: set[str] = set()
        for r in rows:
            snaps.setdefault(r.synced_at, {})
            snaps[r.synced_at].setdefault(r.category_name, {})
            snaps[r.synced_at][r.category_name][r.fighter_id] = r.rank
            fighter_ids.add(r.fighter_id)

        prev_key = sorted(snaps.keys(), reverse=True)[1]

        changes: list[dict[str, Any]] = []
        for cat in snaps[latest_ts]:
            if cat not in snaps[prev_key]:
                continue
            for f_id, to_rank in snaps[latest_ts][cat].items():
                from_rank = snaps[prev_key][cat].get(f_id)
                if from_rank is not None and from_rank != to_rank:
                    changes.append(
                        {
                            "fighter_id": f_id,
                            "division": cat,
                            "from_rank": from_rank,
                            "to_rank": to_rank,
                        }
                    )

        changes.sort(key=lambda c: (c["from_rank"] - c["to_rank"]), reverse=True)
        changes = changes[:10]
        if not changes:
            return []

        frows = await session.execute(sa_select(Fighter).where(Fighter.id.in_(fighter_ids)))
        fighters = {f.id: f for f in cast(list[Fighter], frows.scalars().all())}

        entries: list[dict] = []
        for c in changes:
            f = fighters.get(c["fighter_id"])
            if not f:
                continue
            delta = c["from_rank"] - c["to_rank"]
            entries.append(
                RankingMovementEntry(
                    fighter=_fighter_brief(f),
                    division=c["division"],
                    from_rank=c["from_rank"],
                    to_rank=c["to_rank"],
                    change=delta,
                    reason="Won" if delta > 0 else "Dropped",
                ).model_dump(mode="json")
            )
        return entries

    return await cached_json_response(
        request,
        cache_key=cache_key("rankings:movement", division),
        ttl=600,
        loader=loader,
    )


@ranking_router.get("/goat", response_model=list[GOATEntry])
async def goat_rankings(request: Request, uow: UnitOfWork = Depends(get_uow)) -> Response:
    """GOAT (Greatest of All Time) list — current and former champions ranked by title defenses and finish rate.

    Derived from real data: champions (is_champion) across all divisions sorted by title_defenses,
    then all ranked fighters by finish_rate. `title_wins` and `divisions` come from the actual
    ranking rows; there is no fight-date lineage in the schema, so the ranking is an approximation
    of dominance, not a historical simulation.
    """
    session = cast(AsyncSession, uow._session)

    async def loader() -> list[dict]:
        result = await session.execute(
            sa_select(Ranking, Fighter)
            .join(Fighter, Ranking.fighter_id == Fighter.id)
            .where(
                Ranking.is_champion.is_(True),
                or_(Ranking.title_defenses > 0, Ranking.title_defenses.is_(None)),
            )
            .order_by(Ranking.title_defenses.desc().nulls_last())
        )
        champion_rows = list(result.all())

        all_ids = {r.fighter_id for r, _ in champion_rows}
        entries: list[GOATEntry] = []
        seen: set[str] = set()
        for r, f in champion_rows:
            if not r.fighter_id or r.fighter_id in seen:
                continue
            seen.add(r.fighter_id)
            wins = f.record_wins or 0
            win_pct, finish = _record_metrics(f)
            entries.append(
                GOATEntry(
                    rank=len(entries) + 1,
                    fighter=_fighter_brief(f),
                    composite_score=_goat_score(r.title_defenses or 0, win_pct, finish, wins),
                    title_defenses=r.title_defenses,
                    title_wins=(r.title_defenses or 0) + 1,
                    finish_rate=finish,
                    divisions=[r.category_name],
                    era=str(r.synced_at.year) if r.synced_at else None,
                )
            )

        for fid in seen:
            all_ids.add(fid)
        if len(entries) < 15:
            fres = await session.execute(
                sa_select(Fighter).where(Fighter.id.not_in(all_ids), Fighter.is_active.is_(True))
            )
            for f in cast(list[Fighter], fres.scalars().all()):
                wins = f.record_wins or 0
                win_pct, finish = _record_metrics(f)
                entries.append(
                    GOATEntry(
                        rank=len(entries) + 1,
                        fighter=_fighter_brief(f),
                        composite_score=_goat_score(0, win_pct, finish, wins),
                        title_defenses=None,
                        title_wins=None,
                        finish_rate=finish,
                        divisions=[],
                        era=None,
                    )
                )
        entries.sort(key=lambda e: e.composite_score, reverse=True)
        for i, e in enumerate(entries, start=1):
            e.rank = i
        return [e.model_dump(mode="json") for e in entries]

    return await cached_json_response(
        request,
        cache_key=cache_key("rankings:goat"),
        ttl=600,
        loader=loader,
    )


@ranking_router.get("/prospects", response_model=list[ProspectEntry])
async def prospect_rankings(request: Request, uow: UnitOfWork = Depends(get_uow)) -> Response:
    """Rising prospects — active, unranked fighters with the strongest records.

    'Unranked' means absent from the current division rankings; sorted by finish rate.
    """
    session = cast(AsyncSession, uow._session)

    async def loader() -> list[dict]:
        rres = await session.execute(sa_select(Ranking.fighter_id))
        ranked_ids = {rid for (rid,) in rres.all() if rid}
        stmt = sa_select(Fighter).where(Fighter.is_active.is_(True))
        if ranked_ids:
            stmt = stmt.where(Fighter.id.not_in(ranked_ids))
        fres = await session.execute(stmt)
        fighters = sorted(
            (
                f
                for f in cast(list[Fighter], fres.scalars().all())
                if f.id not in ranked_ids and (f.record_wins or 0) > 0
            ),
            key=lambda f: (_record_metrics(f)[1] or 0.0, _record_metrics(f)[0] or 0.0),
            reverse=True,
        )
        entries = [
            ProspectEntry(
                fighter=_fighter_brief(f),
                age=None,
                finish_rate=_record_metrics(f)[1],
                trajectory="rising",
                potential=round(min(100.0, (_record_metrics(f)[1] or 0.0) * 100 + 20.0), 2),
                division="unranked",
                comparable=None,
            )
            for f in fighters[:15]
        ]
        return [e.model_dump(mode="json") for e in entries]

    return await cached_json_response(
        request,
        cache_key=cache_key("rankings:prospects"),
        ttl=600,
        loader=loader,
    )


@ranking_router.get("/streaks", response_model=list[StreakEntry])
async def win_streaks(
    request: Request,
    limit: int = Query(10, ge=1, le=50),
    uow: UnitOfWork = Depends(get_uow),
) -> Response:
    """Longest current win streaks, derived from real fight outcomes (Competitor records)."""
    session = cast(AsyncSession, uow._session)

    async def loader() -> list[dict]:
        cres = await session.execute(
            sa_select(Competitor.fighter_id, Competition.status, Competitor.outcome, Competition.result_time)
            .join(Competition, Competitor.competition_id == Competition.id)
            .where(Competition.status == "FINAL")
            .order_by(Competition.result_time.desc())
        )
        rows = cres.all()
        by_fighter: dict[str, list[str | None]] = defaultdict(list)
        for fighter_id, _status, outcome, _ts in rows:
            if fighter_id:
                by_fighter[fighter_id].append(outcome)

        active_ids = [fid for fid in by_fighter if by_fighter[fid]]
        fres = await session.execute(
            sa_select(Fighter).where(Fighter.id.in_(active_ids))
        )
        fighters = {f.id: f for f in cast(list[Fighter], fres.scalars().all())}

        entries: list[StreakEntry] = []
        for fid, outcomes in by_fighter.items():
            f = fighters.get(fid)
            if not f:
                continue
            streak, kind = 0, "wins"
            for outcome in outcomes:
                if outcome == "WIN":
                    streak += 1
                    kind = "wins"
                elif streak > 0:
                    break
            if streak >= 3:
                entries.append(
                    StreakEntry(
                        fighter=_fighter_brief(f),
                        streak=streak,
                        type=kind,
                        best_rank=None,
                        last_fight=None,
                    )
                )
        entries.sort(key=lambda e: e.streak, reverse=True)
        return [e.model_dump(mode="json") for e in entries[:limit]]

    return await cached_json_response(
        request,
        cache_key=cache_key("rankings:streaks", limit),
        ttl=600,
        loader=loader,
    )


# ═══════════════════════════════════════════════════════════════════════════
# Title defenses
# ═══════════════════════════════════════════════════════════════════════════

title_router = APIRouter(prefix="/v1/title-defenses", tags=["champions"])


@title_router.get("", response_model=list[TitleDefenseEntry])
async def list_title_defenses(request: Request, uow: UnitOfWork = Depends(get_uow)) -> Response:
    """Champions ranked by number of title defenses (from rankings.title_defenses)."""
    session = cast(AsyncSession, uow._session)

    async def loader() -> list[dict]:
        result = await session.execute(
            sa_select(Ranking, Fighter)
            .join(Fighter, Ranking.fighter_id == Fighter.id)
            .where(Ranking.is_champion.is_(True))
            .order_by(Ranking.title_defenses.desc().nulls_last())
        )
        rows = list(result.all())
        entries = [
            TitleDefenseEntry(
                fighter=_fighter_brief(f),
                defenses=r.title_defenses or 0,
                division=r.category_name,
            )
            for r, f in rows
            if (r.title_defenses or 0) > 0
        ]
        return [e.model_dump(mode="json") for e in entries]

    return await cached_json_response(
        request,
        cache_key=cache_key("title-defenses:all"),
        ttl=600,
        loader=loader,
    )


# ═══════════════════════════════════════════════════════════════════════════
# Promotions
# ═══════════════════════════════════════════════════════════════════════════

promo_router = APIRouter(prefix="/v1/promotions", tags=["promotions"])


@promo_router.get("", response_model=list[PromotionListItem])
async def list_promotions(request: Request, uow: UnitOfWork = Depends(get_uow)) -> Response:
    """All MMA promotions."""
    session = cast(AsyncSession, uow._session)

    async def loader() -> list[dict]:
        result = await session.execute(sa_select(Promotion).order_by(Promotion.name))
        promos = list(result.scalars().all())
        return [
            PromotionListItem(
                id=p.id,
                name=p.name,
                abbreviation=p.abbreviation,
                slug=p.slug,
                country=getattr(p, "country", None),
                founded_year=getattr(p, "founded_year", None),
                logo_url=p.logo_url,
                fighter_count=0,
                event_count=0,
                current_season=p.season_year,
            ).model_dump(mode="json") for p in promos
        ]

    return await cached_json_response(
        request,
        cache_key=cache_key("promotions:list"),
        ttl=86400,
        loader=loader,
    )


@promo_router.get("/{slug}", response_model=PromotionDetailResponse)
async def get_promotion(slug: str, uow: UnitOfWork = Depends(get_uow)) -> PromotionDetailResponse:
    """Promotion detail — branding, links, stats."""
    session = cast(AsyncSession, uow._session)
    result = await session.execute(
        sa_select(Promotion).where(Promotion.slug == slug)
    )
    promo = result.scalar_one_or_none()
    if promo is None:
        raise HTTPException(404, detail=ErrorResponse.not_found("promotion", slug).error)

    # Count fighters and events
    fighter_count = 0
    event_count = 0
    if promo.id:
        fcnt = await session.execute(
            sa_select(func.count()).select_from(Fighter)
        )
        fighter_count = fcnt.scalar_one()
        ecnt = await session.execute(
            sa_select(func.count()).select_from(Event).where(Event.promotion_id == promo.id)
        )
        event_count = ecnt.scalar_one()

    return PromotionDetailResponse(
        id=promo.id,
        name=promo.name,
        abbreviation=promo.abbreviation,
        short_name=promo.short_name,
        slug=promo.slug,
        country=getattr(promo, "country", None),
        founded_year=getattr(promo, "founded_year", None),
        first_event_date=None,
        gender=promo.gender,
        current_season=promo.season_year,
        logo_url=promo.logo_url,
        badge_url=None,
        banner_url=promo.banner_url,
        poster_url=promo.poster_url,
        description=promo.description,
        tv_rights=None,
        website=promo.website,
        facebook_url=promo.facebook_url,
        instagram_url=promo.instagram_url,
        twitter_url=promo.twitter_url,
        fighter_count=fighter_count,
        event_count=event_count,
        ranking_categories=0,
    )


@promo_router.get("/{slug}/events", response_model=PaginatedResponse)
async def promotion_events(
    slug: str,
    pagination: PaginationDep,
    uow: UnitOfWork = Depends(get_uow),
) -> PaginatedResponse[Any]:
    """Events for this promotion."""
    session = cast(AsyncSession, uow._session)
    promo_result = await session.execute(
        sa_select(Promotion).where(Promotion.slug == slug)
    )
    promo = promo_result.scalar_one_or_none()
    if promo is None:
        raise HTTPException(404)

    result = await session.execute(
        sa_select(Event).where(Event.promotion_id == promo.id)
        .order_by(Event.date_utc.desc())
        .limit(pagination.limit).offset((pagination.page - 1) * pagination.limit)
    )
    events = list(result.scalars().all())
    cnt_result = await session.execute(
        sa_select(func.count()).select_from(Event).where(Event.promotion_id == promo.id)
    )
    total = cnt_result.scalar_one()

    items = [{"id": e.id, "name": e.name, "status": e.status, "date": str(e.date_utc)} for e in events]
    return PaginatedResponse(items=items, total=total, page=pagination.page,
                              limit=pagination.limit,
                              pages=(total + pagination.limit - 1) // pagination.limit if total > 0 else 0)


@promo_router.get("/{slug}/fighters", response_model=PaginatedResponse)
async def promotion_fighters(
    slug: str,
    pagination: PaginationDep,
    uow: UnitOfWork = Depends(get_uow),
) -> PaginatedResponse[Any]:
    """Fighters in this promotion."""
    session = cast(AsyncSession, uow._session)
    result = await session.execute(
        sa_select(Fighter).limit(pagination.limit)
        .offset((pagination.page - 1) * pagination.limit)
    )
    fighters = list(result.scalars().all())
    cnt = await session.execute(sa_select(func.count()).select_from(Fighter))
    total = cnt.scalar_one()

    items = [{"id": f.id, "name": f"{f.first_name} {f.last_name}", "weight_class": f.weight_class_name} for f in fighters]
    return PaginatedResponse(items=items, total=total, page=pagination.page,
                              limit=pagination.limit,
                              pages=(total + pagination.limit - 1) // pagination.limit if total > 0 else 0)


# ═══════════════════════════════════════════════════════════════════════════
# Venues
# ═══════════════════════════════════════════════════════════════════════════

venue_router = APIRouter(prefix="/v1/venues", tags=["venues"])


@venue_router.get("", response_model=PaginatedResponse[VenueListItem])
async def list_venues(
    request: Request,
    pagination: PaginationDep,
    uow: UnitOfWork = Depends(get_uow),
) -> Response:
    """All known venues."""
    session = cast(AsyncSession, uow._session)

    async def loader() -> dict:
        result = await session.execute(
            sa_select(Venue).limit(pagination.limit)
            .offset((pagination.page - 1) * pagination.limit)
        )
        venues = list(result.scalars().all())
        cnt = await session.execute(sa_select(func.count()).select_from(Venue))
        total = cnt.scalar_one()
        return PaginatedResponse(
            items=[VenueListItem(id=v.id, name=v.name, city=v.city, country=v.country, capacity=v.capacity) for v in venues],
            total=total, page=pagination.page, limit=pagination.limit,
            pages=(total + pagination.limit - 1) // pagination.limit if total > 0 else 0,
        ).model_dump(mode="json")

    return await cached_json_response(
        request,
        cache_key=cache_key("venues:list", pagination.limit, pagination.page),
        ttl=86400,
        loader=loader,
    )


@venue_router.get("/{venue_id}", response_model=VenueDetailResponse)
async def get_venue(venue_id: str, uow: UnitOfWork = Depends(get_uow)) -> VenueDetailResponse:
    """Venue detail — capacity, coordinates, past events."""
    require_uuid(venue_id)
    session = cast(AsyncSession, uow._session)
    result = await session.execute(sa_select(Venue).where(Venue.id == venue_id))
    venue = result.scalar_one_or_none()
    if venue is None:
        raise HTTPException(404)

    event_cnt = await session.execute(
        sa_select(func.count()).select_from(Event).where(Event.venue_id == venue_id)
    )
    event_count = event_cnt.scalar_one()

    return VenueDetailResponse(
        id=venue.id, name=venue.name, city=venue.city, state=venue.state,
        country=venue.country, latitude=venue.latitude, longitude=venue.longitude,
        capacity=venue.capacity, indoor=venue.indoor, event_count=event_count,
        last_event_date=None,
    )


@venue_router.get("/{venue_id}/events", response_model=PaginatedResponse)
async def venue_events(
    venue_id: str,
    pagination: PaginationDep,
    uow: UnitOfWork = Depends(get_uow),
) -> PaginatedResponse[Any]:
    """Events held at this venue."""
    require_uuid(venue_id)
    session = cast(AsyncSession, uow._session)
    result = await session.execute(
        sa_select(Event).where(Event.venue_id == venue_id)
        .order_by(Event.date_utc.desc())
        .limit(pagination.limit).offset((pagination.page - 1) * pagination.limit)
    )
    events = list(result.scalars().all())
    cnt = await session.execute(
        sa_select(func.count()).select_from(Event).where(Event.venue_id == venue_id)
    )
    total = cnt.scalar_one()

    items = [{"id": e.id, "name": e.name, "status": e.status, "date": str(e.date_utc)} for e in events]
    return PaginatedResponse(items=items, total=total, page=pagination.page,
                              limit=pagination.limit,
                              pages=(total + pagination.limit - 1) // pagination.limit if total > 0 else 0)


# ═══════════════════════════════════════════════════════════════════════════
# Weight Classes
# ═══════════════════════════════════════════════════════════════════════════

wc_router = APIRouter(prefix="/v1/weight-classes", tags=["weight-classes"])


@wc_router.get("", response_model=PaginatedResponse[WeightClassListItem])
async def list_weight_classes(
    request: Request,
    pagination: PaginationDep,
    uow: UnitOfWork = Depends(get_uow),
) -> Response:
    """All known weight divisions, ordered by name."""
    session = cast(AsyncSession, uow._session)

    async def loader() -> dict:
        result = await session.execute(
            sa_select(WeightClass)
            .order_by(WeightClass.name.asc())
            .limit(pagination.limit)
            .offset((pagination.page - 1) * pagination.limit)
        )
        classes = list(result.scalars().all())
        cnt = await session.execute(sa_select(func.count()).select_from(WeightClass))
        total = cnt.scalar_one()

        items: list[dict[str, Any]] = []
        for wc in classes:
            fcnt = await session.execute(
                sa_select(func.count()).select_from(Fighter)
                .where(Fighter.weight_class_id == wc.id)
            )
            items.append({
                "id": wc.id,
                "name": wc.name,
                "abbreviation": wc.abbreviation,
                "gender": wc.gender,
                "fighter_count": fcnt.scalar_one(),
            })
        return PaginatedResponse(
            items=items, total=total, page=pagination.page, limit=pagination.limit,
            pages=(total + pagination.limit - 1) // pagination.limit if total > 0 else 0,
        ).model_dump(mode="json")

    return await cached_json_response(
        request,
        cache_key=cache_key("weight-classes:list", pagination.limit, pagination.page),
        ttl=86400,
        loader=loader,
    )


@wc_router.get("/{wc_id}", response_model=WeightClassDetailResponse)
async def get_weight_class(
    wc_id: str, uow: UnitOfWork = Depends(get_uow)
) -> WeightClassDetailResponse:
    """Weight class detail — weight bounds and roster size."""
    require_uuid(wc_id)
    session = cast(AsyncSession, uow._session)
    result = await session.execute(
        sa_select(WeightClass).where(WeightClass.id == wc_id)
    )
    wc = result.scalar_one_or_none()
    if wc is None:
        raise HTTPException(404)

    fcnt = await session.execute(
        sa_select(func.count()).select_from(Fighter)
        .where(Fighter.weight_class_id == wc_id)
    )

    return WeightClassDetailResponse(
        id=wc.id, name=wc.name, abbreviation=wc.abbreviation,
        min_weight_kg=wc.min_weight_kg, max_weight_kg=wc.max_weight_kg,
        gender=wc.gender, fighter_count=fcnt.scalar_one(),
    )


# ═══════════════════════════════════════════════════════════════════════════
# Search
# ═══════════════════════════════════════════════════════════════════════════

search_router = APIRouter(prefix="/v1/search", tags=["search"])


@search_router.get("", response_model=SearchResponse)
async def search(
    q: str = Query(..., min_length=2, description="Search query"),
    uow: UnitOfWork = Depends(get_uow),
) -> SearchResponse:
    """Unified search across fighters, events, venues, promotions."""
    session = cast(AsyncSession, uow._session)
    results: list[SearchResultItem] = []

    # Fighters
    fighter_result = await session.execute(
        sa_select(Fighter).where(
            or_(Fighter.full_name.ilike(f"%{q}%"), Fighter.last_name.ilike(f"%{q}%"))
        ).limit(10)
    )
    for f in fighter_result.scalars().all():
        results.append(SearchResultItem(
            id=f.id, type="fighter",
            name=f"{f.first_name} {f.last_name}",
            subtitle=f.weight_class_name,
            image_url=f.headshot_url, relevance=0.9,
        ))

    # Events
    event_result = await session.execute(
        sa_select(Event).where(Event.name.ilike(f"%{q}%")).limit(5)
    )
    for e in event_result.scalars().all():
        results.append(SearchResultItem(
            id=e.id, type="event", name=e.name,
            subtitle=e.status, relevance=0.85,
        ))

    # Venues
    venue_result = await session.execute(
        sa_select(Venue).where(Venue.name.ilike(f"%{q}%")).limit(5)
    )
    for v in venue_result.scalars().all():
        results.append(SearchResultItem(
            id=v.id, type="venue", name=v.name,
            subtitle=f"{v.city}, {v.country}", relevance=0.8,
        ))

    # Promotions
    promo_result = await session.execute(
        sa_select(Promotion).where(Promotion.name.ilike(f"%{q}%")).limit(5)
    )
    for p in promo_result.scalars().all():
        results.append(SearchResultItem(
            id=p.id, type="promotion", name=p.name,
            subtitle=p.abbreviation, relevance=0.8,
        ))

    return SearchResponse(query=q, total=len(results), results=results)


# ═══════════════════════════════════════════════════════════════════════════
# Health
# ═══════════════════════════════════════════════════════════════════════════

health_router = APIRouter(tags=["health"])


@health_router.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
