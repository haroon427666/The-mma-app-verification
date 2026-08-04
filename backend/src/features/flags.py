"""Feature Flags — runtime toggle for experimental features.

Flags control behavior without redeploying.
Backed by environment variables for now, Redis in production.

Usage:
    from src.features.flags import is_enabled
    if is_enabled("live_mode"):
        ...
"""

import os
from typing import Any

# ── Flag Definitions ──────────────────────────────────────────────────────

FLAGS: dict[str, dict[str, Any]] = {
    "live_mode": {
        "default": True,
        "description": "Enable 30-second polling during live events",
        "env_var": "FEATURE_LIVE_MODE",
    },
    "recommendations": {
        "default": False,
        "description": "AI-powered fight recommendations (Phase 11)",
        "env_var": "FEATURE_RECOMMENDATIONS",
    },
    "notifications": {
        "default": True,
        "description": "Push + in-app notifications",
        "env_var": "FEATURE_NOTIFICATIONS",
    },
    "experimental_search": {
        "default": False,
        "description": "Full-text search with PostgreSQL tsvector",
        "env_var": "FEATURE_EXPERIMENTAL_SEARCH",
    },
    "provider_octagon": {
        "default": True,
        "description": "Octagon API enrichment for fighter images + style",
        "env_var": "FEATURE_PROVIDER_OCTAGON",
    },
    "provider_tsdb": {
        "default": True,
        "description": "TheSportsDB enrichment for media + bios",
        "env_var": "FEATURE_PROVIDER_TSDB",
    },
    "maintenance_mode": {
        "default": False,
        "description": "Returns 503 for all non-admin requests",
        "env_var": "MAINTENANCE_MODE",
    },
    "rate_limiting": {
        "default": True,
        "description": "Per-client rate limiting",
        "env_var": "FEATURE_RATE_LIMITING",
    },
    "payload_archive": {
        "default": False,
        "description": "Archive raw provider JSON for debugging (adds storage cost)",
        "env_var": "FEATURE_PAYLOAD_ARCHIVE",
    },
    "discord_alerts": {
        "default": False,
        "description": "Send alerts to Discord webhook",
        "env_var": "FEATURE_DISCORD_ALERTS",
    },
}


def is_enabled(flag_name: str) -> bool:
    """Check if a feature flag is enabled. Env override wins over default."""
    flag = FLAGS.get(flag_name)
    if flag is None:
        return False

    env_val = os.environ.get(flag["env_var"])
    if env_val is not None:
        return env_val.lower() in ("1", "true", "yes", "on")

    return bool(flag["default"])


def set_flag(flag_name: str, value: bool) -> None:
    """Runtime override (in-memory only — resets on restart)."""
    if flag_name in FLAGS:
        FLAGS[flag_name]["default"] = value


def list_flags() -> dict[str, dict[str, bool | str]]:
    return {
        name: {"enabled": is_enabled(name), "description": f["description"]}
        for name, f in FLAGS.items()
    }
