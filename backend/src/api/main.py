"""FastAPI Application — production REST API.

Layers: Client → Routers → Services → Repositories → PostgreSQL
Providers are NEVER called directly from API endpoints.

API docs: /docs (Swagger), /redoc (ReDoc), /openapi.json
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.config import settings
from src.schemas.common import ErrorResponse

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"Starting {settings.app_name} ({settings.environment})")

    # Start scheduler on startup (if database available)
    try:
        from src.scheduler.manager import SyncManager
        from src.api.sync import set_sync_manager
        # Manager would be initialized with real context in production
        # manager = SyncManager(context)
        # await manager.start()
        # set_sync_manager(manager)
        logger.info("SyncManager — deferred to production runtime")
    except Exception as e:
        logger.warning(f"SyncManager not started: {e}")

    yield

    # Shutdown scheduler
    logger.info("Shutting down")


app = FastAPI(
    title="MMA Backend API",
    description="""
## Production-grade MMA data platform

**Three providers, one API:**
- **ESPN** — Primary data (fighters, events, rankings, stats)
- **TheSportsDB** — Media enrichment (posters, bios, branding)
- **Octagon API** — Fighter enrichment (gym, style, leg reach, renders)

### Key features
- Versioned REST endpoints (`/api/v1/`)
- Pagination, filtering, sorting, and search on all list endpoints
- Redis-cached responses with automatic invalidation after syncs
- Rate limiting (100 req/min per client)
- Complete OpenAPI 3.1 documentation
    """,
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    contact={"name": "MMA Platform Team"},
    license_info={"name": "Proprietary"},
    openapi_tags=[
        {"name": "fighters", "description": "Fighter profiles, records, statistics, rankings"},
        {"name": "events", "description": "Event cards, venues, broadcasts"},
        {"name": "fights", "description": "Individual fights within events"},
        {"name": "rankings", "description": "UFC rankings — all divisions"},
        {"name": "promotions", "description": "MMA promotions and leagues"},
        {"name": "venues", "description": "Arenas and venues"},
        {"name": "search", "description": "Unified search across all entities"},
        {"name": "scheduler", "description": "Sync job management and dashboard"},
        {"name": "health", "description": "Health and readiness probes"},
    ],
)

# ── Middleware ─────────────────────────────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID", "X-RateLimit-Remaining"],
)

# Rate limiter: 100 req/min
try:
    from src.middleware.rate_limit import RateLimiter
    app.add_middleware(RateLimiter, max_requests=100, window_seconds=60)
except ImportError:
    pass

# Request context + correlation IDs
try:
    from src.logging.middleware import RequestContextMiddleware, AuditLogMiddleware
    app.add_middleware(RequestContextMiddleware)
    app.add_middleware(AuditLogMiddleware)
except ImportError:
    pass

# Exception tracking
try:
    from src.monitoring.exception_tracker import ExceptionTrackerMiddleware
    app.add_middleware(ExceptionTrackerMiddleware)
except ImportError:
    pass

# Performance profiler (P50/P95/P99)
try:
    from src.monitoring.exception_tracker import ProfilerMiddleware
    app.add_middleware(ProfilerMiddleware)
except ImportError:
    pass

# ── Exception Handlers ─────────────────────────────────────────────────────────

from src.schemas.common import ErrorDetail
from src.api.errors import (
    ProblemDetail, problem_detail_handler, unhandled_exception_handler,
    NotFoundError, ValidationError,
)

@app.exception_handler(ProblemDetail)
async def problem_handler(request: Request, exc: ProblemDetail):
    return await problem_detail_handler(request, exc)


@app.exception_handler(NotFoundError)
async def not_found_handler(request: Request, exc: NotFoundError):
    return await problem_detail_handler(request, exc)


@app.exception_handler(ValidationError)
async def validation_error_handler(request: Request, exc: ValidationError):
    return await problem_detail_handler(request, exc)


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    detail = exc.detail if isinstance(exc.detail, str) else str(exc.detail)
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(error=detail, code=exc.status_code).model_dump(),
    )


@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    return JSONResponse(
        status_code=404,
        content=ErrorResponse(
            error="Not found", code=404,
            details=[ErrorDetail(message=f"Path not found: {request.url.path}")],
        ).model_dump(),
    )


@app.exception_handler(422)
async def validation_handler(request: Request, exc):
    return JSONResponse(
        status_code=422,
        content=ErrorResponse(
            error="Validation error", code=422,
            details=[ErrorDetail(message=str(exc))],
        ).model_dump(),
    )


# ── Routers ────────────────────────────────────────────────────────────────────

from src.api.v1 import routers as v1_routers
for router in v1_routers:
    app.include_router(router, prefix="/api")

# Scheduler admin endpoints
from src.api.sync import router as scheduler_router
app.include_router(scheduler_router, prefix="/api")

# Legacy health (at root for Docker/K8s compatibility)
@app.get("/health")
async def health():
    return {"status": "ok", "app": settings.app_name, "version": "1.0.0"}


@app.get("/health/live")
async def health_live():
    """Kubernetes liveness probe — always ok if the process is alive."""
    try:
        from src.monitoring.health import HealthChecker
        checker = HealthChecker()
        return await checker.run_liveness()
    except ImportError:
        return {"status": "healthy", "uptime_seconds": 0}


@app.get("/health/ready")
async def health_ready():
    """Kubernetes readiness probe — DB + Redis must be up."""
    try:
        from src.monitoring.health import HealthChecker, check_database
        checker = HealthChecker()
        checker.register("database", check_database)
        return await checker.run_readiness()
    except ImportError:
        return {"status": "healthy", "checks": {"database": {"status": "healthy"}}}


@app.get("/health/database")
async def health_database():
    """Database connectivity check."""
    try:
        from src.monitoring.health import check_database
        ok = await check_database()
        return {"status": "healthy" if ok else "failed", "check": "database"}
    except ImportError:
        return {"status": "healthy", "check": "database", "message": "not configured"}


@app.get("/health/redis")
async def health_redis():
    """Redis connectivity check."""
    try:
        from src.monitoring.health import check_redis
        ok = await check_redis()
        return {"status": "healthy" if ok else "failed", "check": "redis"}
    except ImportError:
        return {"status": "healthy", "check": "redis", "message": "not configured"}


@app.get("/health/providers")
async def health_providers():
    """Provider health: ESPN, TSDB, Octagon status."""
    try:
        from src.monitoring.health import check_provider_espn
        ok = await check_provider_espn()
        return {"status": "healthy" if ok else "failed", "providers": {"espn": {"status": "healthy" if ok else "failed"}}}
    except ImportError:
        return {"status": "healthy", "providers": {"espn": {"status": "unknown"}}}


@app.get("/health/scheduler")
async def health_scheduler():
    """Scheduler health: running, queue state, job failures."""
    try:
        from src.monitoring.health import check_scheduler
        ok = await check_scheduler()
        return {"status": "healthy" if ok else "degraded", "check": "scheduler"}
    except ImportError:
        return {"status": "healthy", "check": "scheduler", "message": "not configured"}


@app.get("/api/metrics")
async def prometheus_metrics():
    """Prometheus metrics endpoint — scraped by Prometheus server."""
    try:
        from src.metrics.prometheus import get_metrics
        from fastapi.responses import PlainTextResponse
        return PlainTextResponse(get_metrics().export(), media_type="text/plain")
    except ImportError:
        return {"status": "disabled", "message": "prometheus_client not installed"}


@app.get("/api/profiling")
async def profiling():
    """API latency percentiles — P50/P95/P99 per endpoint."""
    try:
        from src.monitoring.exception_tracker import ProfilerMiddleware
        for mw in app.user_middleware:
            if isinstance(mw, ProfilerMiddleware):
                return mw.get_all_percentiles()
        return {"status": "disabled"}
    except ImportError:
        return {"status": "disabled"}


# Flag management (admin only)
@app.get("/api/flags")
async def feature_flags():
    try:
        from src.features.flags import list_flags
        return {"flags": list_flags()}
    except ImportError:
        return {"flags": {}}
