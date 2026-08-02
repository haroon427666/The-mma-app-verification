"""Production Prometheus Metrics — full prometheus_client integration.

Every metric the Grafana dashboards need. No more lightweight mock.
Exported at GET /metrics in Prometheus text format.

Metrics:
    api_requests_total{method, endpoint, status}
    api_latency_seconds{method, endpoint}          — Histogram (P50/P90/P99)
    sync_job_duration_seconds{job, status}         — Histogram
    sync_jobs_total{job, status}                    — Counter
    sync_records_total{job, operation}              — Counter (inserted/updated/errors)
    provider_requests_total{provider, status}       — Counter
    provider_latency_seconds{provider}              — Histogram
    scheduler_running_jobs                          — Gauge
    scheduler_queued_jobs                           — Gauge
    scheduler_failed_jobs_total                     — Counter
    cache_hits_total                                — Counter
    cache_misses_total                              — Counter
    db_connections_active                           — Gauge
    db_connections_idle                             — Gauge
    db_query_duration_seconds                       — Histogram
    login_attempts_total{status}                    — Counter
    failed_logins_total                             — Counter
    jwt_created_total                               — Counter
    jwt_revoked_total                               — Counter
    notification_sent_total{type}                   — Counter
    payload_archive_size_bytes                      — Gauge
"""

import logging
import time
from contextlib import contextmanager
from typing import Optional

try:
    from prometheus_client import Counter, Gauge, Histogram, generate_latest, REGISTRY
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False

logger = logging.getLogger(__name__)


class Metrics:
    """Central metrics registry — all application metrics in one place."""

    def __init__(self):
        self._started = False

    def setup(self) -> None:
        """Initialize all metrics. Call once at startup."""
        if self._started:
            return
        self._started = True

        if not PROMETHEUS_AVAILABLE:
            logger.warning("prometheus_client not installed — metrics disabled")
            self._init_mock()
            return

        self._init_real()
        logger.info("Prometheus metrics initialized")

    def _init_real(self):
        # ── API ────────────────────────────────────────────────────
        self.api_requests = Counter(
            "api_requests_total", "Total API requests",
            ["method", "endpoint", "status"],
        )
        self.api_latency = Histogram(
            "api_latency_seconds", "API request latency",
            ["method", "endpoint"],
            buckets=[0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0],
        )

        # ── Sync ───────────────────────────────────────────────────
        self.sync_job_duration = Histogram(
            "sync_job_duration_seconds", "Sync job duration",
            ["job", "status"],
            buckets=[1, 5, 15, 30, 60, 120, 300, 600, 900],
        )
        self.sync_jobs_total = Counter(
            "sync_jobs_total", "Sync job runs", ["job", "status"],
        )
        self.sync_records_total = Counter(
            "sync_records_total", "Records synced", ["job", "operation"],
        )

        # ── Provider ───────────────────────────────────────────────
        self.provider_requests = Counter(
            "provider_requests_total", "Provider API requests",
            ["provider", "status"],
        )
        self.provider_latency = Histogram(
            "provider_latency_seconds", "Provider API latency",
            ["provider"],
            buckets=[0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0],
        )

        # ── Scheduler ──────────────────────────────────────────────
        self.scheduler_running = Gauge(
            "scheduler_running_jobs", "Currently running jobs",
        )
        self.scheduler_queued = Gauge(
            "scheduler_queued_jobs", "Jobs waiting in queue",
        )
        self.scheduler_failed = Counter(
            "scheduler_failed_jobs_total", "Total failed jobs", ["job"],
        )
        self.scheduler_retries = Counter(
            "scheduler_retries_total", "Job retry count", ["job"],
        )

        # ── Cache ──────────────────────────────────────────────────
        self.cache_hits = Counter("cache_hits_total", "Cache hits")
        self.cache_misses = Counter("cache_misses_total", "Cache misses")

        # ── Database ────────────────────────────────────────────────
        self.db_connections_active = Gauge(
            "db_connections_active", "Active DB connections",
        )
        self.db_connections_idle = Gauge(
            "db_connections_idle", "Idle DB connections",
        )
        self.db_query_duration = Histogram(
            "db_query_duration_seconds", "Database query duration",
            ["operation"],
            buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0],
        )

        # ── Auth ───────────────────────────────────────────────────
        self.login_attempts = Counter(
            "login_attempts_total", "Login attempts", ["status"],
        )
        self.failed_logins = Counter(
            "failed_logins_total", "Failed login attempts",
        )
        self.jwt_created = Counter("jwt_created_total", "JWTs issued")
        self.jwt_revoked = Counter("jwt_revoked_total", "JWTs revoked")

        # ── Notifications ──────────────────────────────────────────
        self.notifications_sent = Counter(
            "notification_sent_total", "Notifications sent", ["type"],
        )

        # ── Payload Archive ────────────────────────────────────────
        self.payload_archive_size = Gauge(
            "payload_archive_size_bytes", "Estimated payload archive size",
        )

    def _init_mock(self):
        """Dummy metrics that silently accept calls (no prometheus_client)."""

        class _NoOp:
            def labels(self, **kw): return self
            def inc(self, amount=1): pass
            def dec(self, amount=1): pass
            def set(self, value): pass
            def observe(self, value): pass
            def time(self): return _Timer()

        class _Timer:
            def __enter__(self): return self
            def __exit__(self, *a): pass

        self.api_requests = _NoOp()
        self.api_latency = _NoOp()
        self.sync_job_duration = _NoOp()
        self.sync_jobs_total = _NoOp()
        self.sync_records_total = _NoOp()
        self.provider_requests = _NoOp()
        self.provider_latency = _NoOp()
        self.scheduler_running = _NoOp()
        self.scheduler_queued = _NoOp()
        self.scheduler_failed = _NoOp()
        self.scheduler_retries = _NoOp()
        self.cache_hits = _NoOp()
        self.cache_misses = _NoOp()
        self.db_connections_active = _NoOp()
        self.db_connections_idle = _NoOp()
        self.db_query_duration = _NoOp()
        self.login_attempts = _NoOp()
        self.failed_logins = _NoOp()
        self.jwt_created = _NoOp()
        self.jwt_revoked = _NoOp()
        self.notifications_sent = _NoOp()
        self.payload_archive_size = _NoOp()

    def export(self) -> str:
        if PROMETHEUS_AVAILABLE:
            return generate_latest(REGISTRY).decode()
        return "# prometheus_client not installed\n"


# Singleton
_metrics = Metrics()


def get_metrics() -> Metrics:
    return _metrics


def setup_metrics() -> None:
    _metrics.setup()
