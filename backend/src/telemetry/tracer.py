"""OpenTelemetry Tracing — distributed tracing for API, DB, Redis, providers.

Setup:
    from src.telemetry.tracer import setup_tracing
    setup_tracing(app_name="mma-backend", otlp_endpoint="http://localhost:4317")

Spans:
    Client → FastAPI → Service → Repository → Database
          → Redis
          → ESPN / TSDB / Octagon

Each span is timed and linked by trace_id.
"""

import logging
import os
from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any

logger = logging.getLogger(__name__)

OTEL_AVAILABLE = False

try:
    from opentelemetry import trace
    from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
    from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
    from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
    OTEL_AVAILABLE = True
except ImportError:
    pass


def setup_tracing(
    app_name: str = "mma-backend",
    otlp_endpoint: str | None = None,
    console: bool = False,
) -> Any | None:
    """Initialize OpenTelemetry tracing. Returns tracer if available."""
    if not OTEL_AVAILABLE:
        logger.warning("opentelemetry packages not installed — tracing disabled")
        return None

    provider = TracerProvider()

    # Console exporter (dev)
    if console:
        provider.add_span_processor(BatchSpanProcessor(ConsoleSpanExporter()))

    # OTLP exporter (production: Jaeger, Grafana Tempo, Honeycomb)
    if otlp_endpoint or os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT"):
        endpoint = otlp_endpoint or os.environ["OTEL_EXPORTER_OTLP_ENDPOINT"]
        try:
            provider.add_span_processor(
                BatchSpanProcessor(OTLPSpanExporter(endpoint=endpoint))
            )
            logger.info(f"OTLP exporter configured: {endpoint}")
        except Exception as e:
            logger.warning(f"OTLP exporter failed: {e}")

    trace.set_tracer_provider(provider)
    tracer = trace.get_tracer(app_name)
    logger.info(f"OpenTelemetry tracing initialized for {app_name}")
    return tracer


def instrument_app(app: Any) -> None:
    """Auto-instrument FastAPI app for OpenTelemetry tracing."""
    if not OTEL_AVAILABLE:
        return
    FastAPIInstrumentor.instrument_app(app)
    logger.info("FastAPI auto-instrumented for OpenTelemetry")


def instrument_sqlalchemy(engine: Any) -> None:
    """Auto-instrument SQLAlchemy for query tracing."""
    if not OTEL_AVAILABLE:
        return
    SQLAlchemyInstrumentor().instrument(engine=engine.sync_engine)
    logger.info("SQLAlchemy instrumented for OpenTelemetry")


def instrument_httpx() -> None:
    """Auto-instrument httpx HTTP client for provider tracing."""
    if not OTEL_AVAILABLE:
        return
    HTTPXClientInstrumentor().instrument()
    logger.info("httpx instrumented for OpenTelemetry")


# ── Manual Span Helpers ──────────────────────────────────────────────────────

def tracer() -> Any | None:
    """Get the current tracer for manual span creation."""
    if not OTEL_AVAILABLE:
        return None
    return trace.get_tracer("mma-backend")


@contextmanager
def span(name: str, **attributes: Any) -> Iterator[None]:
    """Context manager for manual spans.

    Usage:
        with span("sync.fighters", provider="espn"):
            await sync_fighters()
    """
    t = tracer()
    if t is None:
        yield
        return

    with t.start_as_current_span(name) as s:
        for k, v in attributes.items():
            s.set_attribute(k, str(v))
        yield
