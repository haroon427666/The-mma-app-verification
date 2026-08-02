"""Structured JSON Logging — correlation IDs, request context, sampling.

Every log line is a JSON object with:
- timestamp, level, message
- request_id, correlation_id (traces requests end-to-end)
- user_id, provider, sync_run_id (when available)
- duration_ms, endpoint, status_code (when applicable)
"""

import json
import logging
import time
import uuid
from contextvars import ContextVar
from datetime import datetime, timezone
from typing import Any, Optional

# ── Context Variables (thread-safe, async-safe) ──────────────────────────

request_id_var: ContextVar[str] = ContextVar("request_id", default="")
correlation_id_var: ContextVar[str] = ContextVar("correlation_id", default="")
user_id_var: ContextVar[str] = ContextVar("user_id", default="")
sync_run_id_var: ContextVar[str] = ContextVar("sync_run_id", default="")
provider_var: ContextVar[str] = ContextVar("provider", default="")


def set_request_id(rid: str | None = None) -> str:
    val = rid or f"req_{uuid.uuid4().hex[:12]}"
    request_id_var.set(val)
    correlation_id_var.set(val)
    return val


def set_correlation_id(cid: str) -> None:
    correlation_id_var.set(cid)


def set_user(uid: str) -> None:
    user_id_var.set(uid)


def set_sync_run(sid: str) -> None:
    sync_run_id_var.set(sid)


def set_provider(provider: str) -> None:
    provider_var.set(provider)


# ── JSON Formatter ───────────────────────────────────────────────────────

class JsonFormatter(logging.Formatter):
    """Produces JSON log lines with contextual metadata."""

    RESERVED = {"timestamp", "level", "logger", "message", "module", "function", "line"}

    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "line": record.lineno,
        }

        # Inject context variables
        if rid := request_id_var.get():
            log_entry["request_id"] = rid
        if cid := correlation_id_var.get():
            log_entry["correlation_id"] = cid
        if uid := user_id_var.get():
            log_entry["user_id"] = uid
        if sid := sync_run_id_var.get():
            log_entry["sync_run_id"] = sid
        if prov := provider_var.get():
            log_entry["provider"] = prov

        # Exception info
        if record.exc_info and record.exc_info[1]:
            log_entry["exception"] = {
                "type": type(record.exc_info[1]).__name__,
                "message": str(record.exc_info[1]),
            }

        # Extra fields from `logger.info("msg", extra={...})`
        for key, val in record.__dict__.items():
            if key not in self.RESERVED and not key.startswith("_"):
                log_entry[key] = val

        return json.dumps(log_entry, default=str)


# ── Config ───────────────────────────────────────────────────────────────

def configure_logging(level: str = "INFO", json_output: bool = True):
    """Configure root logger with JSON formatting."""
    root = logging.getLogger()
    root.setLevel(getattr(logging, level.upper(), logging.INFO))

    # Remove existing handlers
    for h in root.handlers[:]:
        root.removeHandler(h)

    handler = logging.StreamHandler()
    if json_output:
        handler.setFormatter(JsonFormatter())
    else:
        handler.setFormatter(logging.Formatter(
            "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
        ))

    root.addHandler(handler)

    # Silence noisy libraries
    for lib in ("uvicorn.access", "httpx", "apscheduler"):
        logging.getLogger(lib).setLevel(logging.WARNING)
