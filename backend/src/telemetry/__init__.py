"""Telemetry package — OpenTelemetry tracing."""

from src.telemetry.tracer import (
    setup_tracing, instrument_app, instrument_sqlalchemy, instrument_httpx,
    tracer, span, OTEL_AVAILABLE,
)

__all__ = [
    "setup_tracing", "instrument_app", "instrument_sqlalchemy", "instrument_httpx",
    "tracer", "span", "OTEL_AVAILABLE",
]
