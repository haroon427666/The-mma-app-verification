from src.logging.config import (
    JsonFormatter,
    configure_logging,
    correlation_id_var,
    provider_var,
    request_id_var,
    set_correlation_id,
    set_provider,
    set_request_id,
    set_sync_run,
    set_user,
    sync_run_id_var,
    user_id_var,
)

try:
    from src.logging.middleware import AuditLogMiddleware, RequestContextMiddleware
except ImportError:
    RequestContextMiddleware = None  # type: ignore
    AuditLogMiddleware = None  # type: ignore

__all__ = [
    "AuditLogMiddleware",
    "JsonFormatter",
    "RequestContextMiddleware",
    "configure_logging",
    "correlation_id_var",
    "provider_var",
    "request_id_var",
    "set_correlation_id",
    "set_provider",
    "set_request_id",
    "set_sync_run",
    "set_user",
    "sync_run_id_var",
    "user_id_var",
]
