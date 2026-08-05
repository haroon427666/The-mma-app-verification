"""Fighters API — v1. Real implementation connected to FighterService → FighterRepository → PostgreSQL."""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response

from src.api.cache import cache_key, cached_json_response
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
from src.schemas.fighter import (
    FighterFightEntry,
    FighterListItem,
    FighterMediaResponse,
    FighterProfileResponse,
    FighterRankingEntry,
    FighterRecordResponse,
    FighterStatsResponse,
    StatValue,
)
from src.services.fighter_service import FighterService

router = APIRouter(prefix="/v1/fighters", tags=["fighters"])


def _fighter_to_list_item(fighter: Any) -> FighterListItem:
    """Map ORM Fighter model → FighterListItem Pydantic schema."""
    record = f"{fighter.record_wins or 0}-{fighter.record_losses or 0}-{fighter.record_draws or 0}"
    return FighterListItem(
        id=fighter.id,
        first_name=fighter.first_name,
        last_name=fighter.last_name,
        full_name=fighter.full_name,
        nickname=fighter.nickname,
        weight_class=fighter.weight_class_name,
        record=record,
        record_wins=fighter.record_wins or 0,
        record_losses=fighter.record_losses or 0,
        record_draws=fighter.record_draws or 0,
        nationality=fighter.nationality,
        headshot_url=fighter.headshot_url,
        is_active=fighter.is_active if fighter.is_active is not None else True,
        stance=fighter.stance,
        fighting_style=fighter.fighting_style,
        latest_rank=None,
        latest_rank_category=None,
    )


def _fighter_to_profile(
    fighter: Any,
    record: Any = None,
    rankings: Any = None,
    recent_fights: Any = None,
) -> FighterProfileResponse:
    """Map ORM Fighter + relations → FighterProfileResponse."""
    from datetime import UTC, datetime
    age = None
    if fighter.birth_date:
        today = datetime.now(UTC).date()
        age = today.year - fighter.birth_date.year - (
            (today.month, today.day) < (fighter.birth_date.month, fighter.birth_date.day)
        )

    return FighterProfileResponse(
        id=fighter.id,
        first_name=fighter.first_name,
        last_name=fighter.last_name,
        full_name=fighter.full_name,
        short_name=fighter.short_name,
        nickname=fighter.nickname,
        slug=fighter.slug,
        weight_kg=fighter.weight_kg,
        height_cm=fighter.height_cm,
        reach_cm=fighter.reach_cm,
        leg_reach_cm=fighter.leg_reach_cm,
        stance=fighter.stance,
        weight_class=fighter.weight_class_name,
        nationality=fighter.nationality,
        birth_date=fighter.birth_date,
        birth_location=fighter.birth_location,
        age=age,
        is_active=fighter.is_active if fighter.is_active is not None else True,
        debut_date=fighter.debut_date,
        record=_record_to_schema(record) if record else None,
        statistics=FighterStatsResponse(),
        rankings=[
            FighterRankingEntry(
                category_name=r.category_name,
                rank=r.rank,
                trend=r.trend,
                is_champion=r.is_champion,
                title_defenses=r.title_defenses,
            ) for r in (rankings or [])
        ],
        recent_fights=[],
        upcoming_fight=None,
        trains_at=fighter.trains_at,
        fighting_style=fighter.fighting_style,
        biography=fighter.biography,
        media=FighterMediaResponse(
            headshot_url=fighter.headshot_url,
            cutout_url=fighter.cutout_url,
            render_url=fighter.render_url,
            cdn_url=fighter.headshot_url,
        ),
        instagram_url=fighter.instagram_url,
        twitter_url=fighter.twitter_url,
        source_provider=fighter.source_provider,
        synced_at=fighter.synced_at,
    )


def _record_to_schema(record: Any) -> FighterRecordResponse | None:
    if record is None:
        return None
    return FighterRecordResponse(
        wins=record.wins,
        losses=record.losses,
        draws=record.draws,
        no_contests=record.no_contests,
        ko_tko_wins=record.ko_tko_wins,
        ko_tko_losses=record.ko_tko_losses,
        submission_wins=record.submission_wins,
        submission_losses=record.submission_losses,
        title_wins=record.title_wins,
        title_losses=record.title_losses,
        title_draws=record.title_draws,
        total_fights=record.total_fights,
        win_percentage=record.win_percentage,
        finish_rate=record.finish_rate,
        record_summary=record.record_summary,
    )


@router.get("", response_model=PaginatedResponse[FighterListItem])
async def list_fighters(
    request: Request,
    pagination: PaginationDep,
    sort: SortingDep,
    weight_class: str | None = Query(None),
    country: str | None = Query(None),
    active: bool | None = Query(None),
    ranked: bool | None = Query(None),
    stance: str | None = Query(None),
    gym: str | None = Query(None),
    style: str | None = Query(None),
    search: str | None = Query(None),
    uow: UnitOfWork = Depends(get_uow),
) -> Response:
    """List fighters with pagination, filtering, search."""
    svc = FighterService(uow)

    async def loader() -> dict:
        items, total = await svc.list_fighters(
            limit=pagination.limit,
            offset=(pagination.page - 1) * pagination.limit,
            weight_class=weight_class,
            country=country,
            active=active,
            stance=stance,
            search=search,
            sort_by=sort.sort_by,
            sort_dir=sort.sort_dir,
        )
        return PaginatedResponse(
            items=[_fighter_to_list_item(f) for f in items],
            total=total,
            page=pagination.page,
            limit=pagination.limit,
            pages=(total + pagination.limit - 1) // pagination.limit if total > 0 else 0,
        ).model_dump(mode="json")

    return await cached_json_response(
        request,
        cache_key=cache_key(
            "fighters:list",
            pagination.limit, pagination.page, sort.sort_by, sort.sort_dir,
            weight_class, country, active, ranked, stance, gym, style, search,
        ),
        ttl=300,
        loader=loader,
    )


@router.get("/{fighter_id}", response_model=FighterProfileResponse,
            responses={404: {"model": ErrorResponse}})
async def get_fighter(request: Request, fighter_id: str, uow: UnitOfWork = Depends(get_uow)) -> Response:
    """Complete fighter profile — bio, record, rankings, stats, media."""
    svc = FighterService(uow)

    async def loader() -> dict:
        detail = await svc.get_fighter_detail(fighter_id)
        if detail is None:
            raise HTTPException(404, detail=ErrorResponse.not_found("fighter", fighter_id).error)
        return _fighter_to_profile(
            fighter=detail["fighter"],
            record=detail.get("record"),
            rankings=detail.get("rankings"),
            recent_fights=detail.get("recent_fights"),
        ).model_dump(mode="json")

    return await cached_json_response(
        request,
        cache_key=cache_key("fighters:detail", fighter_id),
        ttl=3600,
        loader=loader,
    )


@router.get("/{fighter_id}/statistics", response_model=FighterStatsResponse)
async def get_fighter_stats(request: Request, fighter_id: str, uow: UnitOfWork = Depends(get_uow)) -> Response:
    """Fighter's career statistics — striking, grappling, general."""
    svc = FighterService(uow)

    async def loader() -> dict:
        fighter = await svc._uow.fighters.get_by_id(fighter_id)
        if fighter is None:
            raise HTTPException(404)

        stats_rows = await svc.get_fighter_stats(fighter_id)
        stats = FighterStatsResponse(all_stats=[
            StatValue(label=s.label, value=s.value, display_value=s.display_value or str(s.value), category=s.category)
            for s in stats_rows
        ])

        # Populate known stat fields from rows
        for s in stats_rows:
            label_lower = s.label.lower()
            if "sig strikes landed per min" in label_lower:
                stats.sig_strikes_landed_per_min = s.value
            elif "accuracy" in label_lower and "takedown" not in label_lower:
                stats.sig_strikes_accuracy = s.value
            elif "absorbed" in label_lower:
                stats.sig_strikes_absorbed_per_min = s.value
            elif "defense" in label_lower and "takedown" not in label_lower:
                stats.sig_strikes_defense = s.value
            elif "takedown avg" in label_lower:
                stats.takedown_avg_per_15min = s.value
            elif "takedown accuracy" in label_lower:
                stats.takedown_accuracy = s.value
            elif "takedown defense" in label_lower:
                stats.takedown_defense = s.value
            elif "submission avg" in label_lower:
                stats.submission_avg_per_15min = s.value
            elif "knockdown" in label_lower:
                stats.knockdowns = s.value
            elif "avg fight time" in label_lower:
                stats.avg_fight_time_sec = s.value
            elif "control time" in label_lower:
                stats.control_time_sec = s.value
        return stats.model_dump(mode="json")

    return await cached_json_response(
        request,
        cache_key=cache_key("fighters:statistics", fighter_id),
        ttl=3600,
        loader=loader,
    )


@router.get("/{fighter_id}/history", response_model=list[FighterFightEntry])
async def get_fighter_history(request: Request, fighter_id: str, limit: int = Query(20, le=50), uow: UnitOfWork = Depends(get_uow)) -> Response:
    """Recent fight history."""
    svc = FighterService(uow)

    async def loader() -> list[dict]:
        fighter = await svc._uow.fighters.get_by_id(fighter_id)
        if fighter is None:
            raise HTTPException(404)

        fights = await svc.get_fighter_fights(fighter_id, limit)
        entries = []
        for f in fights:
            comp = f["competition"]
            opp = f.get("opponent")
            corner = f.get("corner")
            entries.append(FighterFightEntry(
                event_name=f.get("event_name") or "",
                event_date=f.get("event_date"),
                opponent_name=f"{opp.first_name} {opp.last_name}" if opp else None,
                opponent_id=opp.id if opp else None,
                outcome=corner.outcome if corner else None,
                method=comp.result_method,
                round=comp.result_round,
                time=comp.result_time,
                weight_class=comp.weight_class_name,
                is_title_fight=comp.is_title_fight or False,
            ))
        return [e.model_dump(mode="json") for e in entries]

    return await cached_json_response(
        request,
        cache_key=cache_key("fighters:history", fighter_id, limit),
        ttl=3600,
        loader=loader,
    )


@router.get("/{fighter_id}/media", response_model=FighterMediaResponse)
async def get_fighter_media(fighter_id: str, uow: UnitOfWork = Depends(get_uow)) -> FighterMediaResponse:
    """Fighter images — headshot, cutout, render, CDN fallback."""
    svc = FighterService(uow)
    media = await svc.get_fighter_media(fighter_id)
    if media is None:
        raise HTTPException(404)
    return FighterMediaResponse(**media)
