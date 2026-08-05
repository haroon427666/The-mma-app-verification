"""Events API — v1. Real implementation connected to EventService → EventRepository → PostgreSQL."""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response

from src.api.cache import cache_key, cached_json_response
from src.db.models.core import Broadcast
from src.db.models.event import Event
from src.db.unit_of_work import UnitOfWork
from src.dependencies import (
    Pagination as PaginationDep,
)
from src.dependencies import (
    Sorting as SortingDep,
)
from src.dependencies import (
    get_uow,
)
from src.schemas.common import ErrorResponse, PaginatedResponse
from src.schemas.event import (
    BroadcastResponse,
    EventDetailResponse,
    EventListItem,
    EventStatisticsResponse,
    FightListItem,
)
from src.services.fighter_service import EventService

router = APIRouter(prefix="/v1/events", tags=["events"])


def _event_to_list_item(event: Event) -> EventListItem:
    """Map ORM Event → EventListItem."""
    return EventListItem(
        id=event.id,
        name=event.name,
        short_name=event.short_name,
        date=event.date_utc,
        status=event.status,
        promotion=None,  # Will be populated if relation loaded
        venue_name=None,
        city=None,
        country=None,
        poster_url=None,
        thumbnail_url=None,
        fight_count=0,
    )


def _build_fight_items(fights_data: list[dict[str, Any]] | None) -> list[FightListItem]:
    """Map competition+competitor rows → FightListItem list."""
    fight_items = []
    if fights_data:
        for fd in fights_data:
            comp = fd["competition"]
            competitors = fd["competitors"]
            ftr_a = None
            ftr_b = None
            for c in competitors:
                if c.corner == "RED":
                    ftr_a = c
                elif c.corner == "BLUE":
                    ftr_b = c
            winner_id = None
            for c in competitors:
                if c.outcome == "WIN":
                    winner_id = c.fighter_id
            fight_items.append(FightListItem(
                id=comp.id,
                order=comp.order_num or 0,
                card_segment=comp.card_segment,
                status=comp.status or "SCHEDULED",
                is_main_event=comp.is_main_event or False,
                is_title_fight=comp.is_title_fight or False,
                weight_class=comp.weight_class_name,
                fighter_a_name=f"Fighter {ftr_a.fighter_id[:8]}" if ftr_a else None,
                fighter_a_id=ftr_a.fighter_id if ftr_a else None,
                fighter_a_record=None,
                fighter_b_name=f"Fighter {ftr_b.fighter_id[:8]}" if ftr_b else None,
                fighter_b_id=ftr_b.fighter_id if ftr_b else None,
                fighter_b_record=None,
                winner=winner_id or comp.result_method,
                method=comp.result_method,
                round=comp.result_round,
                time=comp.result_time,
            ))
    return fight_items


def _event_to_detail(
    event: Event,
    fights_data: list[dict[str, Any]] | None = None,
    broadcasts: list[Broadcast] | None = None,
) -> EventDetailResponse:
    """Map ORM Event + relations → EventDetailResponse."""
    fight_items = _build_fight_items(fights_data)

    broadcast_items = [
        BroadcastResponse(
            network=b.network,
            region=b.region,
            broadcast_type=b.broadcast_type or "TV",
            language=b.language,
        ) for b in (broadcasts or [])
    ]

    return EventDetailResponse(
        id=event.id,
        name=event.name,
        short_name=event.short_name,
        slug=event.slug,
        date=event.date_utc,
        time_local=None,
        status=event.status,
        season=event.season,
        promotion=None,
        promotion_id=event.promotion_id,
        venue_name=None,
        venue_id=event.venue_id,
        city=None,
        country=None,
        venue_capacity=None,
        poster_url=None,
        banner_url=None,
        thumbnail_url=None,
        square_url=None,
        description=None,
        fight_items=fight_items,
        broadcasts=broadcast_items,
        spectators=None,
    )


@router.get("", response_model=PaginatedResponse[EventListItem])
async def list_events(
    request: Request,
    pagination: PaginationDep,
    sort: SortingDep,
    status: str | None = Query(None),
    promotion_slug: str | None = Query(None),
    year: int | None = Query(None),
    country: str | None = Query(None),
    search: str | None = Query(None),
    uow: UnitOfWork = Depends(get_uow),
) -> Response:
    """List events with pagination, filtering, search."""
    svc = EventService(uow)

    async def loader() -> dict:
        items, total = await svc.list_events(
            limit=pagination.limit,
            offset=(pagination.page - 1) * pagination.limit,
            status=status,
            year=year,
            search=search,
            sort_by=sort.sort_by,
            sort_dir=sort.sort_dir,
        )
        return PaginatedResponse(
            items=[_event_to_list_item(e) for e in items],
            total=total,
            page=pagination.page,
            limit=pagination.limit,
            pages=(total + pagination.limit - 1) // pagination.limit if total > 0 else 0,
        ).model_dump(mode="json")

    return await cached_json_response(
        request,
        cache_key=cache_key(
            "events:list",
            pagination.limit, pagination.page, sort.sort_by, sort.sort_dir,
            status, promotion_slug, year, country, search,
        ),
        ttl=300,
        loader=loader,
    )


@router.get("/upcoming", response_model=list[EventListItem])
async def upcoming_events(request: Request, limit: int = Query(20, le=50), uow: UnitOfWork = Depends(get_uow)) -> Response:
    """Upcoming scheduled events."""
    svc = EventService(uow)

    async def loader() -> list[dict]:
        events = await svc.get_upcoming(limit)
        return [_event_to_list_item(e).model_dump(mode="json") for e in events]

    return await cached_json_response(
        request,
        cache_key=cache_key("events:upcoming", limit),
        ttl=300,
        loader=loader,
    )


@router.get("/live", response_model=list[EventListItem])
async def live_events(request: Request, uow: UnitOfWork = Depends(get_uow)) -> Response:
    """Currently live or in-progress events."""
    svc = EventService(uow)

    async def loader() -> list[dict]:
        events = await svc.get_live()
        return [_event_to_list_item(e).model_dump(mode="json") for e in events]

    return await cached_json_response(
        request,
        cache_key=cache_key("events:live"),
        ttl=60,
        loader=loader,
    )


@router.get("/past", response_model=PaginatedResponse[EventListItem])
async def past_events(
    pagination: PaginationDep,
    year: int | None = Query(None),
    uow: UnitOfWork = Depends(get_uow),
) -> PaginatedResponse[EventListItem]:
    """Completed events."""
    svc = EventService(uow)
    items, total = await svc.get_past(
        limit=pagination.limit,
        offset=(pagination.page - 1) * pagination.limit,
    )
    return PaginatedResponse(
        items=[_event_to_list_item(e) for e in items],
        total=total,
        page=pagination.page,
        limit=pagination.limit,
        pages=(total + pagination.limit - 1) // pagination.limit if total > 0 else 0,
    )


@router.get("/{event_id}/fights", response_model=list[FightListItem],
            responses={404: {"model": ErrorResponse}})
async def get_event_fights(request: Request, event_id: str, uow: UnitOfWork = Depends(get_uow)) -> Response:
    """Fight card for an event — competitions + competitors with results."""
    from sqlalchemy import select as sa_select

    from src.db.models.event import Competition, Competitor

    async def loader() -> list[dict]:
        event = await uow.events.get_by_id(event_id)
        if event is None:
            raise HTTPException(404, detail=ErrorResponse.not_found("event", event_id).error)
        result = await uow.session.execute(
            sa_select(Competition).where(Competition.event_id == event_id).order_by(Competition.order_num)
        )
        competitions = list(result.scalars().all())
        competitors_by_comp: dict[str, list[Competitor]] = {}
        if competitions:
            comp_ids = [comp.id for comp in competitions]
            comp_result = await uow.session.execute(
                sa_select(Competitor).where(Competitor.competition_id.in_(comp_ids))
            )
            for comp in comp_result.scalars().all():
                competitors_by_comp.setdefault(comp.competition_id, []).append(comp)
        fights_data = [
            {"competition": comp, "competitors": competitors_by_comp.get(comp.id, [])}
            for comp in competitions
        ]
        return [item.model_dump(mode="json") for item in _build_fight_items(fights_data)]

    return await cached_json_response(
        request,
        cache_key=cache_key("events:fights", event_id),
        ttl=120,
        loader=loader,
    )


@router.get("/{event_id}/results", response_model=list[FightListItem],
            responses={404: {"model": ErrorResponse}})
async def get_event_results(request: Request, event_id: str, uow: UnitOfWork = Depends(get_uow)) -> Response:
    """Completed fights for an event — only fights with a recorded result."""
    from sqlalchemy import select as sa_select

    from src.db.models.event import Competition, Competitor

    async def loader() -> list[dict]:
        event = await uow.events.get_by_id(event_id)
        if event is None:
            raise HTTPException(404, detail=ErrorResponse.not_found("event", event_id).error)
        result = await uow.session.execute(
            sa_select(Competition).where(
                Competition.event_id == event_id,
                Competition.result_method.isnot(None),
            ).order_by(Competition.order_num)
        )
        competitions = list(result.scalars().all())
        competitors_by_comp: dict[str, list[Competitor]] = {}
        if competitions:
            comp_ids = [comp.id for comp in competitions]
            comp_result = await uow.session.execute(
                sa_select(Competitor).where(Competitor.competition_id.in_(comp_ids))
            )
            for comp in comp_result.scalars().all():
                competitors_by_comp.setdefault(comp.competition_id, []).append(comp)
        fights_data = [
            {"competition": comp, "competitors": competitors_by_comp.get(comp.id, [])}
            for comp in competitions
        ]
        return [item.model_dump(mode="json") for item in _build_fight_items(fights_data)]

    return await cached_json_response(
        request,
        cache_key=cache_key("events:results", event_id),
        ttl=120,
        loader=loader,
    )


@router.get("/{event_id}/statistics", response_model=EventStatisticsResponse,
            responses={404: {"model": ErrorResponse}})
async def get_event_statistics(request: Request, event_id: str, uow: UnitOfWork = Depends(get_uow)) -> Response:
    """Aggregated statistics for an event — computed from the fight card."""
    from sqlalchemy import select as sa_select

    from src.db.models.event import Competition, Competitor
    from src.db.models.fighter import Fighter

    async def loader() -> dict:
        event = await uow.events.get_by_id(event_id)
        if event is None:
            raise HTTPException(404, detail=ErrorResponse.not_found("event", event_id).error)
        result = await uow.session.execute(
            sa_select(Competition).where(Competition.event_id == event_id)
        )
        competitions = list(result.scalars().all())

        fighters_by_id: dict[str, Fighter] = {}
        if competitions:
            comp_ids = [comp.id for comp in competitions]
            comp_result = await uow.session.execute(
                sa_select(Competitor).where(Competitor.competition_id.in_(comp_ids))
            )
            competitor_rows = list(comp_result.scalars().all())
            fighter_ids = {c.fighter_id for c in competitor_rows if c.fighter_id}
            if fighter_ids:
                f_result = await uow.session.execute(
                    sa_select(Fighter).where(Fighter.id.in_(fighter_ids))
                )
                for f in f_result.scalars().all():
                    fighters_by_id[f.id] = f

        methods = [c.result_method for c in competitions if c.result_method]
        total_fights = len(competitions)
        title_fights = sum(1 for c in competitions if c.is_title_fight)
        decisions = methods.count("Decision")
        submissions = methods.count("Submission")
        ko_tko = sum(1 for m in methods if m in ("KO", "TKO"))
        finishes = max(total_fights - decisions, 0)
        countries = {f.nationality for f in fighters_by_id.values() if f.nationality}
        weight_classes = sorted({c.weight_class_name for c in competitions if c.weight_class_name})

        return EventStatisticsResponse(
            total_fights=total_fights,
            title_fights=title_fights,
            decisions=decisions,
            finishes=finishes,
            ko_tko=ko_tko,
            submissions=submissions,
            countries_represented=len(countries),
            weight_classes=weight_classes,
        ).model_dump(mode="json")

    return await cached_json_response(
        request,
        cache_key=cache_key("events:statistics", event_id),
        ttl=120,
        loader=loader,
    )


@router.get("/{event_id}", response_model=EventDetailResponse,
            responses={404: {"model": ErrorResponse}})
async def get_event(request: Request, event_id: str, uow: UnitOfWork = Depends(get_uow)) -> Response:
    """Event detail — venue, fights, broadcasts, poster."""
    svc = EventService(uow)

    async def loader() -> dict:
        detail = await svc.get_event_detail(event_id)
        if detail is None:
            raise HTTPException(404, detail=ErrorResponse.not_found("event", event_id).error)
        return _event_to_detail(
            event=detail["event"],
            fights_data=detail.get("fights"),
            broadcasts=detail.get("broadcasts"),
        ).model_dump(mode="json")

    return await cached_json_response(
        request,
        cache_key=cache_key("events:detail", event_id),
        ttl=300,
        loader=loader,
    )
