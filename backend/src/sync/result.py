"""
Sync result — immutable aggregate outcome of a full sync run.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from src.sync.job import JobResult
from src.sync.types import SyncStatus


@dataclass(frozen=True)
class SyncResult:
    """Immutable aggregate result of a full sync run.

    One SyncResult contains N JobResults (one per entity type in the plan).
    Rollup totals are derived from job_results.
    """

    run_id: str
    overall_status: SyncStatus
    job_results: list[JobResult] = field(default_factory=list)
    started_at: datetime | None = None
    completed_at: datetime | None = None
    duration_ms: float = 0.0

    @property
    def total_inserted(self) -> int:
        return sum(j.records_inserted for j in self.job_results)

    @property
    def total_updated(self) -> int:
        return sum(j.records_updated for j in self.job_results)

    @property
    def total_skipped(self) -> int:
        return sum(j.records_skipped for j in self.job_results)

    @property
    def total_errors(self) -> int:
        return sum(j.records_errors for j in self.job_results)

    @property
    def total_api_calls(self) -> int:
        return sum(j.api_calls for j in self.job_results)

    @property
    def completed_jobs(self) -> int:
        return sum(1 for j in self.job_results if j.status.value == "COMPLETED")

    @property
    def failed_jobs(self) -> int:
        return sum(1 for j in self.job_results if j.status.value == "FAILED")

    @property
    def total_jobs(self) -> int:
        return len(self.job_results)

    # ── Summary ────────────────────────────────────────────────────────────

    def summary(self) -> dict[str, Any]:
        """JSON-serializable summary for logging."""
        return {
            "run_id": self.run_id,
            "status": self.overall_status.value,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "duration_ms": round(self.duration_ms, 1),
            "total_jobs": self.total_jobs,
            "completed_jobs": self.completed_jobs,
            "failed_jobs": self.failed_jobs,
            "total_inserted": self.total_inserted,
            "total_updated": self.total_updated,
            "total_skipped": self.total_skipped,
            "total_errors": self.total_errors,
            "total_api_calls": self.total_api_calls,
            "jobs": [
                {
                    "entity": j.entity_type,
                    "status": j.status.value,
                    "inserted": j.records_inserted,
                    "updated": j.records_updated,
                    "skipped": j.records_skipped,
                    "errors": j.records_errors,
                    "duration_ms": round(j.duration_ms, 1),
                    "error": j.error_msg,
                }
                for j in self.job_results
            ],
        }
