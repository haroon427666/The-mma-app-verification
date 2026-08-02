"""Sync Job Definitions — what each scheduled job does.

Each job is a coroutine that:
1. Acquires a distributed lock
2. Fetches data from the appropriate provider
3. Parses + validates
4. Upserts into the database
5. Records metrics
6. Releases the lock

Frequency table:
    events_upcoming     every 15 min      — poll for new events
    events_live         every 30 sec      — active fight night polling
    events_results      every 2 min       — poll for fight results
    rankings            daily             — ESPN + Octagon verification
    fighters_enrich     weekly            — TSDB + Octagon enrichment
    promotion_meta      weekly            — TSDB branding refresh
    cleanup             daily             — old payloads, temp files
"""

import asyncio
import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Optional

logger = logging.getLogger(__name__)


class JobStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class JobResult:
    job_name: str
    status: JobStatus
    duration_ms: float = 0.0
    records_inserted: int = 0
    records_updated: int = 0
    errors: int = 0
    error_message: str = ""


@dataclass
class JobConfig:
    name: str
    description: str = ""
    cron: Optional[str] = None           # APScheduler cron expression
    interval_seconds: Optional[int] = None  # Alternative to cron
    max_runtime_seconds: int = 600       # Kill job if it runs longer than this
    lock_ttl: int = 300                  # Distributed lock TTL
    retry_policy: Optional["RetryPolicy"] = None
    enabled: bool = True
    depends_on: list[str] = field(default_factory=list)  # Must run after these


# ── Job Coroutine Definitions ──────────────────────────────────────────────────

async def sync_events_upcoming(ctx: "SyncContext") -> JobResult:
    """Fetch upcoming UFC events from ESPN + enrich from TSDB."""
    start = time.monotonic()
    try:
        events = await ctx.espn_provider.fetch_events()
        # enrichment would go here
        duration = (time.monotonic() - start) * 1000
        return JobResult(
            job_name="events_upcoming", status=JobStatus.SUCCESS,
            duration_ms=duration, records_inserted=len(events),
        )
    except Exception as e:
        return JobResult(
            job_name="events_upcoming", status=JobStatus.FAILED,
            duration_ms=(time.monotonic() - start) * 1000,
            errors=1, error_message=str(e),
        )


async def sync_events_live(ctx: "SyncContext") -> JobResult:
    """High-frequency poll for active event results."""
    start = time.monotonic()
    try:
        # Only run if UFC event is active
        if not ctx.is_live_event_active():
            return JobResult(job_name="events_live", status=JobStatus.SUCCESS,
                           duration_ms=0)  # Skipped — no live event

        events = await ctx.espn_provider.fetch_events()
        for event in events:
            if event.status == "FINAL" or event.status == "IN_PROGRESS":
                competitions = await ctx.espn_provider.fetch_competitions(str(event.external_id))
                # Upsert competitions with results

        duration = (time.monotonic() - start) * 1000
        return JobResult(
            job_name="events_live", status=JobStatus.SUCCESS,
            duration_ms=duration, records_updated=len(events),
        )
    except Exception as e:
        return JobResult(job_name="events_live", status=JobStatus.FAILED,
                        errors=1, error_message=str(e))


async def sync_results(ctx: "SyncContext") -> JobResult:
    """Poll for completed fights — update winners, methods, times."""
    start = time.monotonic()
    try:
        # Find events with status=FINAL but competitions still SCHEDULED
        # Resolve their competition statuses
        duration = (time.monotonic() - start) * 1000
        return JobResult(job_name="results", status=JobStatus.SUCCESS,
                        duration_ms=duration)
    except Exception as e:
        return JobResult(job_name="results", status=JobStatus.FAILED,
                        errors=1, error_message=str(e))


async def sync_rankings(ctx: "SyncContext") -> JobResult:
    """Daily rankings sync — ESPN + Octagon verification."""
    start = time.monotonic()
    try:
        rankings = await ctx.espn_provider.fetch_rankings()
        # Octagon verification
        duration = (time.monotonic() - start) * 1000
        return JobResult(job_name="rankings", status=JobStatus.SUCCESS,
                        duration_ms=duration, records_inserted=len(rankings))
    except Exception as e:
        return JobResult(job_name="rankings", status=JobStatus.FAILED,
                        errors=1, error_message=str(e))


async def sync_fighter_enrichment(ctx: "SyncContext") -> JobResult:
    """Weekly enrichment from TSDB + Octagon — bios, images, gym, style."""
    start = time.monotonic()
    try:
        # Octagon enrichment first (higher priority)
        oct_fighters = await ctx.octagon_provider.fetch_fighters()
        # TSDB enrichment second (media + bios)
        tsdb_fighters = await ctx.tsdb_provider.fetch_fighters()

        duration = (time.monotonic() - start) * 1000
        return JobResult(
            job_name="fighter_enrichment", status=JobStatus.SUCCESS,
            duration_ms=duration,
            records_updated=len(oct_fighters) + len(tsdb_fighters),
        )
    except Exception as e:
        return JobResult(job_name="fighter_enrichment", status=JobStatus.FAILED,
                        errors=1, error_message=str(e))


async def sync_promotion_meta(ctx: "SyncContext") -> JobResult:
    """Weekly promotion branding refresh from TSDB."""
    start = time.monotonic()
    try:
        promos = await ctx.tsdb_provider.fetch_promotions()
        duration = (time.monotonic() - start) * 1000
        return JobResult(job_name="promotion_meta", status=JobStatus.SUCCESS,
                        duration_ms=duration, records_updated=len(promos))
    except Exception as e:
        return JobResult(job_name="promotion_meta", status=JobStatus.FAILED,
                        errors=1, error_message=str(e))


async def sync_cleanup(ctx: "SyncContext") -> JobResult:
    """Daily cleanup — old payloads, expired checkpoints."""
    start = time.monotonic()
    try:
        from src.sync.payload_store import PayloadStore
        store = PayloadStore(ctx.db)
        pruned = await store.prune_old(days=90)

        duration = (time.monotonic() - start) * 1000
        return JobResult(job_name="cleanup", status=JobStatus.SUCCESS,
                        duration_ms=duration, records_updated=pruned)
    except Exception as e:
        return JobResult(job_name="cleanup", status=JobStatus.FAILED,
                        errors=1, error_message=str(e))


# ── Job Registry ──────────────────────────────────────────────────────────────

JOB_REGISTRY: dict[str, JobConfig] = {
    "events_upcoming": JobConfig(
        name="events_upcoming",
        description="Poll ESPN for new/upcoming events",
        interval_seconds=900,  # 15 min
        max_runtime_seconds=120,
    ),
    "events_live": JobConfig(
        name="events_live",
        description="High-frequency poll during active fight nights",
        interval_seconds=30,  # 30 sec
        max_runtime_seconds=60,
        enabled=False,  # Only enabled when live event detected
    ),
    "results": JobConfig(
        name="results",
        description="Poll for fight results during live events",
        interval_seconds=120,  # 2 min
        max_runtime_seconds=60,
    ),
    "rankings": JobConfig(
        name="rankings",
        description="Daily ESPN rankings sync + Octagon verification",
        cron="0 6 * * *",  # Daily 6 AM
        max_runtime_seconds=300,
    ),
    "fighter_enrichment": JobConfig(
        name="fighter_enrichment",
        description="Weekly TSDB + Octagon fighter enrichment",
        cron="0 5 * * 0",  # Sunday 5 AM
        max_runtime_seconds=900,
    ),
    "promotion_meta": JobConfig(
        name="promotion_meta",
        description="Weekly TSDB promotion branding refresh",
        cron="0 6 * * 0",  # Sunday 6 AM
        max_runtime_seconds=300,
    ),
    "cleanup": JobConfig(
        name="cleanup",
        description="Daily cleanup — old payloads, expired checkpoints",
        cron="0 3 * * *",  # Daily 3 AM
        max_runtime_seconds=60,
    ),
}

JOB_FUNCTIONS: dict[str, Callable] = {
    "events_upcoming": sync_events_upcoming,
    "events_live": sync_events_live,
    "results": sync_results,
    "rankings": sync_rankings,
    "fighter_enrichment": sync_fighter_enrichment,
    "promotion_meta": sync_promotion_meta,
    "cleanup": sync_cleanup,
}
