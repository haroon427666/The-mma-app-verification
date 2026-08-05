"""Fights API — v1. Real implementation connected to CompetitionRepository → PostgreSQL."""

from typing import cast

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from sqlalchemy import func
from sqlalchemy import select as sa_select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.cache import cache_key, cached_json_response
from src.db.models.event import Competition, Competitor
from src.db.models.fighter import Fighter
from src.db.unit_of_work import UnitOfWork
from src.dependencies import Pagination as PaginationDep
from src.dependencies import get_uow
from src.schemas.common import ErrorResponse, PaginatedResponse
from src.schemas.event import (
    FightDetailResponse,
    FighterCornerResponse,
    FightListItem,
)

router = APIRouter(prefix="/v1/fights", tags=["fights"])


def _comp_to_list_item(comp: Competition) -> FightListItem:
    return FightListItem(
        id=comp.id,
        order=comp.order_num or 0,
        card_segment=comp.card_segment,
        status=comp.status or "SCHEDULED",
        is_main_event=comp.is_main_event or False,
        is_title_fight=comp.is_title_fight or False,
        weight_class=comp.weight_class_name,
        fighter_a_name=None,
        fighter_a_id=None,
        fighter_a_record=None,
        fighter_b_name=None,
        fighter_b_id=None,
        fighter_b_record=None,
        winner=None,
        method=comp.result_method,
        round=comp.result_round,
        time=comp.result_time,
    )


@router.get("", response_model=PaginatedResponse[FightListItem])
async def list_fights(
    pagination: PaginationDep,
    status: str | None = Query(None, description="SCHEDULED, IN_PROGRESS, FINAL"),
    weight_class: str | None = Query(None),
    event_id: str | None = Query(None),
    fighter_id: str | None = Query(None),
    outcome: str | None = Query(None),
    method: str | None = Query(None),
    is_title: bool | None = Query(None, description="Filter to title fights only"),
    uow: UnitOfWork = Depends(get_uow),
) -> PaginatedResponse[FightListItem]:
    """List fights with filters."""
    session = cast(AsyncSession, uow._session)
    stmt = sa_select(Competition)
    if status:
        stmt = stmt.where(Competition.status == status)
    if weight_class:
        stmt = stmt.where(Competition.weight_class_name == weight_class)
    if event_id:
        stmt = stmt.where(Competition.event_id == event_id)
    if method:
        stmt = stmt.where(Competition.result_method == method)
    if is_title is not None:
        stmt = stmt.where(Competition.is_title_fight.is_(is_title))

    # Fighter filter via subquery
    if fighter_id:
        sub = sa_select(Competitor.competition_id).where(Competitor.fighter_id == fighter_id)
        stmt = stmt.where(Competition.id.in_(sub))

    count_stmt = sa_select(func.count()).select_from(Competition)
    # Apply same filters to count
    if status:
        count_stmt = count_stmt.where(Competition.status == status)
    if weight_class:
        count_stmt = count_stmt.where(Competition.weight_class_name == weight_class)
    if event_id:
        count_stmt = count_stmt.where(Competition.event_id == event_id)
    if is_title is not None:
        count_stmt = count_stmt.where(Competition.is_title_fight.is_(is_title))
    if fighter_id:
        sub = sa_select(Competitor.competition_id).where(Competitor.fighter_id == fighter_id)
        count_stmt = count_stmt.where(Competition.id.in_(sub))

    total_result = await session.execute(count_stmt)
    total = total_result.scalar_one()

    offset = (pagination.page - 1) * pagination.limit
    stmt = stmt.order_by(Competition.order_num.desc()).limit(pagination.limit).offset(offset)
    result = await session.execute(stmt)
    comps = list(result.scalars().all())

    return PaginatedResponse(
        items=[_comp_to_list_item(c) for c in comps],
        total=total,
        page=pagination.page,
        limit=pagination.limit,
        pages=(total + pagination.limit - 1) // pagination.limit if total > 0 else 0,
    )


@router.get("/upcoming", response_model=list[FightListItem])
async def upcoming_fights(
    limit: int = Query(50, le=100),
    weight_class: str | None = Query(None),
    uow: UnitOfWork = Depends(get_uow),
) -> list[FightListItem]:
    """Upcoming scheduled fights."""
    session = cast(AsyncSession, uow._session)
    stmt = sa_select(Competition).where(Competition.status == "SCHEDULED")
    if weight_class:
        stmt = stmt.where(Competition.weight_class_name == weight_class)
    stmt = stmt.order_by(Competition.order_num).limit(limit)
    result = await session.execute(stmt)
    return [_comp_to_list_item(c) for c in result.scalars().all()]


@router.get("/live", response_model=list[FightListItem])
async def live_fights(uow: UnitOfWork = Depends(get_uow)) -> list[FightListItem]:
    """Currently in-progress fights."""
    session = cast(AsyncSession, uow._session)
    result = await session.execute(
        sa_select(Competition).where(Competition.status == "IN_PROGRESS").limit(20)
    )
    return [_comp_to_list_item(c) for c in result.scalars().all()]


@router.get("/recent", response_model=list[FightListItem])
async def recent_fights(limit: int = Query(50, le=100), uow: UnitOfWork = Depends(get_uow)) -> list[FightListItem]:
    """Recently completed fights."""
    session = cast(AsyncSession, uow._session)
    result = await session.execute(
        sa_select(Competition).where(Competition.status == "FINAL")
        .order_by(Competition.order_num.desc()).limit(limit)
    )
    return [_comp_to_list_item(c) for c in result.scalars().all()]


@router.get("/{fight_id}", response_model=FightDetailResponse,
            responses={404: {"model": ErrorResponse}})
async def get_fight(request: Request, fight_id: str, uow: UnitOfWork = Depends(get_uow)) -> Response:
    """Fight detail — both competitors, result, round-by-round stats."""
    session = cast(AsyncSession, uow._session)

    async def loader() -> dict:
        # Fetch competition
        comp_result = await session.execute(
            sa_select(Competition).where(Competition.id == fight_id)
        )
        comp = comp_result.scalar_one_or_none()
        if comp is None:
            raise HTTPException(404, detail=ErrorResponse.not_found("fight", fight_id).error)

        # Fetch competitors
        comps_result = await session.execute(
            sa_select(Competitor).where(Competitor.competition_id == fight_id)
        )
        competitors = list(comps_result.scalars().all())

        # Resolve fighter names
        fighter_items = []
        for c in competitors:
            f_result = await session.execute(
                sa_select(Fighter).where(Fighter.id == c.fighter_id)
            )
            ftr = f_result.scalar_one_or_none()
            record = f"{ftr.record_wins}-{ftr.record_losses}-{ftr.record_draws}" if ftr else None
            fighter_items.append(FighterCornerResponse(
                fighter_id=c.fighter_id,
                name=f"{ftr.first_name} {ftr.last_name}" if ftr else "Unknown",
                corner=c.corner or "",
                outcome=c.outcome,
                record=record,
            ))

        # Event name
        event_name = None
        event_date = None
        if comp.event_id:
            from src.db.models.event import Event
            evt_result = await session.execute(
                sa_select(Event).where(Event.id == comp.event_id)
            )
            evt = evt_result.scalar_one_or_none()
            if evt:
                event_name = evt.name
                event_date = evt.date_utc

        return FightDetailResponse(
            id=comp.id,
            event_id=comp.event_id or "",
            event_name=event_name,
            event_date=event_date,
            order=comp.order_num or 0,
            card_segment=comp.card_segment,
            status=comp.status or "SCHEDULED",
            is_main_event=comp.is_main_event or False,
            is_title_fight=comp.is_title_fight or False,
            weight_class=comp.weight_class_name,
            description=None,
            fighters=fighter_items,
            winner=comp.result_method,
            method=comp.result_method,
            method_detail=comp.result_detail,
            round=comp.result_round,
            time=comp.result_time,
            broadcasts=[],
        ).model_dump(mode="json")

    return await cached_json_response(
        request,
        cache_key=cache_key("fights:detail", fight_id),
        ttl=300,
        loader=loader,
    )
