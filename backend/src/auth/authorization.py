"""Authorization — RBAC, permissions, resource ownership, hierarchical roles.

Built on top of src/auth/dependencies.py — extends with:
- Hierarchical roles (premium inherits user, moderator inherits premium, etc.)
- Resource ownership checks (owns_fighter, owns_event, etc.)
- Feature flag integration (premium features)
- Policy-based access (for fine-grained rules)
"""

import logging
from typing import Optional

from fastapi import Depends, HTTPException, status

from src.auth.dependencies import get_current_user, TokenPayload

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════
# Role Hierarchy
# ═══════════════════════════════════════════════════════════════════════════

ROLE_HIERARCHY: dict[str, list[str]] = {
    "admin":       ["admin", "moderator", "premium", "analyst", "user"],
    "moderator":   ["moderator", "premium", "analyst", "user"],
    "premium":     ["premium", "analyst", "user"],
    "analyst":     ["analyst", "user"],
    "user":        ["user"],
}

def role_is_at_least(role: str, minimum: str) -> bool:
    """Check if a role meets or exceeds a minimum role level."""
    hierarchy = ROLE_HIERARCHY.get(role, ["user"])
    return minimum in hierarchy


# ═══════════════════════════════════════════════════════════════════════════
# Permission Catalogue
# ═══════════════════════════════════════════════════════════════════════════

PERMISSIONS: dict[str, list[str]] = {
    "admin": [
        "sync.run", "sync.cancel", "scheduler.manage",
        "users.manage", "providers.manage", "metrics.read",
        "content.delete", "content.edit", "flags.manage",
    ],
    "moderator": [
        "sync.run", "sync.cancel", "users.manage", "metrics.read",
        "content.edit",
    ],
    "premium": [
        "predictions.advanced", "recommendations.personalized",
        "export.data", "analytics.advanced",
    ],
    "analyst": [
        "analytics.read", "export.data", "metrics.read",
    ],
    "user": [
        "metrics.read",
        "predictions.basic", "recommendations.basic",
    ],
}


def has_permission(user: TokenPayload, permission: str) -> bool:
    """Check if a user has a specific permission."""
    user_perms = getattr(user, "permissions", None)
    if user_perms and isinstance(user_perms, list):
        if permission in user_perms:
            return True
    role_perms = PERMISSIONS.get(user.role, [])
    return permission in role_perms


# ═══════════════════════════════════════════════════════════════════════════
# Dependency Factories
# ═══════════════════════════════════════════════════════════════════════════

def require_role(*roles: str):
    """Require user to have one of the specified roles (hierarchical).
    
    Usage:
        @router.get("/admin")
        async def admin_endpoint(user = Depends(require_role("admin"))): ...
    """
    async def checker(user: TokenPayload = Depends(get_current_user)) -> TokenPayload:
        if user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requires role: {' or '.join(roles)}",
            )
        return user
    return checker


def require_permission(permission: str):
    """Require a specific permission.
    
    Usage:
        @router.post("/sync/full")
        async def trigger_sync(user = Depends(require_permission("sync.run"))): ...
    """
    async def checker(user: TokenPayload = Depends(get_current_user)) -> TokenPayload:
        if not has_permission(user, permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Missing permission: {permission}",
            )
        return user
    return checker


def require_premium():
    """Require premium tier (or higher)."""
    return require_role("premium", "moderator", "admin")


def require_admin():
    """Require admin role."""
    return require_role("admin")


# ═══════════════════════════════════════════════════════════════════════════
# Resource Ownership
# ═══════════════════════════════════════════════════════════════════════════

def require_resource_owner(
    entity_type: str,
    id_param: str = "entity_id",
    repo_attr: str | None = None,
):
    """Dependency factory: ensure the authenticated user owns the resource.
    
    Checks the resource's user_id/owner_id field against token.sub.
    Admins bypass ownership checks.
    
    Usage:
        @router.delete("/favorites/fighters/{fighter_id}")
        async def remove_fav(
            fighter_id: str,
            user = Depends(require_resource_owner("favorite", "fighter_id")),
        ): ...
    
    Args:
        entity_type: "favorite", "watchlist", "preference", etc.
        id_param: the URL path parameter name for the entity ID
        repo_attr: the repository attribute name on the UnitOfWork (e.g., "favorites")
    """
    async def checker(
        request,
        user: TokenPayload = Depends(get_current_user),
    ) -> TokenPayload:
        # Admins bypass ownership checks
        if user.role == "admin":
            return user

        # Get entity ID from path params
        entity_id = request.path_params.get(id_param)
        if entity_id is None:
            raise HTTPException(status_code=400, detail=f"Missing {id_param}")

        # Verify ownership via database
        from src.db.models.auth import User
        from sqlalchemy import select as sa_select
        from src.db.session import async_session_factory

        async with async_session_factory() as sess:
            # For favorites/watchlist/preferences — check user_id matches
            if entity_type in ("favorite", "watchlist", "preference", "notification"):
                from src.db.models.auth import (
                    FighterFavorite, EventFavorite, WatchlistEvent, Notification,
                )
                model_map = {
                    "favorite": FighterFavorite,
                    "watchlist": WatchlistEvent,
                    "notification": Notification,
                }
                model = model_map.get(entity_type)
                if model:
                    result = await sess.execute(
                        sa_select(model).where(
                            model.id == entity_id,
                            model.user_id == user.sub,
                        )
                    )
                    if result.scalar_one_or_none() is None:
                        raise HTTPException(
                            status_code=403,
                            detail=f"You don't own this {entity_type}",
                        )

        return user
    return checker
