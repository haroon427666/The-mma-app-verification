# Continuation prompt for Claude — paste everything below this line

---

We're resuming the **MMA backend** project. You were mid-way through the **Production Readiness** milestone and the session was cut off during Phase 1 (Redis caching), at the cache-layer **design stage** — before any cache code was committed. I've since verified the exact state of the repo. Read this carefully before writing anything; **do not re-derive state from `PROJECT_STATUS.md` — that file is stale and I'll tell you how below.**

## Verified current state (re-checked by running the code, 2026-07-30)

- **Green baseline:** `pytest` → **48 passed, 91% coverage** against a real PostgreSQL; `ruff check .` → clean; `mypy app` (strict) → no issues in 60 files. Keep all three green at every step.
- **`PROJECT_STATUS.md` is OUT OF DATE.** It's stamped "end of Milestone 3.5" and claims rankings, broadcasts, competition-level status, live-event sync and weight-class sync are "blocked / deliberately not built." **They are all already implemented in the code** (`sync_rankings`, `sync_event_broadcasts`, `_apply_competition_status`, `sync_live_events`, `sync_known_fighters`, `_upsert_weight_class`, the `Ranking`/`Broadcast` models, migration `08cc277c877c`, and the 4-tier scheduler). There was an unlogged milestone between 3.5 and the Redis attempt. The test count is 48, not 40.
- **Redis caching = nothing committed yet.** There is no `app/core/cache.py`, no `import redis` anywhere in `app/`, no cache decorator on any route/service, and no cache tests. The only Redis artifacts are pre-existing scaffolding: the `redis>=5.1.1` dep in `pyproject.toml`, `REDIS_URL` in `app/core/config.py`, the `redis` service in `docker-compose.yml`, and the `.env.example` line. So **start Phase 1 clean — there is no half-built cache code to reconcile.**

## Non-negotiable engineering standards (already established in this repo — match them exactly)

1. **Strict layering:** routes stay thin; **services** hold business logic; **repositories** hold all SQL. Routes never touch the DB; repositories never hold business rules; services never know about HTTP. **Slot caching in at the service/route boundary — do NOT smear Redis calls through repositories.**
2. **Dependency injection** via `app/api/v1/dependencies.py`, overridable in tests through `app.dependency_overrides`. The cache client must be injected the same way so tests can swap it.
3. **Tests:** DB tests run against **real Postgres** (see `tests/conftest.py`, SAVEPOINT-per-test). External I/O is faked, never hit live. For Redis, **use `fakeredis`** so CI stays hermetic — do not require a running Redis in the test suite.
4. **`ruff` + `mypy --strict` must stay green.** Full typing, PEP 695 generics, Python 3.12.
5. **Scheduler invariant:** every job opens and closes its own `Session` + `ESPNClient` (APScheduler thread pool). Preserve this in any scheduler work.
6. **Migrations:** Alembic autogenerate, but always hand-read the generated file before applying. Zero-drift is the standard (`alembic check`).
7. **Doc discipline:** `PROJECT_STATUS.md` is the declared source of truth, updated at the end of every milestone.

## What I want you to do, in order

**Task 0 — Re-sync `PROJECT_STATUS.md` FIRST (small but mandatory).** Before any Redis work, correct the doc so it reflects reality: rankings/broadcasts/competition-status/live-sync/weight-class are implemented; scheduler is 4-tier; test count is 48; coverage 91%. This prevents every future session from being misled. Keep it factual and concise — don't rewrite the whole file, just fix the wrong claims and move those items from "blocked/not built" to "done."

Then proceed through the Production Readiness phases. Do them one phase at a time; after each, run the full test+lint+type gate and pause for my review before the next.

**Phase 1 — Redis caching (this is where we were cut off; start here after Task 0).**
- Add a small cache client wrapper in `app/core/cache.py`, injected via `dependencies.py`, TTL-configurable from settings (reuse the existing `REDIS_URL`; add cache TTL settings).
- Apply **cache-aside** to the hot read paths: fighter detail, `next-fight`, fighter statistics, event detail, and the list endpoints (promotions, venues, events). Pick TTLs per data volatility (next-fight/live-adjacent data short; slow-changing profile/venue data longer) and document the reasoning inline, matching the commentary style already in the repo.
- Add **invalidation hooks** in the sync layer (`espn_sync.py`) so that when an entity is re-synced, its cached representation is busted. Account for the cross-entity cases the old status doc flagged (e.g. a fighter's `weightClass`/ranking changing).
- **Graceful degradation:** if Redis is unreachable, endpoints must fall back to the DB and log, never 500. Add a test for that path.
- Tests with `fakeredis`: hit (cached), miss (populates), invalidation-on-sync, and Redis-down fallback. Keep coverage at/above current.

**Phase 2 — Scheduler optimisation.** Add a locking/job-store strategy so running multiple app instances doesn't double-fire jobs (this matters on Render once there's >1 worker/instance). Review coalesce/misfire/overlap. Emit per-tier run metrics. Preserve the per-job Session/Client invariant.

**Phase 3 — Observability.** Structured request logging + a request-timing middleware (build on the existing `structlog` setup), correlation IDs, and a Prometheus `/metrics` endpoint (request latency/count, scheduler run counts/durations, cache hit/miss ratio from Phase 1).

**Phase 4 — Health monitoring.** Keep `/health` liveness dependency-free. Add `/health/ready` readiness that checks **DB and Redis** (Redis check must degrade gracefully — a down cache is degraded, not dead). 

**Phase 5 — Performance.** Audit N+1s on event-detail and fighter-detail/fights (add eager loading where the relationship traversal shows them), add query timing, sanity-check pagination under load. Back findings with a test or a measurement, not a guess.

**Phase 6 — Configuration hardening.** Production-safe config: enforce `DEBUG=false`, non-wildcard CORS, real secrets in production via the existing `field_validator` pattern; fail fast on misconfig. Per-environment settings.

**Phase 7 — Docker (production).** A production image distinct from the dev compose one: multi-stage build, non-root user, a real WSGI/ASGI server config (uvicorn workers or gunicorn+uvicorn worker), no `--reload`, container healthcheck. Keep the dev `docker-compose.yml` working.

**Phase 8 — Documentation.** Finalise README + `PROJECT_STATUS.md` for the completed Production Readiness milestone: caching strategy + TTLs, observability endpoints, health semantics, prod-vs-dev Docker, config expectations.

## Working agreement
- **Don't rebuild anything already implemented** (rankings, broadcasts, competition status, live/fighter sync, weight-class sync, the 15 read endpoints, the 4-tier scheduler). If you think something's missing, grep the repo and confirm before writing.
- After each phase: run `pytest --cov=app`, `ruff check .`, `mypy app`; report the numbers; then stop and let me review before the next phase.
- Match the existing code's commentary style — the repo explains *why* a decision was made, not just *what*. Keep that.

Start with **Task 0**, then Phase 1. Show me your Phase 1 cache-layer design (where it plugs into the layering, TTL table, invalidation points) before you write the implementation.
