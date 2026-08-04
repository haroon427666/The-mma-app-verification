"""Recommendations API — personalized feeds. Returns DB data until AI engine integrated."""

from typing import Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.dependencies import get_optional_user
from src.auth.jwt import TokenPayload
from src.db.session import get_session

router = APIRouter(prefix="/v1/recommendations", tags=["recommendations"])


@router.get("")
async def get_recommendations(
    limit: int = Query(20, le=50),
    user: TokenPayload = Depends(get_optional_user),
    session: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    """Personalized recommendation feed — fighters + events."""
    from sqlalchemy import select as sa_select

    from src.db.models.event import Event
    from src.db.models.fighter import Fighter

    # Fighters — active, ranked first
    f_result = await session.execute(
        sa_select(Fighter).where(Fighter.is_active == True).limit(limit)
    )
    fighters = []
    for f in f_result.scalars().all():
        fighters.append({
            "id": f.id, "type": "fighter",
            "title": f"{f.first_name} {f.last_name}",
            "subtitle": f.weight_class_name or "",
            "imageUrl": f.headshot_url, "score": 0.85,
            "reasons": [{"reason": "Active fighter", "weight": 0.5, "category": "trending"}],
        })

    # Events — upcoming
    e_result = await session.execute(
        sa_select(Event).where(Event.status == "SCHEDULED").order_by(Event.date_utc.asc()).limit(5)
    )
    events = []
    for e in e_result.scalars().all():
        events.append({
            "id": e.id, "type": "event",
            "title": e.name, "subtitle": e.status,
            "imageUrl": None, "score": 0.8,
            "reasons": [{"reason": "Upcoming event", "weight": 0.5, "category": "trending"}],
        })

    return {"data": fighters + events}


@router.get("/fighters")
async def recommended_fighters(
    limit: int = Query(10, le=30),
    session: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    """Recommended fighters feed."""
    from sqlalchemy import select as sa_select

    from src.db.models.fighter import Fighter
    result = await session.execute(
        sa_select(Fighter).where(Fighter.is_active == True).limit(limit)
    )
    items = []
    for f in result.scalars().all():
        items.append({
            "id": f.id, "type": "fighter",
            "title": f"{f.first_name} {f.last_name}",
            "subtitle": f.weight_class_name or "", "imageUrl": f.headshot_url, "score": 0.85,
            "reasons": [{"reason": "Active fighter", "weight": 0.5, "category": "trending"}],
        })
    return {"data": items}


@router.get("/events")
async def recommended_events(
    limit: int = Query(10, le=30),
    session: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    """Recommended events feed."""
    from sqlalchemy import select as sa_select

    from src.db.models.event import Event
    result = await session.execute(
        sa_select(Event).where(Event.status == "SCHEDULED")
        .order_by(Event.date_utc.asc()).limit(limit)
    )
    return {"data": [{"id": e.id, "type": "event", "title": e.name, "subtitle": e.status, "imageUrl": None, "score": 0.8, "reasons": [{"reason": "Upcoming", "weight": 0.5, "category": "trending"}]} for e in result.scalars().all()]}


@router.get("/trending")
async def trending(session: AsyncSession = Depends(get_session)) -> dict[str, Any]:
    """Trending fighters and events."""
    return {"data": []}


@router.get("/discover")
async def discover(session: AsyncSession = Depends(get_session)) -> dict[str, Any]:
    """Discovery feed."""
    return {"data": []}


@router.get("/because/watched")
async def because_watched(session: AsyncSession = Depends(get_session)) -> dict[str, Any]:
    """Because you watched..."""
    return {"data": []}


@router.get("/because/follow")
async def because_follow(session: AsyncSession = Depends(get_session)) -> dict[str, Any]:
    """Because you follow..."""
    return {"data": []}


@router.post("/feedback", status_code=201)
async def recs_feedback(body: dict[str, Any]) -> dict[str, Any]:
    """Record recommendation feedback (liked/dismissed/opened)."""
    return {"status": "recorded"}


@router.get("/profile")
async def recs_profile(session: AsyncSession = Depends(get_session)) -> dict[str, Any]:
    """User interest profile."""
    return {"data": {"categories": [], "fighters": [], "styles": []}}


@router.post("/dismiss/{rec_id}", status_code=201)
async def dismiss_recommendation(rec_id: str) -> dict[str, Any]:
    """Dismiss a recommendation."""
    return {"status": "dismissed"}
