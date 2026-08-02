"""Watchlist API — favorites, watchlist, reminders. Auth-required."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.session import get_session
from src.auth.dependencies import get_current_user, TokenPayload

router = APIRouter(prefix="/v1/watchlist", tags=["watchlist"])


@router.get("/events")
async def watchlist_events(
    user: TokenPayload = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """User's watchlisted events."""
    from sqlalchemy import select as sa_select
    from src.db.models.auth import WatchlistEvent
    from src.db.models.event import Event
    result = await session.execute(
        sa_select(Event).join(WatchlistEvent, WatchlistEvent.event_id == Event.id)
        .where(WatchlistEvent.user_id == user.sub)
        .order_by(Event.date_utc.asc()).limit(50)
    )
    events = []
    for e in result.scalars().all():
        events.append({"id": e.id, "title": e.name, "subtitle": e.status, "date": str(e.date_utc) if e.date_utc else None})
    return {"data": events}


@router.get("/fighters")
async def watchlist_fighters(
    user: TokenPayload = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """User's favorited fighters."""
    from sqlalchemy import select as sa_select
    from src.db.models.auth import FighterFavorite
    from src.db.models.fighter import Fighter
    result = await session.execute(
        sa_select(Fighter).join(FighterFavorite, FighterFavorite.fighter_id == Fighter.id)
        .where(FighterFavorite.user_id == user.sub).limit(100)
    )
    fighters = []
    for f in result.scalars().all():
        fighters.append({"id": f.id, "title": f"{f.first_name} {f.last_name}", "subtitle": f.weight_class_name, "date": None, "imageUrl": f.headshot_url})
    return {"data": fighters}


@router.post("/events/{event_id}", status_code=201)
async def add_event_watchlist(
    event_id: str,
    user: TokenPayload = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Add event to watchlist."""
    from src.db.models.auth import WatchlistEvent
    wl = WatchlistEvent(user_id=user.sub, event_id=event_id)
    session.add(wl)
    await session.flush()
    await session.commit()
    return {"status": "added"}


@router.delete("/events/{event_id}", status_code=204)
async def remove_event_watchlist(
    event_id: str,
    user: TokenPayload = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Remove event from watchlist."""
    from sqlalchemy import delete as sa_delete
    from src.db.models.auth import WatchlistEvent
    await session.execute(
        sa_delete(WatchlistEvent).where(
            WatchlistEvent.user_id == user.sub,
            WatchlistEvent.event_id == event_id,
        )
    )
    await session.commit()
    return


@router.post("/fighters/{fighter_id}", status_code=201)
async def add_fighter_favorite(
    fighter_id: str,
    user: TokenPayload = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Add fighter to favorites."""
    from src.db.models.auth import FighterFavorite
    fav = FighterFavorite(user_id=user.sub, fighter_id=fighter_id)
    session.add(fav)
    await session.flush()
    await session.commit()
    return {"status": "favorited"}


@router.delete("/fighters/{fighter_id}", status_code=204)
async def remove_fighter_favorite(
    fighter_id: str,
    user: TokenPayload = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Remove fighter from favorites."""
    from sqlalchemy import delete as sa_delete
    from src.db.models.auth import FighterFavorite
    await session.execute(
        sa_delete(FighterFavorite).where(
            FighterFavorite.user_id == user.sub,
            FighterFavorite.fighter_id == fighter_id,
        )
    )
    await session.commit()
    return
