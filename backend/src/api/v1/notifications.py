"""Notifications API — inbox, preferences, push tokens. Auth-required."""

from typing import Any, cast

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.utils import require_uuid
from src.auth.dependencies import get_current_user
from src.auth.jwt import TokenPayload
from src.db.session import get_session

router = APIRouter(prefix="/v1/notifications", tags=["notifications"])


@router.get("")
async def list_notifications(
    limit: int = Query(40, le=100),
    user: TokenPayload = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    """User's notifications — newest first."""
    from sqlalchemy import select as sa_select

    from src.db.models.auth import Notification
    result = await session.execute(
        sa_select(Notification)
        .where(Notification.user_id == user.sub)
        .order_by(Notification.created_at.desc())
        .limit(limit)
    )
    items = []
    for n in result.scalars().all():
        items.append({
            "id": n.id, "category": n.ntype or "system",
            "title": n.title, "message": n.message or "",
            "read": n.read or False,
            "createdAt": n.created_at.isoformat() if n.created_at else "",
            "deepLink": n.payload.get("deep_link") if n.payload else None,
            "actionable": bool(n.payload),
        })
    return {"data": items}


@router.patch("/{notif_id}/read")
async def mark_read(
    notif_id: str,
    user: TokenPayload = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> dict[str, str]:
    """Mark a notification as read."""
    require_uuid(notif_id)
    from sqlalchemy import update as sa_update

    from src.db.models.auth import Notification
    await session.execute(
        sa_update(Notification)
        .where(Notification.id == notif_id, Notification.user_id == user.sub)
        .values(read=True)
    )
    await session.commit()
    return {"status": "read"}


@router.patch("/read-all")
async def mark_all_read(
    user: TokenPayload = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> dict[str, str]:
    """Mark all notifications as read."""
    from sqlalchemy import update as sa_update

    from src.db.models.auth import Notification
    await session.execute(
        sa_update(Notification)
        .where(Notification.user_id == user.sub, Notification.read == False)
        .values(read=True)
    )
    await session.commit()
    return {"status": "all_read"}


@router.delete("/{notif_id}", status_code=204)
async def delete_notification(
    notif_id: str,
    user: TokenPayload = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> None:
    """Delete a notification."""
    require_uuid(notif_id)
    from sqlalchemy import delete as sa_delete

    from src.db.models.auth import Notification
    await session.execute(
        sa_delete(Notification).where(
            Notification.id == notif_id, Notification.user_id == user.sub,
        )
    )
    await session.commit()


@router.get("/unread-count")
async def unread_count(
    user: TokenPayload = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    """Count of unread notifications."""
    from sqlalchemy import func
    from sqlalchemy import select as sa_select

    from src.db.models.auth import Notification
    result = await session.execute(
        sa_select(func.count())
        .select_from(Notification)
        .where(Notification.user_id == user.sub, Notification.read == False)
    )
    return {"count": result.scalar_one()}


@router.get("/preferences")
async def get_preferences(
    user: TokenPayload = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    """User's notification preferences."""
    from sqlalchemy import select as sa_select

    from src.db.models.auth import UserPreference
    result = await session.execute(
        sa_select(UserPreference).where(UserPreference.user_id == user.sub)
    )
    pref = result.scalar_one_or_none()
    prefs = cast(Any, pref)
    return {"data": prefs.notification_prefs if pref and prefs.notification_prefs else {}}


@router.put("/preferences")
async def update_preferences(
    body: dict[str, Any],
    user: TokenPayload = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    """Update notification preferences."""
    from sqlalchemy import select as sa_select

    from src.db.models.auth import UserPreference
    result = await session.execute(
        sa_select(UserPreference).where(UserPreference.user_id == user.sub)
    )
    pref = result.scalar_one_or_none()
    if pref:
        cast(Any, pref).notification_prefs = body
    else:
        pref = UserPreference(user_id=user.sub, notification_prefs=body)
        session.add(pref)
    await session.flush()
    await session.commit()
    return {"status": "updated"}


@router.post("/push-token", status_code=201)
async def register_push_token(
    body: dict[str, Any],
    user: TokenPayload = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> dict[str, str]:
    """Register device push token."""
    from src.db.models.auth import Device
    token = body.get("token", "")
    device = Device(
        user_id=user.sub,
        device_token=token,
        platform=body.get("platform", "mobile"),
        active=True,
    )
    session.add(device)
    await session.flush()
    await session.commit()
    return {"status": "registered"}
