"""Database Monitoring — SQLAlchemy event hooks, slow query detection.

Monitors: connection pool, query duration, slow query logging, table sizes.

Slow queries are logged at:
    > 100ms → DEBUG
    > 250ms → WARNING
    > 500ms → ERROR
    > 1000ms → CRITICAL
"""

import logging
import time
from typing import Any

from sqlalchemy import event

logger = logging.getLogger(__name__)

SLOW_QUERY_THRESHOLDS = [
    (100, "DEBUG"),
    (250, "WARNING"),
    (500, "ERROR"),
    (1000, "CRITICAL"),
]


def _get_level_for_duration(ms: float) -> tuple[str, str | None]:
    for threshold, level in reversed(SLOW_QUERY_THRESHOLDS):
        if ms >= threshold:
            return level, f">={threshold}ms"
    return "DEBUG", None


def install_slow_query_detector(engine: Any) -> None:
    """Install SQLAlchemy event hooks for query timing.

    Logs every query that exceeds thresholds with SQL, parameters, and duration.
    Also updates metrics (if prometheus_client is available).

    Usage:
        from src.monitoring.database import install_slow_query_detector
        install_slow_query_detector(engine)
    """

    @event.listens_for(engine.sync_engine, "before_cursor_execute")
    def before_cursor_execute(conn: Any, cursor: Any, statement: Any, parameters: Any, context: Any, executemany: Any) -> None:
        conn.info["query_start"] = time.monotonic()
        conn.info["query_sql"] = statement[:500]
        conn.info["query_params"] = str(parameters)[:200]

    @event.listens_for(engine.sync_engine, "after_cursor_execute")
    def after_cursor_execute(conn: Any, cursor: Any, statement: Any, parameters: Any, context: Any, executemany: Any) -> None:
        start = conn.info.pop("query_start", None)
        if start is None:
            return

        duration_ms = (time.monotonic() - start) * 1000
        sql = conn.info.pop("query_sql", statement[:200])
        params = conn.info.pop("query_params", "")

        # Determine log level
        level, threshold_tag = _get_level_for_duration(duration_ms)

        if threshold_tag is not None:
            getattr(logger, level.lower())(
                f"SLOW QUERY [{threshold_tag}] {duration_ms:.1f}ms: {sql[:300]}",
                extra={
                    "query_duration_ms": round(duration_ms, 2),
                    "query_sql": sql[:500],
                    "query_params": params,
                },
            )

        # Update metrics
        try:
            from src.metrics.prometheus import get_metrics
            m = get_metrics()
            op = sql.split()[0].upper() if sql else "UNKNOWN"
            m.db_query_duration.labels(operation=op).observe(duration_ms / 1000)
        except Exception:
            pass

    logger.info("Slow query detector installed")


def install_connection_pool_monitor(engine: Any) -> None:
    """Track active/idle DB connections via SQLAlchemy pool events.

    Updates gauge metrics for Grafana dashboard.
    """

    @event.listens_for(engine.sync_engine, "checkout")
    def on_checkout(dbapi_connection: Any, connection_record: Any, connection_proxy: Any) -> None:
        try:
            pool = engine.sync_engine.pool
            from src.metrics.prometheus import get_metrics
            m = get_metrics()
            m.db_connections_active.set(pool.checkedout())
            m.db_connections_idle.set(pool.checkedin() if hasattr(pool, "checkedin") else 0)
        except Exception:
            pass

    @event.listens_for(engine.sync_engine, "checkin")
    def on_checkin(dbapi_connection: Any, connection_record: Any) -> None:
        try:
            pool = engine.sync_engine.pool
            from src.metrics.prometheus import get_metrics
            m = get_metrics()
            m.db_connections_active.set(pool.checkedout())
            m.db_connections_idle.set(pool.checkedin() if hasattr(pool, "checkedin") else 0)
        except Exception:
            pass

    logger.info("Connection pool monitor installed")
