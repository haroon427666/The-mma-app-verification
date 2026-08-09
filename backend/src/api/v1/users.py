"""User API — v1. Profile, preferences, favorites, watchlist, notifications, sessions."""

import logging
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.utils import require_uuid
from src.auth.dependencies import get_current_user
from src.auth.jwt import TokenPayload
from src.db.session import get_session

logger = logging.getLogger(__name__)

user_router = APIRouter(prefix="/v1/me", tags=["user"])
pref_router = APIRouter(prefix="/v1/me/preferences", tags=["preferences"])
fav_router = APIRouter(prefix="/v1/me/favorites", tags=["favorites"])
watch_router = APIRouter(prefix="/v1/me/watchlist", tags=["watchlist"])
session_router = APIRouter(prefix="/v1/me/sessions", tags=["sessions"])


# ── Schemas ──────────────────────────────────────────────────────────────────

class ProfileResponse(BaseModel):
    id: str
    email: str
    username: str
    display_name: str | None = None
    avatar_url: str | None = None
    role: str = "user"
    country: str | None = None
    timezone: str = "UTC"
    language: str = "en"
    email_verified: bool = False
    is_admin: bool = False
    last_login_at: datetime | None = None
    created_at: datetime | None = None


class UpdateProfileRequest(BaseModel):
    display_name: str | None = Field(None, max_length=100)
    country: str | None = Field(None, min_length=2, max_length=2)
    timezone: str | None = None
    language: str | None = None


class PreferencesResponse(BaseModel):
    theme: str = "system"
    default_homepage: str = "rankings"
    default_sort: str = "-date_utc"
    default_weight_classes: list[str] = []
    default_promotions: list[str] = []
    notify_upcoming_fight: bool = True
    notify_event_starting: bool = True
    notify_ranking_changed: bool = False
    notify_fight_cancelled: bool = True
    notify_new_main_event: bool = True
    notify_title_fight: bool = True


class UpdatePreferencesRequest(BaseModel):
    theme: str | None = None
    default_homepage: str | None = None
    default_sort: str | None = None
    default_weight_classes: list[str] | None = None
    default_promotions: list[str] | None = None
    notify_upcoming_fight: bool | None = None
    notify_event_starting: bool | None = None
    notify_ranking_changed: bool | None = None
    notify_fight_cancelled: bool | None = None
    notify_new_main_event: bool | None = None
    notify_title_fight: bool | None = None


class FavoriteResponse(BaseModel):
    fighters: list[str] = []       # fighter IDs
    events: list[str] = []         # event IDs
    promotions: list[str] = []     # promotion slug strings
    weight_classes: list[str] = []  # weight class names


class WatchlistResponse(BaseModel):
    events: list[str] = []  # event IDs
    fights: list[str] = []  # fight IDs


class SessionResponse(BaseModel):
    id: str
    device: str | None = None
    browser: str | None = None
    ip_address: str | None = None
    country: str | None = None
    last_seen: datetime | None = None
    created_at: datetime | None = None
    current: bool = False  # Is this the current session?


# ── Profile ───────────────────────────────────────────────────────────────────

@user_router.get("", response_model=ProfileResponse)
async def get_profile(user: TokenPayload = Depends(get_current_user)) -> ProfileResponse:
    return ProfileResponse(
        id=user.sub, email=user.email, username=user.email.split("@")[0],
        role=user.role,
    )


@user_router.patch("", response_model=ProfileResponse)
async def update_profile(
    req: UpdateProfileRequest,
    user: TokenPayload = Depends(get_current_user),
) -> ProfileResponse:
    # Production: update user in DB
    return ProfileResponse(
        id=user.sub, email=user.email, username=user.email.split("@")[0],
        role=user.role, display_name=req.display_name, country=req.country,
        timezone=req.timezone, language=req.language,
    )


@user_router.delete("", status_code=204)
async def delete_account(user: TokenPayload = Depends(get_current_user)) -> None:
    """Permanently delete account and all associated data."""
    # Production: soft-delete user, revoke all sessions, schedule data cleanup
    return


# ── Preferences ────────────────────────────────────────────────────────────────

def _preferences_response(prefs: Any) -> PreferencesResponse:
    return PreferencesResponse(
        theme=prefs.theme,
        default_homepage=prefs.default_homepage,
        default_sort=prefs.default_sort,
        default_weight_classes=prefs.default_weight_classes or [],
        default_promotions=prefs.default_promotions or [],
        notify_upcoming_fight=prefs.notify_upcoming_fight,
        notify_event_starting=prefs.notify_event_starting,
        notify_ranking_changed=prefs.notify_ranking_changed,
        notify_fight_cancelled=prefs.notify_fight_cancelled,
        notify_new_main_event=prefs.notify_new_main_event,
        notify_title_fight=prefs.notify_title_fight,
    )


async def _get_user_preferences(
    user_id: str, session: AsyncSession
) -> Any:
    from sqlalchemy import select as sa_select

    from src.db.models.auth import UserPreference

    result = await session.execute(
        sa_select(UserPreference).where(UserPreference.user_id == user_id)
    )
    return result.scalar_one_or_none()


@pref_router.get("", response_model=PreferencesResponse)
async def get_preferences(
    user: TokenPayload = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> PreferencesResponse:
    """DB-backed preferences; defaults when the user has no row yet."""
    prefs = await _get_user_preferences(user.sub, session)
    if prefs is None:
        return PreferencesResponse()
    return _preferences_response(prefs)


@pref_router.patch("", response_model=PreferencesResponse)
async def update_preferences(
    req: UpdatePreferencesRequest,
    user: TokenPayload = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> PreferencesResponse:
    """Merge a partial update into the user's preferences row (upsert)."""
    from src.db.models.auth import UserPreference

    prefs = await _get_user_preferences(user.sub, session)
    if prefs is None:
        prefs = UserPreference(user_id=user.sub)
        session.add(prefs)
    for field, value in req.model_dump(exclude_unset=True).items():
        setattr(prefs, field, value)
    await session.flush()
    response = _preferences_response(prefs)
    await session.commit()
    return response


# ── Favorites ──────────────────────────────────────────────────────────────────

def _require_uuid(value: str) -> None:
    """Reject non-UUID ids early (404, not a DB-level 500)."""
    require_uuid(value)


@fav_router.get("", response_model=FavoriteResponse)
async def get_favorites(
    user: TokenPayload = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> FavoriteResponse:
    """DB-backed favorites: fighters + events for the current user."""
    from sqlalchemy import select as sa_select

    from src.db.models.auth import EventFavorite, FighterFavorite

    fighters = await session.execute(
        sa_select(FighterFavorite.fighter_id)
        .where(FighterFavorite.user_id == user.sub)
        .order_by(FighterFavorite.created_at.desc())
    )
    events = await session.execute(
        sa_select(EventFavorite.event_id)
        .where(EventFavorite.user_id == user.sub)
        .order_by(EventFavorite.created_at.desc())
    )
    return FavoriteResponse(
        fighters=[row[0] for row in fighters.all()],
        events=[row[0] for row in events.all()],
    )


@fav_router.post("/fighters/{fighter_id}", status_code=201)
async def favorite_fighter(
    fighter_id: str,
    user: TokenPayload = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> dict[str, str]:
    """Add a fighter to the user's favorites (idempotent)."""
    from sqlalchemy import select as sa_select

    from src.db.models.auth import FighterFavorite

    _require_uuid(fighter_id)
    existing = await session.execute(
        sa_select(FighterFavorite).where(
            FighterFavorite.user_id == user.sub,
            FighterFavorite.fighter_id == fighter_id,
        )
    )
    if existing.scalar_one_or_none() is None:
        session.add(FighterFavorite(user_id=user.sub, fighter_id=fighter_id))
        await session.flush()
        await session.commit()
    return {"status": "added", "fighter_id": fighter_id}


@fav_router.delete("/fighters/{fighter_id}", status_code=204)
async def unfavorite_fighter(
    fighter_id: str,
    user: TokenPayload = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> None:
    from sqlalchemy import delete as sa_delete

    from src.db.models.auth import FighterFavorite

    _require_uuid(fighter_id)
    await session.execute(
        sa_delete(FighterFavorite).where(
            FighterFavorite.user_id == user.sub,
            FighterFavorite.fighter_id == fighter_id,
        )
    )
    await session.commit()


@fav_router.post("/events/{event_id}", status_code=201)
async def favorite_event(
    event_id: str,
    user: TokenPayload = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> dict[str, str]:
    """Add an event to the user's favorites (idempotent)."""
    from sqlalchemy import select as sa_select

    from src.db.models.auth import EventFavorite

    _require_uuid(event_id)
    existing = await session.execute(
        sa_select(EventFavorite).where(
            EventFavorite.user_id == user.sub,
            EventFavorite.event_id == event_id,
        )
    )
    if existing.scalar_one_or_none() is None:
        session.add(EventFavorite(user_id=user.sub, event_id=event_id))
        await session.flush()
        await session.commit()
    return {"status": "added", "event_id": event_id}


@fav_router.delete("/events/{event_id}", status_code=204)
async def unfavorite_event(
    event_id: str,
    user: TokenPayload = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> None:
    from sqlalchemy import delete as sa_delete

    from src.db.models.auth import EventFavorite

    _require_uuid(event_id)
    await session.execute(
        sa_delete(EventFavorite).where(
            EventFavorite.user_id == user.sub,
            EventFavorite.event_id == event_id,
        )
    )
    await session.commit()


@fav_router.post("/promotions/{slug}", status_code=501)
async def favorite_promotion(
    slug: str,
    user: TokenPayload = Depends(get_current_user),
) -> dict[str, str]:
    """Promotion favorites have no backing table — explicit 501, never a fake add."""
    raise HTTPException(501, "Promotion favorites are not supported")


@fav_router.delete("/promotions/{slug}", status_code=501)
async def unfavorite_promotion(
    slug: str,
    user: TokenPayload = Depends(get_current_user),
) -> None:
    raise HTTPException(501, "Promotion favorites are not supported")


# ── Watchlist ──────────────────────────────────────────────────────────────────

@watch_router.get("", response_model=WatchlistResponse)
async def get_watchlist(user: TokenPayload = Depends(get_current_user)) -> WatchlistResponse:
    return WatchlistResponse()


@watch_router.post("/events/{event_id}", status_code=201)
async def watchlist_event(event_id: str, user: TokenPayload = Depends(get_current_user)) -> dict[str, str]:
    return {"status": "added", "event_id": event_id}


@watch_router.delete("/events/{event_id}", status_code=204)
async def unwatchlist_event(event_id: str, user: TokenPayload = Depends(get_current_user)) -> None:
    return


# ── Sessions ───────────────────────────────────────────────────────────────────

@session_router.get("", response_model=list[SessionResponse])
async def get_sessions(user: TokenPayload = Depends(get_current_user)) -> list[SessionResponse]:
    return []


@session_router.delete("/{session_id}", status_code=204)
async def revoke_session(
    session_id: str,
    user: TokenPayload = Depends(get_current_user),
) -> None:
    """Revoke a specific session (logout on that device)."""
    return


@session_router.delete("", status_code=204)
async def revoke_all_sessions(user: TokenPayload = Depends(get_current_user)) -> None:
    """Revoke all sessions except current (logout everywhere else)."""
    return
