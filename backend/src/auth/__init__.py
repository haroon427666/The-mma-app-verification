"""Auth package — JWT, password hashing, OAuth, dependencies."""

from src.auth.authorization import (
    PERMISSIONS,
    ROLE_HIERARCHY,
    has_permission,
    require_admin,
    require_premium,
    require_resource_owner,
    role_is_at_least,
)
from src.auth.dependencies import (
    get_current_user,
    get_optional_user,
    get_permissions_for_role,
    require_permission,
    require_role,
)
from src.auth.jwt import (
    TokenPair,
    TokenPayload,
    create_access_token,
    create_refresh_token,
    create_token_pair,
    decode_token,
    hash_refresh_token,
    verify_access_token,
    verify_refresh_token,
)
from src.auth.password import check_password_strength, hash_password, verify_password
from src.auth.tokens import (
    block_access_token,
    create_session,
    is_jti_blocked,
    revoke_all_sessions,
    revoke_session,
    rotate_refresh_token,
)

__all__ = [
    "PERMISSIONS",
    "ROLE_HIERARCHY",
    "TokenPair",
    "TokenPayload",
    "block_access_token",
    "check_password_strength",
    "create_access_token",
    "create_refresh_token",
    "create_session",
    "create_token_pair",
    "decode_token",
    "get_current_user",
    "get_optional_user",
    "get_permissions_for_role",
    "has_permission",
    "hash_password",
    "hash_refresh_token",
    "is_jti_blocked",
    "require_admin",
    "require_permission",
    "require_premium",
    "require_resource_owner",
    "require_role",
    "revoke_all_sessions",
    "revoke_session",
    "role_is_at_least",
    "rotate_refresh_token",
    "verify_access_token",
    "verify_password",
    "verify_refresh_token",
]
