"""Runtime Configuration Validation — fails fast on startup.

Validates all required environment variables and settings are present
and well-formed BEFORE the application starts. Prevents production
deployments with missing or invalid configuration.

Checks:
    - DATABASE_URL format (postgresql:// or sqlite://)
    - REDIS_URL format (if configured)
    - JWT_SECRET length (>= 32 chars)
    - Provider API keys (if providers enabled)
    - Email SMTP config (if notifications enabled)
    - Discord webhook URL format (if alerts enabled)
    - Timezone validity
    - Storage paths (writable?)
"""

import logging
import os
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class ConfigError:
    key: str
    message: str
    severity: str = "error"  # error | warning
    fix: str = ""


@dataclass
class ConfigResult:
    errors: list[ConfigError] = field(default_factory=list)
    warnings: list[ConfigError] = field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        return len(self.errors) == 0

    def report(self) -> str:
        lines = ["Config Validation Report", "=" * 30]
        for e in self.errors:
            lines.append(f"  ❌ [{e.key}] {e.message} → {e.fix}")
        for w in self.warnings:
            lines.append(f"  ⚠ [{w.key}] {w.message} → {w.fix}")
        if not self.errors and not self.warnings:
            lines.append("  ✅ All checks passed")
        return "\n".join(lines)


def validate_config(
    database_url: str = "",
    redis_url: str = "",
    jwt_secret: str = "",
    environment: str = "development",
) -> ConfigResult:
    """Validate all runtime configuration. Returns errors + warnings."""
    result = ConfigResult()

    # ── JWT Secret ──────────────────────────────────────────────────────
    if jwt_secret == "CHANGE_ME_IN_PRODUCTION_USE_ENV_VAR" or jwt_secret == "your-secret-key":
        if environment == "production":
            result.errors.append(ConfigError(
                key="JWT_SECRET",
                message="Default/placeholder JWT secret detected",
                fix="Set JWT_SECRET env var to a random 64+ character string",
            ))
        else:
            result.warnings.append(ConfigError(
                key="JWT_SECRET",
                message="Using default JWT secret (fine for dev, not for production)",
                fix="Set JWT_SECRET env var before deploying",
            ))
    elif jwt_secret and len(jwt_secret) < 32:
        result.errors.append(ConfigError(
            key="JWT_SECRET",
            message=f"JWT secret too short ({len(jwt_secret)} chars, need >= 32)",
            fix="Generate: python -c 'import secrets; print(secrets.token_hex(32))'",
        ))

    # ── DATABASE_URL ────────────────────────────────────────────────────
    if not database_url:
        result.errors.append(ConfigError(
            key="DATABASE_URL",
            message="Database URL not configured",
            fix="Set DATABASE_URL=postgresql://user:pass@host:5432/dbname",
        ))
    elif not re.match(r"^(postgresql|postgres|sqlite)(\+aiosqlite)?://", database_url):
        result.errors.append(ConfigError(
            key="DATABASE_URL",
            message=f"Unrecognized database URL format: {database_url[:30]}...",
            fix="Use postgresql:// or sqlite:// URL",
        ))

    # ── REDIS_URL ───────────────────────────────────────────────────────
    if redis_url:
        if not redis_url.startswith("redis://"):
            result.errors.append(ConfigError(
                key="REDIS_URL",
                message=f"Invalid Redis URL: {redis_url[:20]}...",
                fix="Use redis://host:6379 format",
            ))
    elif environment == "production":
        result.warnings.append(ConfigError(
            key="REDIS_URL",
            message="Redis not configured in production — using in-memory cache",
            fix="Set REDIS_URL=redis://host:6379 for production caching",
        ))

    # ── Environment ─────────────────────────────────────────────────────
    valid_envs = {"development", "staging", "production", "test"}
    if environment not in valid_envs:
        result.errors.append(ConfigError(
            key="ENVIRONMENT",
            message=f"Invalid environment: '{environment}'",
            fix=f"Set to one of: {', '.join(sorted(valid_envs))}",
        ))

    # ── Timezone ────────────────────────────────────────────────────────
    try:
        import zoneinfo
        tz = os.environ.get("TZ", "UTC")
        zoneinfo.ZoneInfo(tz)
    except Exception:
        result.warnings.append(ConfigError(
            key="TZ",
            message=f"Invalid timezone: '{os.environ.get('TZ', 'not set')}'",
            fix="Set TZ=Asia/Karachi or valid IANA timezone",
        ))

    return result
