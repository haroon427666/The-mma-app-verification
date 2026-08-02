"""Auth package — JWT, password hashing, OAuth, dependencies."""

from src.auth.jwt import (
    create_access_token, create_refresh_token, create_token_pair,
    verify_access_token, verify_refresh_token, decode_token,
    TokenPair, TokenPayload, hash_refresh_token,
)
from src.auth.password import hash_password, verify_password, check_password_strength
from src.auth.tokens import (
    create_session, rotate_refresh_token, revoke_session, revoke_all_sessions,
    block_access_token, is_jti_blocked, hash_refresh_token as hash_token,
)
from src.auth.dependencies import (
    get_current_user, get_optional_user, require_role, require_permission,
    get_permissions_for_role, PERMISSIONS as DEP_PERMISSIONS,
)
from src.auth.authorization import (
    require_admin, require_premium, require_resource_owner,
    role_is_at_least, has_permission, ROLE_HIERARCHY, PERMISSIONS,
)

__all__ = [
    "create_access_token", "create_refresh_token", "create_token_pair",
    "verify_access_token", "verify_refresh_token", "decode_token",
    "TokenPair", "TokenPayload", "hash_refresh_token",
    "hash_password", "verify_password", "check_password_strength",
    "create_session", "rotate_refresh_token", "revoke_session", "revoke_all_sessions",
    "block_access_token", "is_jti_blocked",
    "get_current_user", "get_optional_user", "require_role", "require_permission",
    "get_permissions_for_role", "PERMISSIONS",
]
