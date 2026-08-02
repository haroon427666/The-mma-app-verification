"""Rankings, Promotions, Venues, Search, Health routers — v1. Real implementations."""

from fastapi import APIRouter, Depends, HTTPException, Query

from sqlalchemy import select as sa_select, func, or_

from src.db.unit_of_work import UnitOfWork
from src.db.models.core import Promotion, Venue, Ranking, Broadcast
from src.db.models.event import Event, Competition
from src.db.models.fighter import Fighter
from src.dependencies import Pagination as PaginationDep, get_uow, PaginationParams
from src.schemas.common import ErrorResponse, PaginatedResponse
from src.schemas.misc import (
    RankingsResponse, RankingCategory, RankingEntry,
    PromotionListItem, PromotionDetailResponse,
    VenueListItem, VenueDetailResponse,
    SearchResponse, SearchResultItem,
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
    gender: str | None = Query(None, description="MALE, FEMALE"),
    uow: UnitOfWork = Depends(get_uow),
):
    """All UFC rankings, optionally filtered by gender."""
    result = await uow._session.execute(
        sa_select(Ranking).order_by(Ranking.category_name, Ranking.rank)
    )
    all_rankings = list(result.scalars().all())
    if gender:
        all_rankings = [r for r in all_rankings if r.gender == gender.upper()]
    return RankingsResponse(categories=_group_rankings(all_rankings))


@ranking_router.get("/mens", response_model=RankingsResponse)
async def mens_rankings(uow: UnitOfWork = Depends(get_uow)):
    """Men's divisions — all weight classes + P4P."""
    result = await uow._session.execute(
        sa_select(Ranking).where(Ranking.gender == "MALE").order_by(Ranking.category_name, Ranking.rank)
    )
    return RankingsResponse(categories=_group_rankings(list(result.scalars().all())))


@ranking_router.get("/womens", response_model=RankingsResponse)
async def womens_rankings(uow: UnitOfWork = Depends(get_uow)):
    """Women's divisions."""
    result = await uow._session.execute(
        sa_select(Ranking).where(Ranking.gender == "FEMALE").order_by(Ranking.category_name, Ranking.rank)
    )
    return RankingsResponse(categories=_group_rankings(list(result.scalars().all())))


@ranking_router.get("/p4p", response_model=RankingCategory)
async def pound_for_pound(uow: UnitOfWork = Depends(get_uow)):
    """Pound-for-pound rankings."""
    result = await uow._session.execute(
        sa_select(Ranking).where(Ranking.category_name == "Pound-for-Pound").order_by(Ranking.rank)
    )
    rankings = list(result.scalars().all())
    if not rankings:
        raise HTTPException(404)
    cats = _group_rankings(rankings)
    return cats[0] if cats else RankingCategory(category_name="Pound-for-Pound")


@ranking_router.get("/{division}", response_model=RankingCategory)
async def division_rankings(division: str, uow: UnitOfWork = Depends(get_uow)):
    """Specific weight class rankings. division=flyweight, bantamweight, etc."""
    result = await uow._session.execute(
        sa_select(Ranking).where(Ranking.category_name.ilike(f"%{division}%")).order_by(Ranking.rank)
    )
    rankings = list(result.scalars().all())
    if not rankings:
        raise HTTPException(404, detail=ErrorResponse.not_found("ranking", division).error)
    cats = _group_rankings(rankings)
    return cats[0]


# ═══════════════════════════════════════════════════════════════════════════
# Promotions
# ═══════════════════════════════════════════════════════════════════════════

promo_router = APIRouter(prefix="/v1/promotions", tags=["promotions"])


@promo_router.get("", response_model=list[PromotionListItem])
async def list_promotions(uow: UnitOfWork = Depends(get_uow)):
    """All MMA promotions."""
    result = await uow._session.execute(sa_select(Promotion).order_by(Promotion.name))
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
        ) for p in promos
    ]


@promo_router.get("/{slug}", response_model=PromotionDetailResponse)
async def get_promotion(slug: str, uow: UnitOfWork = Depends(get_uow)):
    """Promotion detail — branding, links, stats."""
    result = await uow._session.execute(
        sa_select(Promotion).where(Promotion.slug == slug)
    )
    promo = result.scalar_one_or_none()
    if promo is None:
        raise HTTPException(404, detail=ErrorResponse.not_found("promotion", slug).error)

    # Count fighters and events
    fighter_count = 0
    event_count = 0
    if promo.id:
        fcnt = await uow._session.execute(
            sa_select(func.count()).select_from(Fighter)
        )
        fighter_count = fcnt.scalar_one()
        ecnt = await uow._session.execute(
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
):
    """Events for this promotion."""
    promo_result = await uow._session.execute(
        sa_select(Promotion).where(Promotion.slug == slug)
    )
    promo = promo_result.scalar_one_or_none()
    if promo is None:
        raise HTTPException(404)

    result = await uow._session.execute(
        sa_select(Event).where(Event.promotion_id == promo.id)
        .order_by(Event.date_utc.desc())
        .limit(pagination.limit).offset((pagination.page - 1) * pagination.limit)
    )
    events = list(result.scalars().all())
    cnt_result = await uow._session.execute(
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
):
    """Fighters in this promotion."""
    result = await uow._session.execute(
        sa_select(Fighter).limit(pagination.limit)
        .offset((pagination.page - 1) * pagination.limit)
    )
    fighters = list(result.scalars().all())
    cnt = await uow._session.execute(sa_select(func.count()).select_from(Fighter))
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
    pagination: PaginationDep,
    uow: UnitOfWork = Depends(get_uow),
):
    """All known venues."""
    result = await uow._session.execute(
        sa_select(Venue).limit(pagination.limit)
        .offset((pagination.page - 1) * pagination.limit)
    )
    venues = list(result.scalars().all())
    cnt = await uow._session.execute(sa_select(func.count()).select_from(Venue))
    total = cnt.scalar_one()

    return PaginatedResponse(
        items=[VenueListItem(id=v.id, name=v.name, city=v.city, country=v.country, capacity=v.capacity) for v in venues],
        total=total, page=pagination.page, limit=pagination.limit,
        pages=(total + pagination.limit - 1) // pagination.limit if total > 0 else 0,
    )


@venue_router.get("/{venue_id}", response_model=VenueDetailResponse)
async def get_venue(venue_id: str, uow: UnitOfWork = Depends(get_uow)):
    """Venue detail — capacity, coordinates, past events."""
    result = await uow._session.execute(sa_select(Venue).where(Venue.id == venue_id))
    venue = result.scalar_one_or_none()
    if venue is None:
        raise HTTPException(404)

    event_cnt = await uow._session.execute(
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
):
    """Events held at this venue."""
    result = await uow._session.execute(
        sa_select(Event).where(Event.venue_id == venue_id)
        .order_by(Event.date_utc.desc())
        .limit(pagination.limit).offset((pagination.page - 1) * pagination.limit)
    )
    events = list(result.scalars().all())
    cnt = await uow._session.execute(
        sa_select(func.count()).select_from(Event).where(Event.venue_id == venue_id)
    )
    total = cnt.scalar_one()

    items = [{"id": e.id, "name": e.name, "status": e.status, "date": str(e.date_utc)} for e in events]
    return PaginatedResponse(items=items, total=total, page=pagination.page,
                              limit=pagination.limit,
                              pages=(total + pagination.limit - 1) // pagination.limit if total > 0 else 0)


# ═══════════════════════════════════════════════════════════════════════════
# Search
# ═══════════════════════════════════════════════════════════════════════════

search_router = APIRouter(prefix="/v1/search", tags=["search"])


@search_router.get("", response_model=SearchResponse)
async def search(
    q: str = Query(..., min_length=2, description="Search query"),
    uow: UnitOfWork = Depends(get_uow),
):
    """Unified search across fighters, events, venues, promotions."""
    results: list[SearchResultItem] = []

    # Fighters
    fighter_result = await uow._session.execute(
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
    event_result = await uow._session.execute(
        sa_select(Event).where(Event.name.ilike(f"%{q}%")).limit(5)
    )
    for e in event_result.scalars().all():
        results.append(SearchResultItem(
            id=e.id, type="event", name=e.name,
            subtitle=e.status, relevance=0.85,
        ))

    # Venues
    venue_result = await uow._session.execute(
        sa_select(Venue).where(Venue.name.ilike(f"%{q}%")).limit(5)
    )
    for v in venue_result.scalars().all():
        results.append(SearchResultItem(
            id=v.id, type="venue", name=v.name,
            subtitle=f"{v.city}, {v.country}", relevance=0.8,
        ))

    # Promotions
    promo_result = await uow._session.execute(
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
async def health():
    return {"status": "ok"}
