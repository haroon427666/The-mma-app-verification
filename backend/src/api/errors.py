"""Global error handling — RFC7807 Problem Details format.

Consistent error schema across every endpoint:
{
  "type": "https://mma-api.example.com/errors/not-found",
  "title": "Fighter not found",
  "status": 404,
  "detail": "No fighter found for: abc-123",
  "instance": "/api/v1/fighters/abc-123",
  "request_id": "req_abc123",
  "timestamp": "2026-08-01T12:00:00Z"
}
"""

import logging
from datetime import datetime, timezone
from typing import Optional, Any

from fastapi import Request
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)


class ProblemDetail(Exception):
    """Base domain exception — all service errors inherit from this."""

    def __init__(
        self,
        title: str,
        status: int = 500,
        detail: str = "",
        error_type: str = "about:blank",
        instance: str = "",
        extensions: dict[str, Any] | None = None,
    ):
        self.title = title
        self.status = status
        self.detail = detail
        self.error_type = error_type
        self.instance = instance
        self.extensions = extensions or {}


# ═══════════════════════════════════════════════════════════════════════════
# Domain Exceptions
# ═══════════════════════════════════════════════════════════════════════════

class NotFoundError(ProblemDetail):
    def __init__(self, entity: str, identifier: str = ""):
        super().__init__(
            title=f"{entity} not found",
            status=404,
            detail=f"No {entity.lower()} found{f' for: {identifier}' if identifier else ''}",
            error_type=f"https://mma-api.example.com/errors/not-found",
        )


class ValidationError(ProblemDetail):
    def __init__(self, detail: str, field: str | None = None):
        extensions = {}
        if field:
            extensions["field"] = field
        super().__init__(
            title="Validation error",
            status=422,
            detail=detail,
            error_type="https://mma-api.example.com/errors/validation",
            extensions=extensions,
        )


class AuthenticationError(ProblemDetail):
    def __init__(self, detail: str = "Not authenticated"):
        super().__init__(
            title="Authentication required",
            status=401,
            detail=detail,
            error_type="https://mma-api.example.com/errors/authentication",
        )


class AuthorizationError(ProblemDetail):
    def __init__(self, detail: str = "Insufficient permissions"):
        super().__init__(
            title="Access denied",
            status=403,
            detail=detail,
            error_type="https://mma-api.example.com/errors/authorization",
        )


class ConflictError(ProblemDetail):
    def __init__(self, detail: str, entity: str = ""):
        super().__init__(
            title="Resource conflict",
            status=409,
            detail=detail,
            error_type="https://mma-api.example.com/errors/conflict",
        )


class RateLimitError(ProblemDetail):
    def __init__(self, retry_after: int = 60):
        super().__init__(
            title="Too many requests",
            status=429,
            detail=f"Rate limit exceeded. Retry after {retry_after}s",
            error_type="https://mma-api.example.com/errors/rate-limit",
            extensions={"retry_after": retry_after},
        )


class SyncError(ProblemDetail):
    def __init__(self, detail: str, provider: str = ""):
        extensions = {}
        if provider:
            extensions["provider"] = provider
        super().__init__(
            title="Sync failed",
            status=502,
            detail=detail,
            error_type="https://mma-api.example.com/errors/sync",
            extensions=extensions,
        )


class ExternalAPIError(ProblemDetail):
    def __init__(self, detail: str, provider: str, status_code: int | None = None):
        super().__init__(
            title=f"{provider} API error",
            status=502,
            detail=detail,
            error_type="https://mma-api.example.com/errors/external-api",
            extensions={"provider": provider, "provider_status": status_code},
        )


class DatabaseError(ProblemDetail):
    def __init__(self, detail: str = "Database unavailable"):
        super().__init__(
            title="Service unavailable",
            status=503,
            detail=detail,
            error_type="https://mma-api.example.com/errors/database",
        )


# ═══════════════════════════════════════════════════════════════════════════
# Response Builder
# ═══════════════════════════════════════════════════════════════════════════

def build_problem_response(
    exc: ProblemDetail,
    request: Request,
    request_id: str = "",
) -> JSONResponse:
    """Build an RFC7807 Problem Details JSON response."""
    body = {
        "type": exc.error_type,
        "title": exc.title,
        "status": exc.status,
        "detail": exc.detail,
        "instance": str(request.url),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    if request_id:
        body["request_id"] = request_id
    if exc.extensions:
        body.update(exc.extensions)

    return JSONResponse(
        status_code=exc.status,
        content=body,
        headers={
            "Content-Type": "application/problem+json",
            "X-Request-ID": request_id,
        } if request_id else {"Content-Type": "application/problem+json"},
    )


async def problem_detail_handler(request: Request, exc: ProblemDetail) -> JSONResponse:
    """FastAPI exception handler for ProblemDetail."""
    request_id = getattr(request.state, "request_id", "")
    return build_problem_response(exc, request, request_id)


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Catch-all for unhandled exceptions. Logs full traceback, returns 500."""
    logger.exception(f"Unhandled exception at {request.url.path}")
    problem = ProblemDetail(
        title="Internal server error",
        status=500,
        detail="An unexpected error occurred",
        error_type="https://mma-api.example.com/errors/internal",
    )
    return await problem_detail_handler(request, problem)
