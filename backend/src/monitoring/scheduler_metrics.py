"""Scheduler Metrics — real-time job stats for Grafana dashboard.

Extends the Phase 7 scheduler with proper Prometheus metric export.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class SchedulerMetricsCollector:
    """Collects scheduler metrics and pushes to Prometheus."""

    def record_job_start(self, job_name: str) -> None:
        try:
            from src.metrics.prometheus import get_metrics
            m = get_metrics()
            m.scheduler_running.inc()
        except Exception:
            pass

    def record_job_finish(self, job_name: str, status: str, duration_ms: float) -> None:
        try:
            from src.metrics.prometheus import get_metrics
            m = get_metrics()
            m.scheduler_running.dec()
            m.sync_jobs_total.labels(job=job_name, status=status).inc()
            m.sync_job_duration.labels(job=job_name, status=status).observe(duration_ms / 1000)
        except Exception:
            pass

    def record_job_failed(self, job_name: str, duration_ms: float = 0) -> None:
        try:
            from src.metrics.prometheus import get_metrics
            m = get_metrics()
            m.scheduler_running.dec()
            m.scheduler_failed.labels(job=job_name).inc()
            m.sync_jobs_total.labels(job=job_name, status="failed").inc()
            if duration_ms:
                m.sync_job_duration.labels(job=job_name, status="failed").observe(duration_ms / 1000)
        except Exception:
            pass

    def record_retry(self, job_name: str) -> None:
        try:
            from src.metrics.prometheus import get_metrics
            m = get_metrics()
            m.scheduler_retries.labels(job=job_name).inc()
        except Exception:
            pass

    def record_queue_size(self, queued: int, running: int) -> None:
        try:
            from src.metrics.prometheus import get_metrics
            m = get_metrics()
            m.scheduler_queued.set(queued)
            m.scheduler_running.set(running)
        except Exception:
            pass

    def record_records_synced(
        self, job_name: str, inserted: int = 0, updated: int = 0, errors: int = 0,
    ) -> None:
        try:
            from src.metrics.prometheus import get_metrics
            m = get_metrics()
            m.sync_records_total.labels(job=job_name, operation="inserted").inc(inserted)
            m.sync_records_total.labels(job=job_name, operation="updated").inc(updated)
            m.sync_records_total.labels(job=job_name, operation="errors").inc(errors)
        except Exception:
            pass

    def record_provider_call(self, provider: str, status: str, latency_ms: float) -> None:
        try:
            from src.metrics.prometheus import get_metrics
            m = get_metrics()
            m.provider_requests.labels(provider=provider, status=status).inc()
            m.provider_latency.labels(provider=provider).observe(latency_ms / 1000)
        except Exception:
            pass

    def record_login(self, status: str) -> None:
        try:
            from src.metrics.prometheus import get_metrics
            m = get_metrics()
            m.login_attempts.labels(status=status).inc()
            if status == "failed":
                m.failed_logins.inc()
        except Exception:
            pass

    def record_jwt_created(self) -> None:
        try:
            from src.metrics.prometheus import get_metrics
            m = get_metrics()
            m.jwt_created.inc()
        except Exception:
            pass

    def record_jwt_revoked(self) -> None:
        try:
            from src.metrics.prometheus import get_metrics
            m = get_metrics()
            m.jwt_revoked.inc()
        except Exception:
            pass

    def record_cache(self, hit: bool) -> None:
        try:
            from src.metrics.prometheus import get_metrics
            m = get_metrics()
            if hit:
                m.cache_hits.inc()
            else:
                m.cache_misses.inc()
        except Exception:
            pass

    def record_api_request(self, method: str, endpoint: str, status: int, duration_ms: float) -> None:
        try:
            from src.metrics.prometheus import get_metrics
            m = get_metrics()
            m.api_requests.labels(method=method, endpoint=endpoint, status=str(status)).inc()
            m.api_latency.labels(method=method, endpoint=endpoint).observe(duration_ms / 1000)
        except Exception:
            pass
