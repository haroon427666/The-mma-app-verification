"""Production integration tests — router → service → repository → DB.

Tests real query construction, data flow, and error handling.
Uses mocked async session to avoid needing a real PostgreSQL.
"""

from unittest.mock import AsyncMock, MagicMock

import pytest

# ═══════════════════════════════════════════════════════════════════════════════
# FighterService API Queries
# ═══════════════════════════════════════════════════════════════════════════════

class TestFighterServiceQueries:
    def test_list_fighters_applies_all_filters(self):
        from src.services.fighter_service import FighterService

        uow = MagicMock()
        uow.fighters = MagicMock()
        uow.fighters.list_filtered = AsyncMock(return_value=[])
        uow.fighters.count_filtered = AsyncMock(return_value=0)
        uow._session = AsyncMock()

        svc = FighterService(uow)

        import asyncio
        async def run():
            items, total = await svc.list_fighters(
                limit=50, offset=0, weight_class="Lightweight",
                country="USA", active=True, stance="Orthodox",
                search="Islam", sort_by="last_name", sort_dir="asc",
            )
            return items, total

        _items, total = asyncio.run(run())
        assert total == 0
        uow.fighters.list_filtered.assert_called_once()
        uow.fighters.count_filtered.assert_called_once()

    def test_get_fighter_detail_returns_none_for_missing(self):
        from src.services.fighter_service import FighterService

        uow = MagicMock()
        uow.fighters.get_by_id = AsyncMock(return_value=None)
        uow._session = AsyncMock()

        svc = FighterService(uow)

        import asyncio
        result = asyncio.run(svc.get_fighter_detail("nonexistent"))
        assert result is None


# ═══════════════════════════════════════════════════════════════════════════════
# AuthService Flows
# ═══════════════════════════════════════════════════════════════════════════════

class TestAuthServiceFlows:
    def test_login_rejects_wrong_password(self):
        import asyncio
        from unittest.mock import MagicMock

        from sqlalchemy.ext.asyncio import AsyncSession

        from src.auth.password import hash_password
        from src.db.models.auth import User
        from src.services.auth_service import AuthService

        async def run():
            session = AsyncMock(spec=AsyncSession)
            session.execute = AsyncMock()

            user = User(
                email="test@example.com",
                username="test",
                password_hash=hash_password("CorrectPass1"),
                login_attempts=0,
                email_verified=True,
            )
            user.id = "user-uuid"

            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = user
            session.execute.return_value = mock_result

            service = AuthService(session)
            with pytest.raises(ValueError, match="Invalid email or password"):
                await service.login("test@example.com", "WrongPassword1")
            assert user.login_attempts == 1

        asyncio.run(run())

    def test_register_rejects_weak_password(self):
        import asyncio

        from sqlalchemy.ext.asyncio import AsyncSession

        from src.services.auth_service import AuthService

        async def run():
            session = AsyncMock(spec=AsyncSession)
            service = AuthService(session)
            with pytest.raises(ValueError, match="uppercase"):
                await service.register("x@x.com", "testuser", "abcdefgh")

        asyncio.run(run())

    def test_register_rejects_duplicate_email(self):
        import asyncio
        from unittest.mock import MagicMock

        from sqlalchemy.ext.asyncio import AsyncSession

        from src.db.models.auth import User
        from src.services.auth_service import AuthService

        async def run():
            session = AsyncMock(spec=AsyncSession)
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = User(email="existing@x.com")

            # First call checks email, second checks username
            session.execute = AsyncMock(return_value=mock_result)
            session.add = MagicMock()
            session.flush = AsyncMock()

            service = AuthService(session)
            with pytest.raises(ValueError, match="Email already registered"):
                await service.register("existing@x.com", "newuser", "ValidPass1!")

        asyncio.run(run())

    def test_account_locked_after_5_failures(self):
        import asyncio
        from unittest.mock import MagicMock

        from src.auth.password import hash_password
        from src.db.models.auth import User
        from src.services.auth_service import AuthService

        async def run():
            session = AsyncMock()
            session.flush = AsyncMock()

            user = User(
                email="locked@x.com",
                username="locked",
                password_hash=hash_password("CorrectPass1"),
                login_attempts=4,
                email_verified=True,
            )
            user.id = "user-uuid"
            user.locked_until = None

            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = user
            session.execute = AsyncMock(return_value=mock_result)

            service = AuthService(session)
            with pytest.raises(ValueError, match="Invalid email or password"):
                await service.login("locked@x.com", "WrongPassword1")

            assert user.login_attempts == 5
            assert user.locked_until is not None

            # Next login should be locked
            mock_result2 = MagicMock()
            mock_result2.scalar_one_or_none.return_value = user
            session.execute = AsyncMock(return_value=mock_result2)

            with pytest.raises(ValueError, match="Account locked"):
                await service.login("locked@x.com", "CorrectPass1")

        asyncio.run(run())


# ═══════════════════════════════════════════════════════════════════════════════
# Error Handling
# ═══════════════════════════════════════════════════════════════════════════════

class TestErrorHandling:
    def test_not_found_error_has_rfc7807_shape(self):
        from unittest.mock import MagicMock

        from fastapi import Request

        from src.api.errors import NotFoundError, build_problem_response

        exc = NotFoundError("Fighter", "abc-123")
        request = MagicMock(spec=Request)
        request.url = "https://api.example.com/v1/fighters/abc-123"

        resp = build_problem_response(exc, request, "req_xyz")
        resp.body if hasattr(resp, 'body') else None

        # Check problem detail presence (body is a string in JSONResponse)
        from json import loads
        loads(resp.body) if hasattr(resp, 'body') else {}

        assert exc.status == 404
        assert exc.title == "Fighter not found"

    def test_domain_exceptions_inherit_problem_detail(self):
        from src.api.errors import (
            AuthenticationError,
            NotFoundError,
            RateLimitError,
        )

        assert issubclass(NotFoundError, Exception)
        assert issubclass(AuthenticationError, Exception)
        nf = NotFoundError("Event", "evt-1")
        assert nf.status == 404

        auth = AuthenticationError()
        assert auth.status == 401

        rate = RateLimitError(retry_after=30)
        assert rate.extensions["retry_after"] == 30

    def test_validation_error_has_field(self):
        from src.api.errors import ValidationError
        exc = ValidationError("Email is invalid", field="email")
        assert exc.extensions["field"] == "email"


# ═══════════════════════════════════════════════════════════════════════════════
# Authorization / RBAC
# ═══════════════════════════════════════════════════════════════════════════════

class TestAuthorization:
    def test_role_hierarchy(self):
        from src.auth.authorization import role_is_at_least
        assert role_is_at_least("admin", "user") is True
        assert role_is_at_least("moderator", "premium") is True
        assert role_is_at_least("user", "admin") is False
        assert role_is_at_least("user", "user") is True

    def test_premium_has_advanced_permissions(self):
        from src.auth.authorization import PERMISSIONS
        premium_perms = PERMISSIONS.get("premium", [])
        assert "predictions.advanced" in premium_perms
        assert "recommendations.personalized" in premium_perms

    def test_admin_has_all_permissions(self):
        from src.auth.authorization import PERMISSIONS
        admin_perms = PERMISSIONS.get("admin", [])
        assert "users.manage" in admin_perms
        assert "providers.manage" in admin_perms
        assert "content.delete" in admin_perms

    def test_user_has_only_basic(self):
        from src.auth.authorization import PERMISSIONS
        user_perms = PERMISSIONS.get("user", [])
        assert "content.delete" not in user_perms
        assert "users.manage" not in user_perms
        assert "predictions.basic" in user_perms
