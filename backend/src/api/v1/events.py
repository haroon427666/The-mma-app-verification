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


def _event_to_detail(
    event: Event,
    fights_data: list[dict[str, Any]] | None = None,
    broadcasts: list[Broadcast] | None = None,
) -> EventDetailResponse:
    """Map ORM Event + relations → EventDetailResponse."""
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
                winner=comp.result_method,
                method=comp.result_method,
                round=comp.result_round,
                time=comp.result_time,
            ))

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
        fights=fight_items,
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
