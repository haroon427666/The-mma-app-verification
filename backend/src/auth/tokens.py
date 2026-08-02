"""Token Revocation — JTI blacklist + refresh token reuse detection.

Prevents replay attacks:
- Access tokens: short-lived (15 min), checked against in-memory JTI blocklist
- Refresh tokens: SHA-256 hashed in DB, immediately revoked on rotation
- Reuse detection: if a revoked refresh token is presented, ALL user sessions revoked
"""

import hashlib
import logging
import time
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

# In-memory JTI blocklist — production: Redis SET with TTL
_blocked_jtis: dict[str, float] = {}


def block_access_token(jti: str, ttl_seconds: int = 900) -> None:
    """Block an access token JTI (for logout before expiry)."""
    _blocked_jtis[jti] = time.monotonic() + ttl_seconds
    # Clean expired entries
    now = time.monotonic()
    expired = [k for k, v in _blocked_jtis.items() if v < now]
    for k in expired:
        del _blocked_jtis[k]


def is_jti_blocked(jti: str) -> bool:
    """Check if a JTI has been revoked."""
    expires = _blocked_jtis.get(jti)
    if expires is None:
        return False
    if expires < time.monotonic():
        del _blocked_jtis[jti]
        return False
    return True


def hash_refresh_token(token: str) -> str:
    """One-way hash for storing refresh tokens in DB."""
    return hashlib.sha256(token.encode()).hexdigest()


async def rotate_refresh_token(
    session,
    user_id: str,
    old_token: str,
    new_token: str,
    device_info: dict,
) -> None:
    """Rotate refresh token: revoke old, store new.

    If old token is already revoked → token reuse attack detected.
    In that case, revoke ALL sessions for the user.

    Args:
        session: Async database session
        user_id: User UUID
        old_token: The refresh token being replaced (raw)
        new_token: The new refresh token (raw)
        device_info: {device, browser, ip, country}
    """
    from src.db.models.auth import UserSession
    from sqlalchemy import select, update
    from datetime import timedelta
    import uuid

    old_hash = hash_refresh_token(old_token)
    new_hash = hash_refresh_token(new_token)

    # Check if old token exists and is not revoked
    result = await session.execute(
        select(UserSession).where(
            UserSession.refresh_token_hash == old_hash,
            UserSession.user_id == user_id,
        )
    )
    existing = result.scalar_one_or_none()

    if existing is None:
        # Token not found — might already be rotated
        logger.warning(f"Refresh token not found for user={user_id}")
        return

    if existing.revoked:
        # TOKEN REUSE ATTACK — revoke ALL sessions
        logger.critical(
            f"REFRESH TOKEN REUSE DETECTED — user={user_id}, "
            f"revoking all sessions"
        )
        await session.execute(
            update(UserSession)
            .where(UserSession.user_id == user_id)
            .values(revoked=True)
        )
        await session.flush()
        return

    # Normal rotation: revoke old, create new
    existing.revoked = True
    existing.last_seen = datetime.now(timezone.utc)

    # Create new session with new refresh token
    new_session = UserSession(
        user_id=user_id,
        refresh_token_hash=new_hash,
        device=device_info.get("device", "unknown"),
        browser=device_info.get("browser", "unknown"),
        ip_address=device_info.get("ip", "unknown"),
        country=device_info.get("country"),
        last_seen=datetime.now(timezone.utc),
        expires_at=datetime.now(timezone.utc) + timedelta(days=7),
        revoked=False,
    )
    session.add(new_session)
    await session.flush()


async def create_session(
    session,
    user_id: str,
    refresh_token: str,
    device_info: dict,
    remember_me: bool = False,
) -> str:
    """Create a new session with a refresh token. Returns the hashed token."""
    from src.db.models.auth import UserSession
    from datetime import timedelta

    token_hash = hash_refresh_token(refresh_token)
    expiry_days = 30 if remember_me else 7

    user_session = UserSession(
        user_id=user_id,
        refresh_token_hash=token_hash,
        device=device_info.get("device", "unknown"),
        browser=device_info.get("browser", "unknown"),
        ip_address=device_info.get("ip", "unknown"),
        country=device_info.get("country"),
        last_seen=datetime.now(timezone.utc),
        expires_at=datetime.now(timezone.utc) + timedelta(days=expiry_days),
        revoked=False,
    )
    session.add(user_session)
    await session.flush()
    return token_hash


async def revoke_session(session, session_id: str, user_id: str) -> bool:
    """Revoke a specific session. Returns True if found and revoked."""
    from src.db.models.auth import UserSession
    from sqlalchemy import update

    result = await session.execute(
        update(UserSession)
        .where(UserSession.id == session_id, UserSession.user_id == user_id)
        .values(revoked=True)
    )
    return result.rowcount > 0


async def revoke_all_sessions(session, user_id: str) -> int:
    """Revoke all sessions for a user. Returns count revoked."""
    from src.db.models.auth import UserSession
    from sqlalchemy import update

    result = await session.execute(
        update(UserSession)
        .where(UserSession.user_id == user_id, UserSession.revoked == False)
        .values(revoked=True)
    )
    return result.rowcount
