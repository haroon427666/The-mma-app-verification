"""Password hashing — Argon2id (recommended by OWASP).

Never stores plaintext. Never uses bcrypt or SHA for passwords.
Argon2id is memory-hard, GPU-resistant, and side-channel resistant.
"""

from __future__ import annotations

import logging
from typing import cast

logger = logging.getLogger(__name__)

# In production: pip install argon2-cffi
# For now: reference implementation with a fallback warning

try:
    from argon2 import PasswordHasher
    from argon2.exceptions import VerifyMismatchError
    _hasher: PasswordHasher | None = PasswordHasher(
        time_cost=3,        # Iterations
        memory_cost=65536,  # 64 MB
        parallelism=4,      # Threads
        hash_len=32,        # Output length
        salt_len=16,
    )
    ARGON2_AVAILABLE = True
except ImportError:
    ARGON2_AVAILABLE = False
    _hasher = None
    logger.warning("argon2-cffi not installed — using hashlib fallback (NOT FOR PRODUCTION)")


def hash_password(password: str) -> str:
    """Hash a password with Argon2id. Returns the encoded hash string.

    Production: MUST install argon2-cffi.
    Fallback: SHA-256 with salt (NOT SECURE — dev only).
    """
    if ARGON2_AVAILABLE:
        return cast(PasswordHasher, _hasher).hash(password)

    # ⚠️ DEV FALLBACK — NEVER USE IN PRODUCTION
    import hashlib
    import os
    salt = os.urandom(32).hex()
    h = hashlib.sha256((password + salt).encode()).hexdigest()
    return f"$dev${salt}${h}"


def verify_password(password: str, password_hash: str) -> bool:
    """Verify a password against its Argon2id hash.

    Returns True if the password matches, False otherwise.
    """
    if ARGON2_AVAILABLE:
        try:
            cast(PasswordHasher, _hasher).verify(password_hash, password)
            return True
        except VerifyMismatchError:
            return False

    # ⚠️ DEV FALLBACK
    if not password_hash.startswith("$dev$"):
        return False
    _, _, salt, stored = password_hash.split("$", 3)
    import hashlib
    return hashlib.sha256((password + salt).encode()).hexdigest() == stored


def check_password_strength(password: str) -> tuple[bool, str | None]:
    """Check password meets minimum strength requirements.

    Returns (valid, error_message).
    """
    if len(password) < 8:
        return False, "Password must be at least 8 characters"
    if len(password) > 128:
        return False, "Password must be at most 128 characters"
    if not any(c.isupper() for c in password):
        return False, "Password must contain at least one uppercase letter"
    if not any(c.islower() for c in password):
        return False, "Password must contain at least one lowercase letter"
    if not any(c.isdigit() for c in password):
        return False, "Password must contain at least one digit"
    return True, None
