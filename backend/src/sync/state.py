"""
Sync state — checkpoint and resume model for every entity/provider combination.

Every production sync engine needs to track what was synced, when, and where
to resume. This model stores per-entity, per-provider state so the engine can:

- Resume from the last successful page after a crash
- Skip entities that haven't changed since last sync (incremental)
- Track cursors, etags, and continuation tokens from paginated APIs
- Detect provider schema version changes

Usage:
    state = SyncState.for_entity(EntityType.FIGHTER, provider_slug="espn")
    state.last_page = 5
    state.last_cursor = "abc123"
    state.checkpoint = {"event_id": "600051442"}
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from src.sync.types import EntityType


@dataclass
class SyncState:
    """Per-entity, per-provider sync progress tracking.

    Persisted to the database (sync_state table or JSON column on sync_runs).
    Checked at the start of every job to decide whether or what to sync.
    """

    # ── Identity ───────────────────────────────────────────────────────────
    entity_type: EntityType
    provider_slug: str                 # "espn", "tapology"

    # ── Timing ─────────────────────────────────────────────────────────────
    last_successful_sync: datetime | None = None   # When the last full sync completed
    last_attempt: datetime | None = None            # When the last attempt started
    last_failure: datetime | None = None            # When the last failure occurred

    # ── Progress / Resumption ──────────────────────────────────────────────
    last_page: int = 0                  # Page number last synced (for pagination resume)
    last_cursor: str | None = None      # API cursor/continuation token
    last_offset: int = 0                # Offset-based pagination position
    total_pages: int = 0                # Total pages known from last sync

    # ── Incremental Sync Signals ───────────────────────────────────────────
    etag: str | None = None             # HTTP ETag from last response
    updated_since: datetime | None = None  # Fetch only items changed after this
    last_modified: datetime | None = None  # Last-Modified header from provider

    # ── Checkpoint ─────────────────────────────────────────────────────────
    checkpoint: dict[str, Any] = field(default_factory=dict)
    """Arbitrary checkpoint data. Sync jobs store what they need:
       - Rankings: {"promotion_id": "...", "categories_synced": 12}
       - Events: {"last_event_date": "2025-12-31T00:00Z"}
       - Fighters: {"last_fighter_id": "3332412"}
    """

    # ── Status ─────────────────────────────────────────────────────────────
    status: str = "PENDING"             # PENDING, IN_PROGRESS, COMPLETED, FAILED
    error_msg: str | None = None        # Last error message
    consecutive_failures: int = 0       # Track for circuit breaking

    # ── Versioning ─────────────────────────────────────────────────────────
    provider_schema_version: int = 1    # Increment when provider schema changes

    # ── Aggregate Stats ────────────────────────────────────────────────────
    total_synced: int = 0               # Cumulative rows synced across all runs
    total_errors: int = 0               # Cumulative errors

    # ── Factory ────────────────────────────────────────────────────────────

    @classmethod
    def for_entity(
        cls,
        entity_type: EntityType,
        provider_slug: str,
    ) -> "SyncState":
        """Create a fresh sync state for an entity/provider pair."""
        return cls(entity_type=entity_type, provider_slug=provider_slug)

    # ── State Transitions ──────────────────────────────────────────────────

    def mark_started(self, now: datetime) -> None:
        """Called when a sync job begins."""
        self.status = "IN_PROGRESS"
        self.last_attempt = now

    def mark_completed(self, now: datetime) -> None:
        """Called when a sync job finishes successfully."""
        self.status = "COMPLETED"
        self.last_successful_sync = now
        self.consecutive_failures = 0
        self.error_msg = None
        # Reset pagination progress on successful completion
        self.last_page = 0
        self.last_offset = 0
        self.last_cursor = None

    def mark_failed(self, now: datetime, error: str) -> None:
        """Called when a sync job fails.
        
        CHECKPOINT IS PRESERVED: last_page, last_offset, last_cursor
        are NOT reset — they're needed for resume.
        """
        self.status = "FAILED"
        self.last_failure = now
        self.error_msg = error
        self.consecutive_failures += 1

    def update_progress(
        self,
        page: int,
        offset: int,
        items_synced: int,
        cursor: str | None = None,
    ) -> None:
        """Called after each batch/page to save progress for resume."""
        self.last_page = page
        self.last_offset = offset
        self.total_synced += items_synced
        if cursor:
            self.last_cursor = cursor

    def prepare_for_resume(self) -> dict:
        """Return pagination parameters for resuming a crashed sync.
        
        The job uses these to skip already-synced pages.
        Returns empty params if no checkpoint exists.
        """
        if self.last_page == 0 and not self.last_cursor:
            return {}
        params: dict = {
            "offset": self.last_offset,
        }
        if self.last_cursor:
            params["cursor"] = self.last_cursor
        return params

    def prepare_for_incremental(self) -> dict:
        """Return parameters for an incremental delta sync.
        
        If updated_since is set, pass it to the provider.
        If no reference point exists, returns empty (full sync).
        """
        if self.updated_since is None and self.last_successful_sync is None:
            return {}
        ref = self.updated_since or self.last_successful_sync
        return {"updated_since": ref}

    @property
    def can_incremental(self) -> bool:
        """True if we have enough state to do an incremental sync."""
        return (
            self.last_successful_sync is not None
            and self.updated_since is not None
        )

    @property
    def needs_full_sync(self) -> bool:
        """True if a full sync is needed (first run or after schema change)."""
        return (
            self.last_successful_sync is None
            or self.status == "FAILED"
            or self.total_synced == 0
        )
