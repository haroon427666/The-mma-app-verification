"""Support tables — external IDs, sync history, checkpoints, payloads, conflicts."""

from datetime import UTC, datetime
from typing import Any

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.db.base import Base, JSONType, TimestampMixin, new_uuid


class ExternalId(Base, TimestampMixin):
    """Cross-provider entity mapping. One fighter = many external IDs."""
    __tablename__ = "external_ids"
    __table_args__ = (
        {"comment": "Maps internal entity IDs to provider-specific external IDs"},
    )

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=new_uuid)
    entity_type: Mapped[str] = mapped_column(String(30), nullable=False)
    # String(36) on SQLite: NUMERIC-affinity UUIDs with all-digit hex are
    # stored as REAL floats and crash the result processor on read-back.
    # Postgres keeps the native UUID type (variant is dialect-scoped).
    entity_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False).with_variant(String(36), "sqlite"), nullable=False
    )
    provider: Mapped[str] = mapped_column(String(20), nullable=False)
    external_id: Mapped[str] = mapped_column(String(50), nullable=False)

    matched_by: Mapped[str | None] = mapped_column(String(30))  # "name", "manual", "inferred"


class SyncRun(Base, TimestampMixin):
    """Tracks each sync execution."""
    __tablename__ = "sync_runs"
    __table_args__ = ({"comment": "Sync execution history"},)

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=new_uuid)
    status: Mapped[str] = mapped_column(String(20), default="RUNNING")
    mode: Mapped[str] = mapped_column(String(20), nullable=False)
    provider: Mapped[str | None] = mapped_column(String(20))
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC),
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    error: Mapped[str | None] = mapped_column(Text)

    total_inserted: Mapped[int] = mapped_column(Integer, default=0)
    total_updated: Mapped[int] = mapped_column(Integer, default=0)
    total_skipped: Mapped[int] = mapped_column(Integer, default=0)
    total_errors: Mapped[int] = mapped_column(Integer, default=0)
    api_calls: Mapped[int] = mapped_column(Integer, default=0)
    duration_ms: Mapped[float] = mapped_column(Float, default=0)


class SyncJob(Base, TimestampMixin):
    """Per-entity job within a sync run."""
    __tablename__ = "sync_jobs"
    __table_args__ = ({"comment": "Per-entity sync job within a run"},)

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=new_uuid)
    sync_run_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("sync_runs.id"), nullable=False,
    )
    entity_type: Mapped[str] = mapped_column(String(30), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="PENDING")

    records_inserted: Mapped[int] = mapped_column(Integer, default=0)
    records_updated: Mapped[int] = mapped_column(Integer, default=0)
    records_skipped: Mapped[int] = mapped_column(Integer, default=0)
    records_errors: Mapped[int] = mapped_column(Integer, default=0)
    api_calls: Mapped[int] = mapped_column(Integer, default=0)
    duration_ms: Mapped[float] = mapped_column(Float, default=0)

    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    error: Mapped[str | None] = mapped_column(Text)


class SyncCheckpoint(Base, TimestampMixin):
    """Resume checkpoint per entity + provider."""
    __tablename__ = "sync_checkpoints"
    __table_args__ = (
        UniqueConstraint(
            "entity_type", "provider",
            name="uq_sync_checkpoints_entity_provider",
        ),
        {"comment": "Sync resume checkpoints"},
    )

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=new_uuid)
    entity_type: Mapped[str] = mapped_column(String(30), nullable=False)
    provider: Mapped[str] = mapped_column(String(20), nullable=False)
    last_offset: Mapped[int] = mapped_column(Integer, default=0)
    last_page: Mapped[int] = mapped_column(Integer, default=0)
    total_records: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(20), default="IN_PROGRESS")
    last_error: Mapped[str | None] = mapped_column(Text)
    completed: Mapped[bool] = mapped_column(Boolean, default=False)
    data: Mapped[dict | None] = mapped_column(JSONType)
    """Serialized SyncState payload (checkpoint dict, timestamps, cursors)."""


class SyncDiscoveredAthlete(Base, TimestampMixin):
    """Deduplicated athlete-ID registry — convergence point for every discovery
    surface (global listing walk, roster walks, ranking injection,
    competition/eventlog refs). One row per (provider, external_id)."""
    __tablename__ = "sync_discovered_athletes"
    __table_args__ = (
        UniqueConstraint(
            "provider", "external_id",
            name="uq_sync_discovered_athletes_provider_external",
        ),
        {"comment": "Deduplicated athlete-ID discovery registry"},
    )

    id: Mapped[int] = mapped_column(
        BigInteger().with_variant(Integer, "sqlite"),
        primary_key=True, autoincrement=True,
    )
    provider: Mapped[str] = mapped_column(String(20), nullable=False)
    external_id: Mapped[str] = mapped_column(String(50), nullable=False)
    source: Mapped[str] = mapped_column(String(50), nullable=False)
    # String(36) on SQLite: avoids NUMERIC-affinity corruption of UUID hex
    # values (all-digit hex is converted to REAL by SQLite). Postgres keeps
    # the native UUID type (variant is dialect-scoped).
    run_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=False).with_variant(String(36), "sqlite")
    )
    consumed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    """False = still queued for the fighter window; True = synced or dead-ended."""


class SyncDiscoveryCheckpoint(Base, TimestampMixin):
    """Per-source resumable discovery-walk state (page/offset/count/completion)."""
    __tablename__ = "sync_discovery_checkpoints"
    __table_args__ = (
        UniqueConstraint(
            "provider", "source", "league_slug",
            name="uq_sync_discovery_checkpoints_source",
        ),
        {"comment": "Per-source discovery-walk checkpoints (resumable census)"},
    )

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=new_uuid)
    provider: Mapped[str] = mapped_column(String(20), nullable=False)
    source: Mapped[str] = mapped_column(String(50), nullable=False)
    league_slug: Mapped[str] = mapped_column(String(30), nullable=False, default="")
    page: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    offset: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    discovered_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_athlete_id: Mapped[str | None] = mapped_column(String(50))
    status: Mapped[str] = mapped_column(String(20), default="IN_PROGRESS", nullable=False)
    last_error: Mapped[str | None] = mapped_column(Text)
    completed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    # String(36) on SQLite: same NUMERIC-affinity avoidance as above.
    run_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=False).with_variant(String(36), "sqlite")
    )
    last_processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class ProviderPayload(Base, TimestampMixin):
    """Raw provider JSON — archive for debugging, replay, testing."""
    __tablename__ = "provider_payloads"
    __table_args__ = ({"comment": "Raw provider API responses — debugging + replay"},)

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=new_uuid)
    provider: Mapped[str] = mapped_column(String(20), nullable=False)
    endpoint: Mapped[str] = mapped_column(String(200), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(30), nullable=False)
    external_id: Mapped[str | None] = mapped_column(String(50))
    payload: Mapped[dict[str, Any]] = mapped_column(JSONType, nullable=False)
    fetched_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC),
    )


class ProviderConflict(Base, TimestampMixin):
    """Records disagreements between providers."""
    __tablename__ = "provider_conflicts"
    __table_args__ = ({"comment": "Provider disagreements — audit trail"},)

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=new_uuid)
    entity_type: Mapped[str] = mapped_column(String(30), nullable=False)
    entity_id: Mapped[str] = mapped_column(UUID(as_uuid=False), nullable=False)
    field: Mapped[str] = mapped_column(String(100), nullable=False)

    provider_a: Mapped[str] = mapped_column(String(20), nullable=False)
    provider_b: Mapped[str] = mapped_column(String(20), nullable=False)
    value_a: Mapped[str | None] = mapped_column(Text)
    value_b: Mapped[str | None] = mapped_column(Text)

    chosen_authority: Mapped[str] = mapped_column(String(20), nullable=False)
    chosen_value: Mapped[str | None] = mapped_column(Text)
    resolution: Mapped[str] = mapped_column(String(30), default="AUTHORITY")  # AUTHORITY | MANUAL | IGNORED
    resolved: Mapped[bool] = mapped_column(Boolean, default=True)


class DeadLetter(Base, TimestampMixin):
    """Data that failed validation — replayable."""
    __tablename__ = "dead_letters"
    __table_args__ = ({"comment": "Failed validation records — replayable"},)

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=new_uuid)
    entity_type: Mapped[str] = mapped_column(String(30), nullable=False)
    provider: Mapped[str] = mapped_column(String(20), nullable=False)
    external_id: Mapped[str | None] = mapped_column(String(50))
    payload: Mapped[dict[str, Any] | None] = mapped_column(JSONType)
    error: Mapped[str] = mapped_column(Text, nullable=False)
    error_category: Mapped[str] = mapped_column(String(30), nullable=False)
    replayed: Mapped[bool] = mapped_column(Boolean, default=False)
    replayed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class FighterProviderRecordStatus(Base, TimestampMixin):
    """Per-provider fighter-record fetch outcomes (Phase D, sparse).

    fighter_records row present  ⇔ HAS_RECORD — canonical signal; no row kept.
    status row present           ⇔ CONFIRMED_ABSENT | FETCH_FAILED |
                                   PERMANENT_FAILURE (per provider).
    no row                       ⇔ NOT_CHECKED.

    A persisted absence NEVER blocks record insertion: persisting a real
    record deletes the status row (FighterUpsert._delete_record_status).
    """
    __tablename__ = "fighter_provider_record_status"
    __table_args__ = (
        {"comment": "Per-provider fighter-record fetch outcomes (sparse)"},
    )

    # Same UUID storage as fighters.id / fighter_records.fighter_id so joins
    # match on every dialect (Postgres: native UUID; SQLite: CHAR(32) hex).
    fighter_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("fighters.id", ondelete="CASCADE"),
        primary_key=True,
    )
    provider: Mapped[str] = mapped_column(String(20), primary_key=True)

    status: Mapped[str] = mapped_column(String(30), nullable=False)
    # RecordFetchStatus: CONFIRMED_ABSENT | FETCH_FAILED | PERMANENT_FAILURE

    last_checked_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )
    last_http_status: Mapped[int | None] = mapped_column(Integer)
    result_detail: Mapped[str | None] = mapped_column(Text)
    retry_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_run_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("sync_runs.id"),
    )
    provenance: Mapped[str | None] = mapped_column(String(30))
