"""Support tables — external IDs, sync history, checkpoints, payloads, conflicts."""

from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, Integer, String, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column

from src.db.base import Base, TimestampMixin, new_uuid


class ExternalId(Base, TimestampMixin):
    """Cross-provider entity mapping. One fighter = many external IDs."""
    __tablename__ = "external_ids"
    __table_args__ = (
        {"comment": "Maps internal entity IDs to provider-specific external IDs"},
    )

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=new_uuid)
    entity_type: Mapped[str] = mapped_column(String(30), nullable=False)
    entity_id: Mapped[str] = mapped_column(UUID(as_uuid=False), nullable=False)
    provider: Mapped[str] = mapped_column(String(20), nullable=False)
    external_id: Mapped[str] = mapped_column(String(50), nullable=False)

    matched_by: Mapped[Optional[str]] = mapped_column(String(30))  # "name", "manual", "inferred"


class SyncRun(Base, TimestampMixin):
    """Tracks each sync execution."""
    __tablename__ = "sync_runs"
    __table_args__ = ({"comment": "Sync execution history"},)

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=new_uuid)
    status: Mapped[str] = mapped_column(String(20), default="RUNNING")
    mode: Mapped[str] = mapped_column(String(20), nullable=False)
    provider: Mapped[Optional[str]] = mapped_column(String(20))
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(),
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    error: Mapped[Optional[str]] = mapped_column(Text)

    total_inserted: Mapped[int] = mapped_column(Integer, default=0)
    total_updated: Mapped[int] = mapped_column(Integer, default=0)
    total_skipped: Mapped[int] = mapped_column(Integer, default=0)
    total_errors: Mapped[int] = mapped_column(Integer, default=0)
    api_calls: Mapped[int] = mapped_column(Integer, default=0)
    duration_ms: Mapped[float] = mapped_column(Integer, default=0)


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
    duration_ms: Mapped[float] = mapped_column(Integer, default=0)

    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    error: Mapped[Optional[str]] = mapped_column(Text)


class SyncCheckpoint(Base, TimestampMixin):
    """Resume checkpoint per entity + provider."""
    __table_args__ = ({"comment": "Sync resume checkpoints"},)

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=new_uuid)
    entity_type: Mapped[str] = mapped_column(String(30), nullable=False)
    provider: Mapped[str] = mapped_column(String(20), nullable=False)
    last_offset: Mapped[int] = mapped_column(Integer, default=0)
    last_page: Mapped[int] = mapped_column(Integer, default=0)
    total_records: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(20), default="IN_PROGRESS")
    last_error: Mapped[Optional[str]] = mapped_column(Text)
    completed: Mapped[bool] = mapped_column(Boolean, default=False)


class ProviderPayload(Base, TimestampMixin):
    """Raw provider JSON — archive for debugging, replay, testing."""
    __tablename__ = "provider_payloads"
    __table_args__ = ({"comment": "Raw provider API responses — debugging + replay"},)

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=new_uuid)
    provider: Mapped[str] = mapped_column(String(20), nullable=False)
    endpoint: Mapped[str] = mapped_column(String(200), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(30), nullable=False)
    external_id: Mapped[Optional[str]] = mapped_column(String(50))
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False)
    fetched_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(),
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
    value_a: Mapped[Optional[str]] = mapped_column(Text)
    value_b: Mapped[Optional[str]] = mapped_column(Text)

    chosen_authority: Mapped[str] = mapped_column(String(20), nullable=False)
    chosen_value: Mapped[Optional[str]] = mapped_column(Text)
    resolution: Mapped[str] = mapped_column(String(30), default="AUTHORITY")  # AUTHORITY | MANUAL | IGNORED
    resolved: Mapped[bool] = mapped_column(Boolean, default=True)


class DeadLetter(Base, TimestampMixin):
    """Data that failed validation — replayable."""
    __tablename__ = "dead_letters"
    __table_args__ = ({"comment": "Failed validation records — replayable"},)

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=new_uuid)
    entity_type: Mapped[str] = mapped_column(String(30), nullable=False)
    provider: Mapped[str] = mapped_column(String(20), nullable=False)
    external_id: Mapped[Optional[str]] = mapped_column(String(50))
    payload: Mapped[Optional[dict]] = mapped_column(JSONB)
    error: Mapped[str] = mapped_column(Text, nullable=False)
    error_category: Mapped[str] = mapped_column(String(30), nullable=False)
    replayed: Mapped[bool] = mapped_column(Boolean, default=False)
    replayed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
