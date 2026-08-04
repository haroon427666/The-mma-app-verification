"""Telemetry package — OpenTelemetry tracing."""

from src.telemetry.tracer import (
    OTEL_AVAILABLE,
    instrument_app,
    instrument_httpx,
    instrument_sqlalchemy,
    setup_tracing,
    span,
    tracer,
)

__all__ = [
    "OTEL_AVAILABLE",
    "instrument_app",
    "instrument_httpx",
    "instrument_sqlalchemy",
    "setup_tracing",
    "span",
    "tracer",
]
