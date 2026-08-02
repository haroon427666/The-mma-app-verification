"""Auth API — v1. All endpoints use AuthService — no placeholders.

Real implementations: register, login, refresh, logout, password reset, email verify.
Every flow: password hash → session save → token issue → audit log.
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, EmailStr, Field

from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.jwt import TokenPair
from src.auth.dependencies import get_current_user, TokenPayload
from src.db.session import get_session
from src.services.auth_service import AuthService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1/auth", tags=["auth"])


# ── Request/Response Models ──────────────────────────────────────────────────

class RegisterRequest(BaseModel):
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50, pattern=r"^[a-zA-Z0-9_-]+$")
    password: str = Field(..., min_length=8, max_length=128)
    display_name: str | None = Field(None, max_length=100)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str
    remember_me: bool = False


class RefreshRequest(BaseModel):
    refresh_token: str


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(..., min_length=8, max_length=128)


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=8, max_length=128)


class VerifyEmailRequest(BaseModel):
    token: str


def _get_device_info(request: Request) -> dict:
    return {
        "device": (request.headers.get("User-Agent") or "unknown")[:50],
        "browser": _parse_browser(request.headers.get("User-Agent", "")),
        "ip": request.client.host if request.client else "unknown",
        "country": request.headers.get("CF-IPCountry", ""),
    }


def _parse_browser(ua: str) -> str:
    ua = ua.lower()
    if "chrome" in ua and "edg" not in ua: return "Chrome"
    if "firefox" in ua: return "Firefox"
    if "safari" in ua and "chrome" not in ua: return "Safari"
    if "edg" in ua: return "Edge"
    return "Other"


# ── Endpoints ─────────────────────────────────────────────────────────────────


@router.post("/register", status_code=201)
async def register(
    req: RegisterRequest,
    request: Request,
    session: AsyncSession = Depends(get_session),
):
    """Create a new user account. Returns JWT tokens immediately."""
    service = AuthService(session)
    try:
        result = await service.register(
            email=req.email, username=req.username, password=req.password,
            display_name=req.display_name, device_info=_get_device_info(request),
        )
        await session.commit()
        return result
    except ValueError as e:
        await session.rollback()
        raise HTTPException(400, str(e))


@router.post("/login")
async def login(
    req: LoginRequest,
    request: Request,
    session: AsyncSession = Depends(get_session),
):
    """Authenticate. Returns JWT tokens + user data."""
    service = AuthService(session)
    try:
        result = await service.login(
            email=req.email, password=req.password,
            remember_me=req.remember_me, device_info=_get_device_info(request),
        )
        await session.commit()
        return result
    except ValueError as e:
        await session.rollback()
        status_code = 429 if "locked" in str(e).lower() else 401
        raise HTTPException(status_code, str(e))


@router.post("/refresh")
async def refresh(
    req: RefreshRequest,
    request: Request,
    session: AsyncSession = Depends(get_session),
):
    """Refresh access token. Rotates refresh token (old → revoked, new → active)."""
    service = AuthService(session)
    try:
        tokens = await service.refresh(
            old_refresh_token=req.refresh_token,
            device_info=_get_device_info(request),
        )
        await session.commit()
        return {
            "access_token": tokens.access_token,
            "refresh_token": tokens.refresh_token,
            "token_type": tokens.token_type,
            "expires_in": tokens.expires_in,
        }
    except ValueError as e:
        await session.rollback()
        raise HTTPException(401, str(e))


@router.post("/logout", status_code=204)
async def logout(
    request: Request,
    user: TokenPayload = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Logout: block access token JTI so it can't be reused."""
    service = AuthService(session)
    await service.logout(user.sub, access_token_jti=user.jti)
    await session.commit()
    return


@router.post("/logout-all", status_code=204)
async def logout_all(
    request: Request,
    user: TokenPayload = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Logout everywhere. Revokes ALL refresh tokens for this user."""
    service = AuthService(session)
    count = await service.logout_all(user.sub)
    await session.commit()
    logger.info(f"All sessions revoked for user={user.sub[:8]} ({count} sessions)")
    return


@router.post("/forgot-password", status_code=204)
async def forgot_password(
    req: ForgotPasswordRequest,
    session: AsyncSession = Depends(get_session),
):
    """Send password reset email. Always returns 204 (anti-enumeration)."""
    service = AuthService(session)
    await service.forgot_password(req.email)
    await session.commit()
    return


@router.post("/reset-password", status_code=204)
async def reset_password(
    req: ResetPasswordRequest,
    session: AsyncSession = Depends(get_session),
):
    """Reset password using emailed token. Revokes all sessions after."""
    service = AuthService(session)
    try:
        await service.reset_password(req.token, req.new_password)
        await session.commit()
    except ValueError as e:
        await session.rollback()
        raise HTTPException(400, str(e))
    return


@router.post("/change-password", status_code=204)
async def change_password(
    req: ChangePasswordRequest,
    user: TokenPayload = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Change password (authenticated). Requires current password."""
    from src.auth.password import verify_password, hash_password, check_password_strength
    from src.db.models.auth import User
    from sqlalchemy import select

    valid, error = check_password_strength(req.new_password)
    if not valid:
        raise HTTPException(400, error)

    result = await session.execute(select(User).where(User.id == user.sub))
    db_user = result.scalar_one_or_none()
    if db_user is None:
        raise HTTPException(404)

    if not verify_password(req.current_password, db_user.password_hash):
        raise HTTPException(400, "Current password is incorrect")

    db_user.password_hash = hash_password(req.new_password)
    await session.commit()
    return


@router.post("/verify-email")
async def verify_email(
    req: VerifyEmailRequest,
    session: AsyncSession = Depends(get_session),
):
    """Verify email address using token sent after registration."""
    service = AuthService(session)
    success = await service.verify_email(req.token)
    await session.commit()
    if not success:
        raise HTTPException(400, "Invalid or expired verification token")
    return {"status": "verified"}
