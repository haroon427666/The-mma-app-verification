"""Auth Dependencies — FastAPI dependency injection for current user.

Provides:
- get_current_user — resolves JWT → User
- require_role — RBAC gate
- get_optional_user — optional auth (for public endpoints with logged-in bonus)
"""

import logging
from typing import Optional

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from src.auth.jwt import verify_access_token, TokenPayload
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError

logger = logging.getLogger(__name__)

security = HTTPBearer(auto_error=False)


async def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> "User":
    """Require valid JWT access token. Returns User or raises 401."""
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials
    try:
        payload = verify_access_token(token)
    except ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Production: fetch User from database
    # user = await user_repo.get_by_id(payload.sub)
    # if not user or not user.is_active:
    #     raise HTTPException(401, "User not found or inactive")

    return payload  # Returns TokenPayload for now — production returns User


async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> Optional[TokenPayload]:
    """Optional auth — returns None if no token, User if valid token."""
    if credentials is None:
        return None
    try:
        return verify_access_token(credentials.credentials)
    except (ExpiredSignatureError, InvalidTokenError):
        return None


def require_role(*roles: str):
    """Dependency factory: require one of the specified roles.

    Usage:
        @router.get("/admin")
        async def admin_endpoint(user = Depends(require_role("admin"))):
            ...
    """
    async def role_checker(
        user: TokenPayload = Depends(get_current_user),
    ) -> TokenPayload:
        if user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requires role: {' or '.join(roles)}",
            )
        return user
    return role_checker


# Permission-based access
PERMISSIONS = {
    "admin": ["sync.run", "sync.cancel", "scheduler.manage", "users.manage",
              "providers.manage", "metrics.read"],
    "moderator": ["sync.run", "sync.cancel", "users.manage", "metrics.read"],
    "user": ["metrics.read"],
}


def get_permissions_for_role(role: str) -> list[str]:
    """Return the permission list for a given role."""
    return PERMISSIONS.get(role, ["metrics.read"])


def require_permission(permission: str):
    """Dependency factory: require a specific permission.

    Usage:
        @router.post("/sync/full")
        async def trigger_sync(user = Depends(require_permission("sync.run"))):
            ...

    Checks both token-level permissions list (from JWT) and
    role-based permission map (fallback).
    """
    async def permission_checker(
        user: TokenPayload = Depends(get_current_user),
    ) -> TokenPayload:
        # Check permissions from JWT claims first
        user_perms = user.permissions if hasattr(user, 'permissions') and user.permissions else []
        if permission in user_perms:
            return user

        # Fallback: role-based permissions
        role_perms = PERMISSIONS.get(user.role, [])
        if permission in role_perms:
            return user

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Missing permission: {permission}",
        )
    return permission_checker
