"""End-to-end auth flow tests — every security-critical path verified.

Uses SQLite in-memory for real DB state verification.
Tests register, login, refresh, logout, password reset, email verify,
RBAC enforcement, token reuse detection, duplicate prevention.
"""

from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine


@pytest.fixture
async def db_session():
    """In-memory SQLite session for test isolation."""
    engine = create_async_engine("sqlite+aiosqlite://", echo=False)
    async with engine.begin() as conn:
        import src.db.models
        import src.db.models.auth
        import src.db.models.support  # noqa: F401
        from src.db.base import Base
        await conn.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, class_=AsyncSession)
    async with factory() as session:
        yield session
    await engine.dispose()


# ═══════════════════════════════════════════════════════════════════════════════
# 1. Register → Verify DB state
# ═══════════════════════════════════════════════════════════════════════════════

class TestRegisterFlow:
    @pytest.mark.asyncio
    async def test_register_creates_user_in_db(self, db_session):
        from sqlalchemy import select

        from src.db.models.auth import User
        from src.services.auth_service import AuthService

        service = AuthService(db_session)
        result = await service.register(
            email="test@example.com", username="testuser",
            password="MySecurePass123!",
            device_info={"device": "pytest", "browser": "Chrome", "ip": "127.0.0.1"},
        )

        # Check tokens returned
        assert "access_token" in result
        assert "refresh_token" in result
        assert result["token_type"] == "bearer"

        # Verify user in DB
        db_result = await db_session.execute(
            select(User).where(User.email == "test@example.com")
        )
        user = db_result.scalar_one_or_none()
        assert user is not None
        assert user.username == "testuser"
        assert user.email_verified is False
        assert user.email_verify_token is not None  # Verification token generated
        assert user.role == "user"

    @pytest.mark.asyncio
    async def test_register_rejects_weak_password(self, db_session):
        from src.services.auth_service import AuthService
        service = AuthService(db_session)
        with pytest.raises(ValueError, match="8 characters"):
            await service.register(
                email="x@x.com", username="user1",
                password="Ab1",  # Too short
            )

    @pytest.mark.asyncio
    async def test_register_rejects_duplicate_email(self, db_session):
        from src.services.auth_service import AuthService
        service = AuthService(db_session)
        await service.register(email="dup@example.com", username="user1", password="MySecurePass123!")
        await db_session.commit()

        with pytest.raises(ValueError, match="Email already registered"):
            await service.register(email="dup@example.com", username="user2", password="AnotherPass456!")

    @pytest.mark.asyncio
    async def test_register_creates_session(self, db_session):
        from sqlalchemy import select

        from src.db.models.auth import UserSession
        from src.services.auth_service import AuthService

        service = AuthService(db_session)
        result = await service.register(
            email="session@example.com", username="sessionuser",
            password="MySecurePass123!",
            device_info={"device": "iPhone", "browser": "Safari", "ip": "10.0.0.1"},
        )

        # Verify session in DB
        session_result = await db_session.execute(
            select(UserSession).where(UserSession.user_id == result["user"]["id"])
        )
        sessions = session_result.scalars().all()
        assert len(sessions) == 1
        assert sessions[0].device == "iPhone"
        assert sessions[0].browser == "Safari"
        assert sessions[0].revoked is False


# ═══════════════════════════════════════════════════════════════════════════════
# 2. Login → Verify session + last_login
# ═══════════════════════════════════════════════════════════════════════════════

class TestLoginFlow:
    @pytest.mark.asyncio
    async def test_login_success(self, db_session):
        from sqlalchemy import select

        from src.db.models.auth import User
        from src.services.auth_service import AuthService

        service = AuthService(db_session)
        # Register first
        await service.register(
            email="login@example.com", username="loginuser",
            password="MySecurePass123!",
        )
        await db_session.commit()

        # Now login
        result = await service.login(
            email="login@example.com", password="MySecurePass123!",
            device_info={"device": "MacBook", "browser": "Chrome", "ip": "192.168.1.1"},
        )
        assert "access_token" in result
        assert result["user"]["email"] == "login@example.com"

        # Verify last_login updated
        db_result = await db_session.execute(
            select(User).where(User.email == "login@example.com")
        )
        user = db_result.scalar_one_or_none()
        assert user.last_login_at is not None
        assert user.last_login_ip == "192.168.1.1"
        assert user.login_attempts == 0

    @pytest.mark.asyncio
    async def test_login_wrong_password(self, db_session):
        from sqlalchemy import select

        from src.db.models.auth import User
        from src.services.auth_service import AuthService

        service = AuthService(db_session)
        await service.register(email="wrong@example.com", username="wronguser", password="CorrectPass123!")
        await db_session.commit()

        with pytest.raises(ValueError, match="Invalid email or password"):
            await service.login(email="wrong@example.com", password="WRONG_PASSWORD")

        # Verify login_attempts incremented
        db_result = await db_session.execute(
            select(User).where(User.email == "wrong@example.com")
        )
        user = db_result.scalar_one_or_none()
        assert user.login_attempts == 1

    @pytest.mark.asyncio
    async def test_account_lockout_after_5_failures(self, db_session):

        from src.services.auth_service import AuthService

        service = AuthService(db_session)
        await service.register(email="lock@example.com", username="lockuser", password="CorrectPass123!")
        await db_session.commit()

        # Fail 5 times
        for _ in range(5):
            try:
                await service.login(email="lock@example.com", password="WRONG")
            except ValueError:
                pass

        # Now locked
        with pytest.raises(ValueError, match="Account locked"):
            await service.login(email="lock@example.com", password="CorrectPass123!")


# ═══════════════════════════════════════════════════════════════════════════════
# 3. Refresh → Rotation + Reuse Detection
# ═══════════════════════════════════════════════════════════════════════════════

class TestRefreshFlow:
    @pytest.mark.asyncio
    async def test_refresh_rotates_token(self, db_session):
        from sqlalchemy import select

        from src.db.models.auth import UserSession
        from src.services.auth_service import AuthService

        service = AuthService(db_session)
        result = await service.register(
            email="rotate@example.com", username="rotateuser",
            password="MySecurePass123!",
        )
        await db_session.commit()
        old_refresh = result["refresh_token"]

        # Refresh
        new_tokens = await service.refresh(old_refresh, {"device": "iPhone"})
        await db_session.commit()
        assert new_tokens.access_token != result["access_token"]
        assert new_tokens.refresh_token != old_refresh

        # Old refresh token should be revoked in DB
        from src.auth.tokens import hash_refresh_token
        old_hash = hash_refresh_token(old_refresh)
        session_result = await db_session.execute(
            select(UserSession).where(UserSession.refresh_token_hash == old_hash)
        )
        old_session = session_result.scalar_one_or_none()
        assert old_session.revoked is True

    @pytest.mark.asyncio
    async def test_reuse_detection_revokes_all(self, db_session):
        from sqlalchemy import select

        from src.db.models.auth import UserSession
        from src.services.auth_service import AuthService

        service = AuthService(db_session)
        result = await service.register(
            email="reuse@example.com", username="reuseuser",
            password="MySecurePass123!",
        )
        await db_session.commit()
        old_refresh = result["refresh_token"]

        # First refresh → rotates normally
        await service.refresh(old_refresh, {})
        await db_session.commit()

        # Second refresh with SAME old token → reuse detected
        await service.refresh(old_refresh, {})
        await db_session.commit()

        # All sessions should be revoked
        session_result = await db_session.execute(
            select(UserSession).where(
                UserSession.user_id == result["user"]["id"],
                UserSession.revoked == False,
            )
        )
        active = session_result.scalars().all()
        assert len(active) == 0  # Everything revoked


# ═══════════════════════════════════════════════════════════════════════════════
# 4. Password Reset → Hashed, single-use, expiry
# ═══════════════════════════════════════════════════════════════════════════════

class TestPasswordReset:
    @pytest.mark.asyncio
    async def test_reset_token_is_hashed(self, db_session):
        from sqlalchemy import select

        from src.db.models.auth import User
        from src.services.auth_service import AuthService

        service = AuthService(db_session)
        await service.register(email="reset@example.com", username="resetuser", password="OldPass123!")
        await db_session.commit()

        await service.forgot_password("reset@example.com")
        await db_session.commit()

        # Verify token is HASHED in DB (not raw UUID)
        db_result = await db_session.execute(
            select(User).where(User.email == "reset@example.com")
        )
        user = db_result.scalar_one_or_none()
        assert user.password_reset_token is not None
        assert len(user.password_reset_token) == 64  # SHA-256 hex = 64 chars
        # A raw UUID would be 36 chars — this proves hashing
        assert len(user.password_reset_token) > 36

    @pytest.mark.asyncio
    async def test_reset_token_single_use(self, db_session):
        import uuid

        from sqlalchemy import select

        from src.db.models.auth import User
        from src.services.auth_service import AuthService

        service = AuthService(db_session)
        await service.register(email="single@example.com", username="singleuser", password="OldPass123!")
        await db_session.commit()

        # Simulate creating a raw token and storing its hash (as forgot_password does)
        raw_token = str(uuid.uuid4())
        from src.auth.tokens import hash_refresh_token
        db_result = await db_session.execute(select(User).where(User.email == "single@example.com"))
        user = db_result.scalar_one()
        user.password_reset_token = hash_refresh_token(raw_token)
        user.password_reset_expires = datetime.now(UTC) + timedelta(hours=1)
        await db_session.commit()

        # Use the raw token to reset
        await service.reset_password(raw_token, "NewSecurePass456!")
        await db_session.commit()

        # Token should be cleared (single-use)
        db_result = await db_session.execute(select(User).where(User.email == "single@example.com"))
        user = db_result.scalar_one()
        assert user.password_reset_token is None
        assert user.password_reset_expires is None

        # Second attempt with same raw token should fail
        with pytest.raises(ValueError, match="Invalid or expired"):
            await service.reset_password(raw_token, "AnotherPass789!")

    @pytest.mark.asyncio
    async def test_reset_token_expires(self, db_session):
        import uuid

        from sqlalchemy import select

        from src.db.models.auth import User
        from src.services.auth_service import AuthService

        service = AuthService(db_session)
        await service.register(email="expire@example.com", username="expireuser", password="OldPass123!")
        await db_session.commit()

        raw_token = str(uuid.uuid4())
        from src.auth.tokens import hash_refresh_token
        db_result = await db_session.execute(select(User).where(User.email == "expire@example.com"))
        user = db_result.scalar_one()
        user.password_reset_token = hash_refresh_token(raw_token)
        user.password_reset_expires = datetime.now(UTC) - timedelta(hours=2)  # Expired
        await db_session.commit()

        with pytest.raises(ValueError, match="expired"):
            await service.reset_password(raw_token, "NewPass456!")


# ═══════════════════════════════════════════════════════════════════════════════
# 5. Email Verification
# ═══════════════════════════════════════════════════════════════════════════════

class TestEmailVerification:
    @pytest.mark.asyncio
    async def test_verify_email(self, db_session):
        from sqlalchemy import select

        from src.db.models.auth import User
        from src.services.auth_service import AuthService

        service = AuthService(db_session)
        await service.register(email="verify@example.com", username="verifyuser", password="MyPass123!")
        await db_session.commit()

        # Get the verification token from DB
        db_result = await db_session.execute(select(User).where(User.email == "verify@example.com"))
        user = db_result.scalar_one()
        assert user.email_verified is False
        token = user.email_verify_token

        # Verify
        success = await service.verify_email(token)
        await db_session.commit()
        assert success is True

        # Check email is now verified and token consumed
        db_result = await db_session.execute(select(User).where(User.email == "verify@example.com"))
        user = db_result.scalar_one()
        assert user.email_verified is True
        assert user.email_verify_token is None  # Single-use

    @pytest.mark.asyncio
    async def test_verify_email_invalid_token(self, db_session):
        from src.services.auth_service import AuthService
        service = AuthService(db_session)
        success = await service.verify_email("invalid-token-xyz")
        assert success is False


# ═══════════════════════════════════════════════════════════════════════════════
# 6. RBAC Enforcement — 403 Forbidden
# ═══════════════════════════════════════════════════════════════════════════════

class TestRBACEnforcement:
    def test_user_role_missing_sync_run(self):
        from src.auth.dependencies import PERMISSIONS
        assert "sync.run" not in PERMISSIONS["user"]

    def test_moderator_has_sync_run(self):
        from src.auth.dependencies import PERMISSIONS
        assert "sync.run" in PERMISSIONS["moderator"]

    def test_admin_has_all(self):
        from src.auth.dependencies import PERMISSIONS
        for perm in PERMISSIONS["moderator"]:
            assert perm in PERMISSIONS["admin"]
        assert "providers.manage" in PERMISSIONS["admin"]
        assert "scheduler.manage" in PERMISSIONS["admin"]

    @pytest.mark.asyncio
    async def test_require_permission_blocks_unauthorized(self, db_session):
        from fastapi import HTTPException

        from src.auth.dependencies import require_permission
        from src.auth.jwt import TokenPayload

        user = TokenPayload(sub="u1", email="user@example.com", role="user", permissions=["metrics.read"])

        # User should not have sync.run
        checker = require_permission("sync.run")
        with pytest.raises(HTTPException) as exc:
            await checker(user)
        assert exc.value.status_code == 403

    @pytest.mark.asyncio
    async def test_require_permission_allows_authorized(self, db_session):
        from src.auth.dependencies import require_permission
        from src.auth.jwt import TokenPayload

        admin = TokenPayload(sub="a1", email="admin@example.com", role="admin",
                            permissions=["sync.run", "sync.cancel", "scheduler.manage",
                                         "users.manage", "providers.manage", "metrics.read"])

        checker = require_permission("sync.run")
        result = await checker(admin)
        assert result.role == "admin"


# ═══════════════════════════════════════════════════════════════════════════════
# 7. Session Management
# ═══════════════════════════════════════════════════════════════════════════════

class TestSessionManagement:
    @pytest.mark.asyncio
    async def test_logout_all_revokes_everything(self, db_session):
        from sqlalchemy import select

        from src.db.models.auth import UserSession
        from src.services.auth_service import AuthService

        service = AuthService(db_session)
        result = await service.register(
            email="logoutall@example.com", username="logoutall",
            password="MySecurePass123!",
        )
        await db_session.commit()
        user_id = result["user"]["id"]

        # Create 2 more sessions (simulating multiple devices)
        from src.auth.jwt import create_refresh_token
        from src.auth.tokens import create_session
        await create_session(db_session, user_id, create_refresh_token(user_id), {"device": "iPad"})
        await create_session(db_session, user_id, create_refresh_token(user_id), {"device": "Android"})
        await db_session.commit()

        # All 3 sessions active
        active = await db_session.execute(
            select(UserSession).where(UserSession.user_id == user_id, UserSession.revoked == False)
        )
        assert len(active.scalars().all()) == 3

        # Logout all
        count = await service.logout_all(user_id)
        await db_session.commit()
        assert count == 3

        # All revoked
        active = await db_session.execute(
            select(UserSession).where(UserSession.user_id == user_id, UserSession.revoked == False)
        )
        assert len(active.scalars().all()) == 0


# ═══════════════════════════════════════════════════════════════════════════════
# 8. JWT Claims — permissions embedded
# ═══════════════════════════════════════════════════════════════════════════════

class TestJWTClaims:
    def test_access_token_contains_permissions(self):
        from src.auth.jwt import create_access_token, verify_access_token

        token = create_access_token("user-1", "x@x.com", role="moderator")
        payload = verify_access_token(token)
        assert hasattr(payload, "permissions")
        assert "sync.run" in payload.permissions
        assert "users.manage" in payload.permissions
        assert "providers.manage" not in payload.permissions  # Admin only

    def test_user_token_has_only_user_perms(self):
        from src.auth.jwt import create_access_token, verify_access_token

        token = create_access_token("user-1", "x@x.com", role="user")
        payload = verify_access_token(token)
        assert payload.permissions == ["metrics.read"]


# ═══════════════════════════════════════════════════════════════════════════════
# 9. Duplicate prevention — favorites, watchlist
# ═══════════════════════════════════════════════════════════════════════════════

class TestDuplicatePrevention:
    def test_favorite_fighter_unique_constraint_declared(self):
        from sqlalchemy import UniqueConstraint

        from src.db.models.auth import FighterFavorite
        constraints = [
            c for c in FighterFavorite.__table_args__
            if isinstance(c, UniqueConstraint)
        ]
        assert len(constraints) >= 1
        # Should have (user_id, fighter_id) unique

    def test_watchlist_unique_constraint_declared(self):
        from sqlalchemy import UniqueConstraint

        from src.db.models.auth import WatchlistEvent
        constraints = [
            c for c in WatchlistEvent.__table_args__
            if isinstance(c, UniqueConstraint)
        ]
        assert len(constraints) >= 1
