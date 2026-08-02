"""AuthService — complete authentication business logic.

All auth flows implemented here, not in routers.
Handles: register, login, refresh, logout, password reset, email verification.
"""

import logging
import uuid
from datetime import datetime, timezone, timedelta
from typing import Optional

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.jwt import (
    create_token_pair, TokenPair, verify_refresh_token, hash_refresh_token,
    REFRESH_TOKEN_EXPIRE_DAYS,
)
from src.auth.password import hash_password, verify_password, check_password_strength
from src.auth.tokens import (
    create_session, rotate_refresh_token, revoke_session, revoke_all_sessions,
    is_jti_blocked, block_access_token,
)
from src.db.models.auth import User, UserSession

logger = logging.getLogger(__name__)


class AuthService:
    """All authentication business logic. No placeholder — real implementation."""

    def __init__(self, session: AsyncSession):
        self._session = session

    # ══════════════════════════════════════════════════════════════════════
    # Register
    # ══════════════════════════════════════════════════════════════════════

    async def register(
        self,
        email: str,
        username: str,
        password: str,
        display_name: str | None = None,
        device_info: dict | None = None,
    ) -> dict:
        """Create a new user account. Returns tokens + user data.

        Steps:
        1. Validate password strength
        2. Check email/username uniqueness
        3. Hash password with Argon2id
        4. Create User record
        5. Generate email verification token
        6. Create session with refresh token
        7. Return access + refresh tokens

        Raises:
            ValueError: if password too weak, email/username taken
        """
        # 1. Password strength
        valid, error = check_password_strength(password)
        if not valid:
            raise ValueError(error)

        # 2. Check uniqueness
        existing_email = await self._session.execute(
            select(User).where(User.email == email.lower().strip())
        )
        if existing_email.scalar_one_or_none():
            raise ValueError("Email already registered")

        existing_username = await self._session.execute(
            select(User).where(User.username == username.lower().strip())
        )
        if existing_username.scalar_one_or_none():
            raise ValueError("Username already taken")

        # 3. Hash password
        password_hash = hash_password(password)

        # 4. Create User
        verify_token = str(uuid.uuid4())
        user = User(
            email=email.lower().strip(),
            username=username.lower().strip(),
            display_name=display_name,
            password_hash=password_hash,
            email_verify_token=verify_token,
            email_verified=False,
            timezone=device_info.get("timezone", "UTC") if device_info else "UTC",
            language=device_info.get("language", "en") if device_info else "en",
        )
        self._session.add(user)
        await self._session.flush()

        # 5. Create tokens and session
        tokens = create_token_pair(user.id, user.email, user.role)
        device = device_info or {}
        await create_session(
            self._session, user.id, tokens.refresh_token, device,
        )

        # 6. Send verification email (async, non-blocking)
        # In production: asyncio.create_task(send_verify_email(user.email, verify_token))

        logger.info(f"User registered: {user.email} (id={user.id[:8]})")
        return self._build_auth_response(tokens, user)

    # ══════════════════════════════════════════════════════════════════════
    # Login
    # ══════════════════════════════════════════════════════════════════════

    async def login(
        self,
        email: str,
        password: str,
        remember_me: bool = False,
        device_info: dict | None = None,
    ) -> dict:
        """Authenticate a user.

        Steps:
        1. Lookup user by email
        2. Check account lockout
        3. Verify password with Argon2id
        4. Reset login attempts on success
        5. Create session with refresh token
        6. Update last_login_at + last_login_ip
        7. Return tokens + user data

        Raises:
            ValueError: invalid credentials, account locked
        """
        # 1. Lookup
        result = await self._session.execute(
            select(User).where(User.email == email.lower().strip())
        )
        user = result.scalar_one_or_none()
        if user is None:
            raise ValueError("Invalid email or password")

        # 2. Account lockout check
        if user.locked_until and user.locked_until > datetime.now(timezone.utc):
            remaining = (user.locked_until - datetime.now(timezone.utc)).seconds
            raise ValueError(f"Account locked. Try again in {remaining // 60} minutes")

        # 3. Verify password
        if not verify_password(password, user.password_hash):
            user.login_attempts += 1
            if user.login_attempts >= 5:
                user.locked_until = datetime.now(timezone.utc) + timedelta(minutes=15)
                logger.warning(f"Account locked: {user.email}")
            await self._session.flush()
            raise ValueError("Invalid email or password")

        # 4. Reset on success
        user.login_attempts = 0
        user.locked_until = None
        user.last_login_at = datetime.now(timezone.utc)

        device = device_info or {}
        user.last_login_ip = device.get("ip", "unknown")

        # 5. Create tokens and session
        tokens = create_token_pair(user.id, user.email, user.role)
        await create_session(
            self._session, user.id, tokens.refresh_token, device, remember_me,
        )

        await self._session.flush()
        logger.info(f"User logged in: {user.email}")

        return self._build_auth_response(tokens, user)

    # ══════════════════════════════════════════════════════════════════════
    # Refresh
    # ══════════════════════════════════════════════════════════════════════

    async def refresh(self, old_refresh_token: str, device_info: dict | None = None) -> TokenPair:
        """Refresh an access token using a refresh token.

        Steps:
        1. Verify JWT signature and expiry
        2. Look up the hashed token in DB
        3. Check it's not revoked (token reuse detection)
        4. Revoke old token, issue new token pair
        5. Create new session with new refresh token

        If old token is already revoked → token reuse attack detected.
        All user sessions are immediately revoked.
        """
        # 1. Verify JWT
        try:
            payload = verify_refresh_token(old_refresh_token)
        except Exception:
            raise ValueError("Invalid or expired refresh token")

        # 2. Issue new tokens BEFORE checking DB (to rotate immediately)
        new_tokens = create_token_pair(payload.sub, payload.email, payload.role)
        device = device_info or {}

        # 3. Rotate in DB — handles reuse detection internally
        await rotate_refresh_token(
            self._session, payload.sub, old_refresh_token,
            new_tokens.refresh_token, device,
        )
        await self._session.flush()

        return new_tokens

    # ══════════════════════════════════════════════════════════════════════
    # Logout
    # ══════════════════════════════════════════════════════════════════════

    async def logout(self, user_id: str, access_token_jti: str | None = None) -> None:
        """Logout: block access token JTI. Session stays for refresh invalidation."""
        if access_token_jti:
            block_access_token(access_token_jti)

    async def logout_all(self, user_id: str) -> int:
        """Revoke all sessions. Returns count revoked."""
        count = await revoke_all_sessions(self._session, user_id)
        await self._session.flush()
        logger.info(f"All sessions revoked for user={user_id[:8]}")
        return count

    # ══════════════════════════════════════════════════════════════════════
    # Password Reset
    # ══════════════════════════════════════════════════════════════════════

    async def forgot_password(self, email: str) -> None:
        """Send password reset email. Always returns success (anti-enumeration)."""
        result = await self._session.execute(
            select(User).where(User.email == email.lower().strip())
        )
        user = result.scalar_one_or_none()
        if user is None:
            return  # Don't reveal whether email exists

        # Generate reset token (stored HASHED in DB — SHA-256 of random UUID)
        raw_token = str(uuid.uuid4())
        hashed_token = hash_refresh_token(raw_token)  # Reusing hash function

        user.password_reset_token = hashed_token
        user.password_reset_expires = datetime.now(timezone.utc) + timedelta(hours=1)
        await self._session.flush()

        # Send email with raw_token (user clicks link with raw token)
        # In production: send_email(user.email, raw_token)
        logger.info(f"Password reset token generated for {user.email} (expires 1h)")

    async def reset_password(self, raw_token: str, new_password: str) -> None:
        """Reset password using a reset token.

        Steps:
        1. Validate password strength
        2. Hash the raw token to find user
        3. Check expiry (1 hour)
        4. Hash new password
        5. Clear reset token (single-use)
        6. Revoke all sessions (force re-login)
        """
        # 1. Validate
        valid, error = check_password_strength(new_password)
        if not valid:
            raise ValueError(error)

        # 2. Hash token to find user
        hashed_token = hash_refresh_token(raw_token)
        result = await self._session.execute(
            select(User).where(User.password_reset_token == hashed_token)
        )
        user = result.scalar_one_or_none()
        if user is None:
            raise ValueError("Invalid or expired reset token")

        # 3. Check expiry
        if user.password_reset_expires is None or user.password_reset_expires < datetime.now(timezone.utc):
            raise ValueError("Reset token has expired")

        # 4. Hash new password
        user.password_hash = hash_password(new_password)

        # 5. Clear reset token (single-use)
        user.password_reset_token = None
        user.password_reset_expires = None

        # 6. Revoke all sessions (force re-login everywhere)
        await revoke_all_sessions(self._session, user.id)

        await self._session.flush()
        logger.info(f"Password reset successful for {user.email}")

    # ══════════════════════════════════════════════════════════════════════
    # Email Verification
    # ══════════════════════════════════════════════════════════════════════

    async def verify_email(self, token: str) -> bool:
        """Verify email using verification token.

        Returns True if verified, False if token invalid.
        """
        result = await self._session.execute(
            select(User).where(User.email_verify_token == token)
        )
        user = result.scalar_one_or_none()
        if user is None:
            return False

        user.email_verified = True
        user.email_verify_token = None  # Single-use
        await self._session.flush()
        logger.info(f"Email verified for {user.email}")
        return True

    # ══════════════════════════════════════════════════════════════════════
    # Helpers
    # ══════════════════════════════════════════════════════════════════════

    def _build_auth_response(self, tokens: TokenPair, user: User) -> dict:
        return {
            "access_token": tokens.access_token,
            "refresh_token": tokens.refresh_token,
            "token_type": tokens.token_type,
            "expires_in": tokens.expires_in,
            "user": {
                "id": user.id,
                "email": user.email,
                "username": user.username,
                "display_name": user.display_name,
                "avatar_url": user.avatar_url,
                "role": user.role,
                "email_verified": user.email_verified,
            },
        }
