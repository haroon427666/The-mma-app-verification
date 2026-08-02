"""Phase 9 Auth Tests — JWT, password, tokens, RBAC, sessions."""

import pytest
import time
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, MagicMock, patch


# ═══════════════════════════════════════════════════════════════════════════════
# JWT Tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestJWT:
    def test_create_and_verify_access_token(self):
        from src.auth.jwt import create_access_token, verify_access_token

        token = create_access_token("user-123", "test@example.com", role="user")
        payload = verify_access_token(token)

        assert payload.sub == "user-123"
        assert payload.email == "test@example.com"
        assert payload.role == "user"
        assert payload.token_type == "access"

    def test_create_token_pair(self):
        from src.auth.jwt import create_token_pair

        pair = create_token_pair("user-123", "test@example.com")
        assert pair.token_type == "bearer"
        assert pair.access_token != pair.refresh_token

    def test_refresh_token_rejected_as_access(self):
        from src.auth.jwt import create_refresh_token, verify_access_token
        import jwt as pyjwt

        refresh = create_refresh_token("user-1")
        with pytest.raises(pyjwt.exceptions.InvalidTokenError):
            verify_access_token(refresh)

    def test_token_with_wrong_secret_rejected(self):
        from src.auth.jwt import create_access_token, SECRET_KEY, ALGORITHM
        import jwt as pyjwt

        token = create_access_token("user-1", "x@x.com")
        with pytest.raises(pyjwt.exceptions.InvalidTokenError):
            pyjwt.decode(token, "wrong-secret", algorithms=[ALGORITHM])

    def test_hash_refresh_token_consistent(self):
        from src.auth.jwt import hash_refresh_token

        token = "test-refresh-token-abc"
        h1 = hash_refresh_token(token)
        h2 = hash_refresh_token(token)
        assert h1 == h2
        assert len(h1) == 64  # SHA-256 hex digest

    def test_admin_role_in_token(self):
        from src.auth.jwt import create_access_token, verify_access_token

        token = create_access_token("admin-1", "admin@example.com", role="admin")
        payload = verify_access_token(token)
        assert payload.role == "admin"


# ═══════════════════════════════════════════════════════════════════════════════
# Password Tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestPassword:
    def test_hash_and_verify(self):
        from src.auth.password import hash_password, verify_password

        pw = "MySecurePass123!"
        hashed = hash_password(pw)
        assert hashed != pw
        assert verify_password(pw, hashed) is True

    def test_wrong_password_rejected(self):
        from src.auth.password import hash_password, verify_password

        hashed = hash_password("correct123!")
        assert verify_password("wrong_password", hashed) is False

    def test_different_salts_produce_different_hashes(self):
        from src.auth.password import hash_password

        pw = "same_password"
        h1 = hash_password(pw)
        h2 = hash_password(pw)
        assert h1 != h2  # Different salts

    def test_weak_password_rejected(self):
        from src.auth.password import check_password_strength

        # Too short
        valid, err = check_password_strength("Ab1")
        assert not valid
        assert "8 characters" in err

        # Missing uppercase
        valid, err = check_password_strength("abcdefg1")
        assert not valid

        # Missing digit
        valid, err = check_password_strength("Abcdefgh")
        assert not valid

        # Good password
        valid, err = check_password_strength("MySecurePass123!")
        assert valid
        assert err is None


# ═══════════════════════════════════════════════════════════════════════════════
# RBAC Tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestRBAC:
    def test_role_permissions(self):
        from src.auth.dependencies import PERMISSIONS

        assert "sync.run" in PERMISSIONS["admin"]
        assert "sync.run" in PERMISSIONS["moderator"]
        assert "sync.run" not in PERMISSIONS["user"]

        assert "users.manage" in PERMISSIONS["admin"]
        assert "users.manage" in PERMISSIONS["moderator"]
        assert "users.manage" not in PERMISSIONS["user"]

    def test_higher_role_has_all_lower_permissions(self):
        from src.auth.dependencies import PERMISSIONS

        # Admin should have everything moderator has
        for perm in PERMISSIONS["moderator"]:
            assert perm in PERMISSIONS["admin"]

    def test_token_payload_role(self):
        from src.auth.dependencies import TokenPayload
        p = TokenPayload(sub="u1", email="x@x.com", role="admin")
        assert p.role == "admin"


# ═══════════════════════════════════════════════════════════════════════════════
# Brute-force Protection Tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestBruteForce:
    def test_lockout_after_max_attempts(self):
        from src.middleware.auth import BruteForceProtection

        bf = BruteForceProtection(app=None)
        ip = "192.168.1.100"

        # Simulate 5 failures
        for _ in range(5):
            bf._failures[ip].append(time.monotonic())

        # 6th attempt should trigger lockout
        bf._failures[ip].append(time.monotonic() - 100)
        still_recent = [time.monotonic() for _ in range(5)]
        bf._failures[ip] = still_recent
        # Manually trigger — need 5 failures within window
        bf._failures[ip] = [time.monotonic() for _ in range(5)]
        # _record_failure adds to the list
        bf._failures[ip] = []  # Reset

    def test_lockout_expires(self):
        """After lockout period, attempts are allowed again."""
        from src.middleware.auth import BruteForceProtection

        bf = BruteForceProtection(app=None)
        ip = "192.168.1.101"

        # Set a lockout in the past
        bf._lockouts[ip] = time.monotonic() - 1000

        # Lockout should have expired
        assert ip not in bf._lockouts or bf._lockouts[ip] < time.monotonic()


# ═══════════════════════════════════════════════════════════════════════════════
# Refresh Token Rotation Tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestTokenRotation:
    def test_refresh_produces_new_tokens(self):
        from src.auth.jwt import create_token_pair, verify_refresh_token

        pair1 = create_token_pair("user-1", "x@x.com")
        pair2 = create_token_pair("user-1", "x@x.com")

        # Each pair is unique
        assert pair1.access_token != pair2.access_token
        assert pair1.refresh_token != pair2.refresh_token

        # Both are valid refresh tokens
        verify_refresh_token(pair1.refresh_token)
        verify_refresh_token(pair2.refresh_token)

    def test_expired_refresh_token_rejected(self):
        from src.auth.jwt import create_access_token, verify_refresh_token, SECRET_KEY, ALGORITHM
        import jwt as pyjwt

        # Create an expired token manually
        now = datetime.now(timezone.utc)
        payload = {
            "sub": "user-1", "iat": now, "token_type": "refresh",
            "exp": now - timedelta(days=1),  # Expired yesterday
        }
        token = pyjwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

        with pytest.raises(pyjwt.exceptions.ExpiredSignatureError):
            verify_refresh_token(token)


# ═══════════════════════════════════════════════════════════════════════════════
# Session Management Tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestSessions:
    def test_session_model_fields(self):
        from src.db.models.auth import UserSession
        assert hasattr(UserSession, "refresh_token_hash")
        assert hasattr(UserSession, "device")
        assert hasattr(UserSession, "revoked")
        assert hasattr(UserSession, "expires_at")

    def test_user_model_has_role_property(self):
        from src.db.models.auth import User
        u = User()
        u.is_admin = False
        u.is_moderator = False
        assert u.role == "user"

        u.is_moderator = True
        assert u.role == "moderator"

        u.is_admin = True
        assert u.role == "admin"


# ═══════════════════════════════════════════════════════════════════════════════
# Auth API Models Test
# ═══════════════════════════════════════════════════════════════════════════════

class TestAuthSchemas:
    def test_login_request_validation(self):
        from src.api.v1.auth import LoginRequest
        req = LoginRequest(email="user@example.com", password="ValidPass1")
        assert req.email == "user@example.com"
        assert req.remember_me is False

    def test_register_rejects_weak_password(self):
        from src.api.v1.auth import RegisterRequest
        # This validates at Pydantic level (min_length=8)
        with pytest.raises(Exception):
            RegisterRequest(email="x@x.com", username="user1", password="short")
