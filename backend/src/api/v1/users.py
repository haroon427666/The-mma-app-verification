"""User API — v1. Profile, preferences, favorites, watchlist, notifications, sessions."""

import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from src.auth.dependencies import get_current_user, TokenPayload

logger = logging.getLogger(__name__)

user_router = APIRouter(prefix="/v1/me", tags=["user"])
pref_router = APIRouter(prefix="/v1/me/preferences", tags=["preferences"])
fav_router = APIRouter(prefix="/v1/me/favorites", tags=["favorites"])
watch_router = APIRouter(prefix="/v1/me/watchlist", tags=["watchlist"])
notif_router = APIRouter(prefix="/v1/notifications", tags=["notifications"])
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


class NotificationItem(BaseModel):
    id: str
    type: str
    title: str
    message: str | None = None
    payload: dict | None = None
    read: bool = False
    created_at: datetime | None = None


# ── Profile ───────────────────────────────────────────────────────────────────

@user_router.get("", response_model=ProfileResponse)
async def get_profile(user: TokenPayload = Depends(get_current_user)):
    return ProfileResponse(
        id=user.sub, email=user.email, username=user.email.split("@")[0],
        role=user.role,
    )


@user_router.patch("", response_model=ProfileResponse)
async def update_profile(
    req: UpdateProfileRequest,
    user: TokenPayload = Depends(get_current_user),
):
    # Production: update user in DB
    return ProfileResponse(
        id=user.sub, email=user.email, username=user.email.split("@")[0],
        role=user.role, display_name=req.display_name, country=req.country,
        timezone=req.timezone, language=req.language,
    )


@user_router.delete("", status_code=204)
async def delete_account(user: TokenPayload = Depends(get_current_user)):
    """Permanently delete account and all associated data."""
    # Production: soft-delete user, revoke all sessions, schedule data cleanup
    return


# ── Preferences ────────────────────────────────────────────────────────────────

@pref_router.get("", response_model=PreferencesResponse)
async def get_preferences(user: TokenPayload = Depends(get_current_user)):
    return PreferencesResponse()


@pref_router.patch("", response_model=PreferencesResponse)
async def update_preferences(
    req: UpdatePreferencesRequest,
    user: TokenPayload = Depends(get_current_user),
):
    # Production: merge partial update with existing preferences
    return PreferencesResponse(**req.model_dump(exclude_unset=True))


# ── Favorites ──────────────────────────────────────────────────────────────────

@fav_router.get("", response_model=FavoriteResponse)
async def get_favorites(user: TokenPayload = Depends(get_current_user)):
    return FavoriteResponse()


@fav_router.post("/fighters/{fighter_id}", status_code=201)
async def favorite_fighter(fighter_id: str, user: TokenPayload = Depends(get_current_user)):
    return {"status": "added", "fighter_id": fighter_id}


@fav_router.delete("/fighters/{fighter_id}", status_code=204)
async def unfavorite_fighter(fighter_id: str, user: TokenPayload = Depends(get_current_user)):
    return


@fav_router.post("/events/{event_id}", status_code=201)
async def favorite_event(event_id: str, user: TokenPayload = Depends(get_current_user)):
    return {"status": "added", "event_id": event_id}


@fav_router.delete("/events/{event_id}", status_code=204)
async def unfavorite_event(event_id: str, user: TokenPayload = Depends(get_current_user)):
    return


@fav_router.post("/promotions/{slug}", status_code=201)
async def favorite_promotion(slug: str, user: TokenPayload = Depends(get_current_user)):
    return {"status": "added", "slug": slug}


@fav_router.delete("/promotions/{slug}", status_code=204)
async def unfavorite_promotion(slug: str, user: TokenPayload = Depends(get_current_user)):
    return


# ── Watchlist ──────────────────────────────────────────────────────────────────

@watch_router.get("", response_model=WatchlistResponse)
async def get_watchlist(user: TokenPayload = Depends(get_current_user)):
    return WatchlistResponse()


@watch_router.post("/events/{event_id}", status_code=201)
async def watchlist_event(event_id: str, user: TokenPayload = Depends(get_current_user)):
    return {"status": "added", "event_id": event_id}


@watch_router.delete("/events/{event_id}", status_code=204)
async def unwatchlist_event(event_id: str, user: TokenPayload = Depends(get_current_user)):
    return


# ── Notifications ──────────────────────────────────────────────────────────────

@notif_router.get("", response_model=list[NotificationItem])
async def get_notifications(
    read: bool | None = Query(None, description="Filter: read/unread/all"),
    limit: int = Query(50, le=100),
    user: TokenPayload = Depends(get_current_user),
):
    return []


@notif_router.patch("/{notification_id}", response_model=NotificationItem)
async def mark_notification_read(
    notification_id: str,
    user: TokenPayload = Depends(get_current_user),
):
    raise HTTPException(404)


@notif_router.patch("/read-all", status_code=204)
async def mark_all_read(user: TokenPayload = Depends(get_current_user)):
    return


# ── Sessions ───────────────────────────────────────────────────────────────────

@session_router.get("", response_model=list[SessionResponse])
async def get_sessions(user: TokenPayload = Depends(get_current_user)):
    return []


@session_router.delete("/{session_id}", status_code=204)
async def revoke_session(
    session_id: str,
    user: TokenPayload = Depends(get_current_user),
):
    """Revoke a specific session (logout on that device)."""
    return


@session_router.delete("", status_code=204)
async def revoke_all_sessions(user: TokenPayload = Depends(get_current_user)):
    """Revoke all sessions except current (logout everywhere else)."""
    return
