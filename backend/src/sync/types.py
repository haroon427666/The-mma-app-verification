"""
Sync types — strongly-typed enums and version identifiers.

No magic strings anywhere in the sync engine.
"""

from dataclasses import dataclass
from enum import Enum

# ── Entity Types ──────────────────────────────────────────────────────────────


class EntityType(str, Enum):
    """All syncable entity types. Used instead of magic strings everywhere."""

    PROMOTION = "promotion"
    VENUE = "venue"
    WEIGHT_CLASS = "weight_class"
    FIGHTER = "fighter"
    EVENT = "event"
    COMPETITION = "competition"
    BROADCAST = "broadcast"
    RANKING = "ranking"
    STATISTIC = "statistic"


# ── Sync Status ───────────────────────────────────────────────────────────────


class SyncStatus(str, Enum):
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    PARTIAL = "PARTIAL"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class JobStatus(str, Enum):
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"
    CANCELLED = "CANCELLED"


# ── Sync Mode ────────────────────────────────────────────────────────────────


class SyncMode(str, Enum):
    """How a sync job should execute."""

    FULL = "full"
    """Complete sync — fetch everything from the provider."""

    INCREMENTAL = "incremental"
    """Delta sync — only fetch what changed since last sync."""

    RESUME = "resume"
    """Resume from last checkpoint after a crash or cancellation."""

    FORCE = "force"
    """Force a full sync regardless of state (e.g. after schema migration)."""


# ── Provider Capabilities ─────────────────────────────────────────────────────


@dataclass(frozen=True)
class ProviderCapabilities:
    """What a provider can and cannot do.

    The engine uses this to decide sync strategy per provider.
    If a provider doesn't support incremental sync, the engine
    always runs full syncs for that provider.
    """

    provider_slug: str

    # Entity coverage
    supports_fighters: bool = True
    supports_events: bool = True
    supports_rankings: bool = True
    supports_statistics: bool = True
    supports_broadcasts: bool = True

    # Sync capabilities
    supports_incremental: bool = False
    """Can this provider fetch only changed data since a timestamp?"""

    supports_pagination: bool = True
    """Does the provider support offset/limit or cursor pagination?"""

    supports_cursor_pagination: bool = False
    """Does the provider support cursor-based pagination (vs offset)?"""

    supports_etag: bool = False
    """Does the provider return ETag headers for conditional requests?"""

    supports_bulk_fetch: bool = False
    """Can multiple entities be fetched in one request?"""

    # Rate limits
    rate_limit_rps: float = 10.0
    """Requests per second (for token bucket)."""

    max_page_size: int = 100
    """Maximum items per page."""

    # Data quality
    is_verified: bool = False
    """Has the data from this provider been verified against real API responses?"""

    coverage_level: str = "partial"
    """'full' (all entities populated), 'partial' (some entities), 'minimal' (names only)."""


# ── Versioning ────────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class SyncSchemaVersion:
    """Version tracking for provider schemas.

    When ESPN changes their API response shape, increment the version.
    The sync engine can use this to conditionally apply transforms.
    """

    provider_slug: str       # "espn", "tapology"
    version: int             # Monotonically increasing
    description: str         # Human-readable description of the schema


# ── Provider Versions (current) ───────────────────────────────────────────────

ESPN_V1 = SyncSchemaVersion(
    provider_slug="espn",
    version=1,
    description="Verified 2026-08-01 — league-scoped URLs, embedded competitions",
)

# ── Provider Capabilities (pre-built) ─────────────────────────────────────────

ESPN_CAPABILITIES = ProviderCapabilities(
    provider_slug="espn",
    supports_fighters=True,
    supports_events=True,
    supports_rankings=True,
    supports_statistics=True,
    supports_broadcasts=True,
    supports_incremental=False,       # ESPN has no updated_since filter for MMA
    supports_pagination=True,
    supports_cursor_pagination=False,  # Offset-based pagination
    supports_etag=False,
    supports_bulk_fetch=False,
    rate_limit_rps=10.0,
    max_page_size=100,
    is_verified=True,                  # Verified 2026-08-01 against live API
    coverage_level="full",              # UFC is fully covered
)
