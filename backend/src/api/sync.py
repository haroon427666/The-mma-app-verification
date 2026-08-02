"""Admin API — sync management and scheduler dashboard.

Routes added to the FastAPI app at startup.
Provides manual control over sync jobs, plus live status dashboard.

Endpoints:
    GET    /scheduler/status          — Full dashboard: jobs, queue, health
    GET    /scheduler/jobs             — List all scheduled jobs
    GET    /scheduler/metrics          — Prometheus metrics export
    POST   /sync/full                  — Trigger full sync
    POST   /sync/{entity}              — Trigger entity-specific sync
    POST   /sync/cancel/{job_name}     — Cancel queued job
    POST   /sync/retry/{job_name}      — Retry a failed job
"""

import logging
from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel

from src.auth.dependencies import require_permission, get_current_user, TokenPayload

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/scheduler", tags=["scheduler"])

# Module-level reference to the SyncManager — set at startup
_manager = None


def set_sync_manager(manager):
    global _manager
    _manager = manager


def get_manager():
    if _manager is None:
        raise HTTPException(503, "SyncManager not initialized")
    return _manager


# ── Dashboard ──────────────────────────────────────────────────────────────────

@router.get("/status")
async def scheduler_status():
    """Full scheduler dashboard — jobs, queue, health, locks, live mode."""
    manager = get_manager()
    return await manager.get_status()


@router.get("/jobs")
async def list_jobs():
    """List all configured sync jobs with their schedules."""
    from src.scheduler.jobs import JOB_REGISTRY
    return {
        "jobs": [
            {
                "name": name,
                "description": cfg.description,
                "interval_seconds": cfg.interval_seconds,
                "cron": cfg.cron,
                "enabled": cfg.enabled,
                "max_runtime": cfg.max_runtime_seconds,
            }
            for name, cfg in JOB_REGISTRY.items()
        ]
    }


@router.get("/metrics")
async def scheduler_metrics():
    """Export Prometheus-compatible metrics."""
    from src.scheduler.metrics import metrics
    from fastapi.responses import PlainTextResponse
    return PlainTextResponse(metrics.export_prometheus(), media_type="text/plain")


# ── Sync Controls ──────────────────────────────────────────────────────────────

class SyncRequest(BaseModel):
    entities: list[str] | None = None  # None = all
    mode: str = "full"


@router.post("/sync/full")
async def trigger_full_sync(
    req: SyncRequest,
    user: TokenPayload = Depends(require_permission("sync.run")),
):
    """Manually trigger a full sync."""
    manager = get_manager()
    run_id = await manager.trigger_full_sync(entities=req.entities)
    return {"status": "accepted", "run_id": run_id, "entities": req.entities or "all"}


@router.post("/sync/{entity}")
async def trigger_entity_sync(
    entity: str,
    user: TokenPayload = Depends(require_permission("sync.run")),
):
    """Trigger sync for a specific entity."""
    manager = get_manager()
    try:
        run_id = await manager.trigger_entity_sync(entity)
        return {"status": "accepted", "entity": entity}
    except ValueError as e:
        raise HTTPException(400, str(e))


@router.post("/sync/cancel/{job_name}")
async def cancel_job(
    job_name: str,
    user: TokenPayload = Depends(require_permission("sync.cancel")),
):
    """Cancel all queued instances of a job."""
    manager = get_manager()
    count = await manager.cancel_job(job_name)
    return {"status": "cancelled", "job_name": job_name, "removed": count}


@router.post("/sync/retry/{job_name}")
async def retry_job(
    job_name: str,
    user: TokenPayload = Depends(require_permission("sync.run")),
):
    """Re-enqueue a failed job for immediate retry."""
    from src.scheduler.jobs import JOB_FUNCTIONS
    from src.scheduler.queue import Priority

    fn = JOB_FUNCTIONS.get(job_name)
    if fn is None:
        raise HTTPException(400, f"Unknown job: {job_name}")

    manager = get_manager()
    await manager.queue.enqueue(job_name, fn, priority=Priority.HIGH)
    return {"status": "retrying", "job_name": job_name}
