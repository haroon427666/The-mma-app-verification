"""
SyncRun — domain model for a sync execution record.

Persisted to the sync_runs database table. Not to be confused with
SyncResult (the in-memory aggregate returned by the engine).
SyncRun is the persistent, queryable record.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class SyncRun:
    """Domain model for a sync execution record (maps to sync_runs table)."""

    run_id: str
    plan_name: str                       # "full_sync", "rankings_sync", etc.
    provider_slug: str                   # "espn", "tapology"
    status: str = "PENDING"              # PENDING, IN_PROGRESS, COMPLETED, PARTIAL, FAILED, CANCELLED
    started_at: datetime | None = None
    completed_at: datetime | None = None
    duration_ms: float = 0.0
    total_inserted: int = 0
    total_updated: int = 0
    total_skipped: int = 0
    total_errors: int = 0
    total_api_calls: int = 0
    error_msg: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    """Arbitrary metadata: schema_version, entity counts, etc."""
