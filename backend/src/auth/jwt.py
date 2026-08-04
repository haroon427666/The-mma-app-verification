"""JWT token management — access + refresh tokens, rotation.

Access token: short-lived (15 min), used for API calls
Refresh token: long-lived (7 days), used to get new access tokens
Token rotation: each refresh issues a new refresh token, revokes old
"""

import hashlib
import logging
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta

import jwt
from jwt.exceptions import InvalidTokenError

logger = logging.getLogger(__name__)

# ── Config ─────────────────────────────────────────────────────────────────

def _get_secret() -> str:
    """Get JWT secret from config.

    Strict enforcement applies in production: the app refuses to boot on the
    placeholder secret. In development a local dev-only secret is used so the
    app and test suite work out of the box.
    """
    import warnings

    try:
        from src.config import settings
        secret = settings.jwt_secret
        if secret == "CHANGE_ME_IN_PRODUCTION_USE_ENV_VAR":
            if settings.environment == "production":
                raise ValueError("JWT_SECRET is still the default — set JWT_SECRET env var")
            warnings.warn(
                "JWT_SECRET is the default — set JWT_SECRET env var before deploying",
                stacklevel=2,
            )
            return "dev-only-insecure-secret-for-local-development"
        return secret
    except ImportError:
        warnings.warn("src.config not available — using hardcoded fallback (NOT FOR PRODUCTION)")
        return "CHANGE_ME_IN_PRODUCTION_USE_ENV_VAR"

SECRET_KEY = _get_secret()
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 15
REFRESH_TOKEN_EXPIRE_DAYS = 7

# Sliding expiration: if access token is within this window of expiry, auto-refresh
SLIDING_REFRESH_WINDOW_MINUTES = 2


@dataclass
class TokenPair:
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = ACCESS_TOKEN_EXPIRE_MINUTES * 60


@dataclass
class TokenPayload:
    sub: str          # user_id
    email: str
    role: str
    permissions: list[str] = field(default_factory=list)  # permission strings
    exp: datetime | None = None
    iat: datetime | None = None
    jti: str | None = None  # JWT ID — for revocation
    token_type: str = "access"


# ── Create ──────────────────────────────────────────────────────────────────


def create_access_token(user_id: str, email: str, role: str = "user") -> str:
    now = datetime.now(UTC)
    import uuid

    # Lazy import inside function to break circular dependency with dependencies.py
    from src.auth.dependencies import get_permissions_for_role
    permissions = get_permissions_for_role(role)
    payload = {
        "sub": user_id,
        "email": email,
        "role": role,
        "permissions": permissions,
        "iat": now,
        "exp": now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
        "jti": str(uuid.uuid4()),
        "token_type": "access",
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def create_refresh_token(user_id: str) -> str:
    now = datetime.now(UTC)
    import uuid
    payload = {
        "sub": user_id,
        "iat": now,
        "exp": now + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS),
        "jti": str(uuid.uuid4()),
        "token_type": "refresh",
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def create_token_pair(user_id: str, email: str, role: str = "user") -> TokenPair:
    return TokenPair(
        access_token=create_access_token(user_id, email, role),
        refresh_token=create_refresh_token(user_id),
    )


# ── Verify ─────────────────────────────────────────────────────────────────

def decode_token(token: str) -> TokenPayload:
    """Decode and verify a JWT. Raises on expiry or invalid signature."""
    data = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    return TokenPayload(
        sub=data["sub"],
        email=data.get("email", ""),
        role=data.get("role", "user"),
        permissions=data.get("permissions", []),
        exp=data.get("exp"),
        iat=data.get("iat"),
        jti=data.get("jti"),
        token_type=data.get("token_type", "access"),
    )


def verify_access_token(token: str) -> TokenPayload:
    """Verify an access token. Raises if expired or invalid."""
    payload = decode_token(token)
    if payload.token_type != "access":
        raise InvalidTokenError("Token is not an access token")
    return payload


def verify_refresh_token(token: str) -> TokenPayload:
    """Verify a refresh token. Raises if expired or invalid."""
    payload = decode_token(token)
    if payload.token_type != "refresh":
        raise InvalidTokenError("Token is not a refresh token")
    return payload


# ── Refresh Token Hashing ──────────────────────────────────────────────────

def hash_refresh_token(token: str) -> str:
    """One-way hash for storing refresh tokens in DB."""
    return hashlib.sha256(token.encode()).hexdigest()
