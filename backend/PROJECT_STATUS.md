# PROJECT_STATUS.md

**Last updated:** 2026-08-05 (Phase 7 item 5 contract audit complete — 100 routes, 0 phantom mobile paths; 3 new event sub-routes; see `SESSION_STATE.md`)
**Updated again:** 2026-08-06 (milestone "Make the Data Flow + Contract Integrity" T01–T18 COMPLETE — see the appended section below; earlier entries preserved)
**Repository:** MMA Backend — `backend/`
**Stack:** Python 3.12 · FastAPI · SQLAlchemy 2 (async) · SQLite (dev) / PostgreSQL (prod) · Alembic · Pydantic v2 · pytest · ruff · mypy

---

## Quality Gates (2026-08-04)

| Gate | Command (from `backend/`) | Result |
|---|---|---|
| Tests | `python -m pytest -q` | ✅ **339 passed** (319 baseline + 10 champions + 9 migration-coverage + 6 etag/auth + 13 rankings-extras + 7 event-extras) |
| Lint | `python -m ruff check src tests` | ✅ 0 errors |
| Types | `python -m mypy src` | ✅ no issues in 184 source files |
| Migrations | `python -m alembic upgrade head --sql` | ✅ renders clean — 7 `ADD COLUMN synced_at` (rankings excluded), 8 auth tables, 005 type fixes, `duration_ms FLOAT` |
| Contract audit | `api_audit.py` (route vs mobile literal cross-ref) | ✅ **100 endpoints, PHANTOM_COUNT 0** (was 39) |

> Live Postgres `alembic upgrade head` NOT executed in this environment (no Docker/Postgres).
> Verified offline via `--sql` render + SQLite `create_all` coverage tests (`tests/integration/test_migration_coverage.py`).

## Monorepo Status (2026-08-05)

This file governs `backend/` only; the sibling AI packages and mobile were also worked on:

- **AI-module restoration complete**: `prediction/`, `recommendation/`, `intelligence/`,
  `data_platform/` (renamed from `platform/`) + `mobile/features/predictions|recommendations/`
  + `mobile/intelligence/` restored from checkpoint `ff74cd8` (161 files, uncommitted-deletion
  recovery), 11 bugs fixed, per-package `verify.py` green (10/10, 10/10, 6/6, 45/45),
  intelligence pytest 31 passed. The no-AI deletion instructions (`01-instruction-index.md`
  §Delete table, migration-plan Phase 5) are **superseded** by user directive.
- **Mobile bootability**: `mobile/` `tsc --noEmit` = **0 errors** (was 67); 3 npm deps added.
- Backend gates above (319 passed, ruff clean) re-verified after the rename; zero `platform` refs remain.

---

## Phase 7 item 5 — Contract Audit (2026-08-05)

Scripted cross-reference of every backend route vs mobile literal URLs found **39 phantom mobile
paths**; all resolved (details in `SESSION_STATE.md` §7b):

- **Implemented** (real data, tested): `GET /v1/events/{event_id}/fights` (fight card),
  `/v1/events/{event_id}/results` (completed fights, `result_method` present),
  `/v1/events/{event_id}/statistics` (aggregates + `EventStatisticsResponse` schema);
  `_build_fight_items()` helper refactored out of `_event_to_detail`. Tests:
  `tests/api/test_event_extras.py` (7 tests, `asyncio.run` direct-call style).
- **Removed from mobile** (no backend / dead / unreachable): `features/predictions/` (no backend
  predictions router exists), `features/recommendations/` module (backend feed API is real and kept;
  the mobile module was imported but never rendered), events reminders + predictions
  api/hooks/store/components, profile `/v1/me/stats` + `/v1/me/export` calls,
  `/v1/me/devices` register/unregister, dead query files (`watchlist/api/queries.ts`,
  `search/types-and-api.ts`, `events/api/queries.ts`), parallel profile layer.
- **Paths fixed** to real routes: `/v1/fighters/{id}/history`, `/v1/watchlist/events`,
  `/v1/me/favorites`, `/v1/notifications/push-token`.

Re-audit confirms **PHANTOM_COUNT 0**. Full gates re-run green: 339 tests, ruff clean,
mypy clean, mobile tsc 0, expo export bundles web/android/iOS.

---

## Migration-Cleanup Session (2026-08-04)

Fixes applied against the 08-03 target architecture (backend portions of the V10→target migration):

| Item | Change | Verification |
|---|---|---|
| `002_phase6_support.py` duplicate `rankings.synced_at` | rankings removed from syncable-column loop (would fail on fresh DB: DuplicateColumnError) | `--sql` shows 7 synced_at, not 8 |
| `002` `sync_runs.duration_ms` Integer vs Float writes | `sa.Float()` in migration + `Float` on `SyncRun`/`SyncJob` models | `--sql` shows `duration_ms FLOAT` |
| Auth models missing from ORM registry | `004_auth_tables.py` (8 tables) + exports in `src/db/models/__init__.py` | `--sql` 8 CREATE TABLEs; import test passes |
| Type drift | `005_schema_fixes.py`: rankings `source_provider`/`version`/`updated_at`, `updated_at` on 7 support tables, `external_ids.matched_by`, promotions `first_event_date`→String(20), `fanart_urls`→Text, events `time_utc`→String(10) | `--sql` ALTERs present |
| `backend/sync.py` invented SyncPlan API | Rewritten on real `SyncEngine(jobs, statestore)` / `SyncPlan.order` / `engine.execute(plan, provider, db_session, mode)` | `--dry-run` plan build; compile+import OK |
| Scheduler wiring | `src/scheduler/context.py` (SchedulerContext + `build_scheduler_context()`), `src/config.py` `sync_enabled`, lifespan starts SyncManager only when `SYNC_ENABLED=true` (docker-compose), graceful when unset/DB-down | import test passes; settings default false |
| Champions endpoints | `champion_router`: `GET /v1/champions`, `/v1/champions/{division}`, `/history` (empty stub — lineage table not modeled) | 10 tests pass |

**Deferred:** TSDB/Octagon enrichment in sync CLI (ESPN-only), champion lineage table (history endpoint returns `[]`), mobile runtime boot (route files/assets — typecheck-level done 2026-08-05), live Postgres migration apply. **Superseded:** AI module deletions Phase 5 (user revoked — modules restored and kept).

---

## Milestone Progress

| Phase | Name | Status | Artifacts |
|---|---|---|---|
| Phase 0 | Project Foundation (Architecture) | ✅ Complete | `ARCHITECTURE.md`, `DATABASE_DESIGN.md` |
| Phase 1 | Database Design + Migrations | ✅ Complete | `src/db/models/*`, `alembic/versions/001_initial_schema.py`, `002_phase6_support.py`, `003_phase8_performance.py` (13 hot-path indexes) |
| Phase 2 | Multi-Provider Data Layer | ✅ Complete | `src/providers/` — ESPN, TSDB, Octagon |
| Phase 3 | Sync Engine | ✅ Complete | `src/sync/` (30 modules), `src/sync/upserts/` (10 entities) |
| Phase 4 | Repository Layer | ✅ Complete | `src/db/repositories/*`, `src/db/unit_of_work.py` |
| Phase 5 | Service Layer | ✅ Complete | `src/services/` — `FighterService`, `EventService`, `AuthService` |
| Phase 6 | REST API (v1) | ✅ Complete | `src/api/` — 10 routers + sync admin + health |
| Phase 7 | Scheduler | ✅ Complete | `src/scheduler/` (10 modules) |
| Phase 8 | Notifications | ⏳ Stub | `src/sync/events.py` event bus; channel plugins pending |
| Phase 9 | Authentication | ✅ Complete | `src/auth/` — JWT, Argon2, RBAC |
| Phase 10 | Redis Caching | ✅ Complete | `src/middleware/cache.py` (memory + Redis backends, degrade-to-serve-through), `src/api/etag.py` (ETag/304), `src/api/cache.py` (cache-aside on hot routes), `src/sync/cache_invalidation.py` (sync→cache busting) |
| Phase 11 | Testing | ✅ Complete | 294 tests across `tests/{unit,integration,api,auth,scheduler,contract}` |
| Phase 12 | Production Hardening | 🔄 In Progress | Observability, health, Docker present; ETag/cache + indices done, scheduler/Redis tuning pending |

---

## Current Architecture

```
backend/
├── src/
│   ├── api/            FastAPI app, v1 routers (auth, events, fighters, fights,
│   │                   notifications, recommendations, search, users, watchlist), sync admin
│   ├── auth/           JWT tokens, Argon2 password hashing, RBAC (roles/permissions), dependencies
│   ├── db/             SQLAlchemy async engine, session, UnitOfWork, repositories,
│   │   │               models (core, event, fighter, support, auth)
│   │   └── models/     ORM: Promotion, Venue, WeightClass, Ranking, Broadcast, Statistic,
│   │                   Fighter, Event, Competition, Competitor, User, Notification, ...
│   ├── dependencies/   FastAPI DI: pagination, sorting, get_uow, get_session
│   ├── domain/models/  Domain-layer re-export shims over ORM models
│   ├── features/       Feature flags
│   ├── logging/        Structured JSON logging config + request middleware
│   ├── metrics/        Prometheus registry + HTTP metrics
│   ├── middleware/     Auth, in-memory cache manager, rate limit
│   ├── monitoring/     Health checks, alerts, DB/provider monitors, exception tracker,
│   │                   config validator, scheduler metrics
│   ├── providers/      BaseDataProvider protocol, ProviderRegistry, provider-neutral DTOs
│   │   ├── espn/       HTTP client (rate limit, backoff, circuit breaker), $ref resolver,
│   │   │               9 parsers, 9 sync jobs, full provider
│   │   ├── tsdb/       Client, config, parsers, provider, sync jobs (partial coverage)
│   │   └── octagon/    Client, config, parsers (fighter, ranking), provider, jobs
│   ├── scheduler/      APScheduler-based: manager, jobs, queue, locks (Redis-ready),
│   │                   retry, cleanup, monitor, metrics, notifier, live-mode
│   ├── schemas/        Pydantic v2 response/request models (common, event, fighter, misc)
│   ├── services/       FighterService, EventService, AuthService
│   ├── sync/           Sync engine: pipeline, plans, strategy (full/incremental/resume),
│   │   │               upsert engine (idempotent per entity), merge engine, id resolver,
│   │   │               checkpoints, conflicts, dead-letter, retry policies, circuit breaker,
│   │   │               failure classifier, state store, observability (metrics/health/alerts)
│   │   └── upserts/    10 entity upserts (fighter, event, competition, competitor,
│   │                   promotion, venue, weight_class, ranking, broadcast, statistics)
│   └── telemetry/      Tracer setup (OpenTelemetry-ready)
├── alembic/            env + 3 migrations (initial schema, phase-6 support tables, phase-8 performance indexes)
├── tests/              294 tests (unit, integration, api, auth, scheduler, contract)
├── scripts/            Operational verification scripts
├── docs/               RUNBOOK, OPERATIONS, INCIDENT_RESPONSE, PERFORMANCE
├── Dockerfile          App image (uvicorn + scheduler)
├── docker-compose.yml  App + PostgreSQL (+ Redis on Phase 1)
├── .env.example        Environment template
└── PROJECT_STATUS.md   This file
```

## Architecture Decisions (carried forward)

- **ADR-001 Provider-First:** every data source implements `BaseDataProvider`; `ProviderRegistry` maps promotion slugs → providers. Adding ONE/PFL requires zero service/repo changes.
- **ADR-002 Event-Driven Notifications:** internal pub/sub `SyncEventBus`; delivery channels are plugins (stub).
- **ADR-003 Transparent Cache:** `CacheManager` abstraction — services never know if data came from Postgres or Redis. `build_cache_manager()` picks Redis when `REDIS_URL` is configured, memory otherwise; both wrappers degrade to cache-miss on backend failure. Endpoints get cache-aside (TTLs per `docs/PERFORMANCE.md`) + content-hash ETags; the sync engine busts the affected prefixes after every completed run.
- **ADR-004 Modular Sync Jobs:** each entity job independently runnable; scheduler only orchestrates; DB/Redis locks coordinate horizontal scaling.
- **ADR-005 Provider-Neutral IDs:** `(provider, external_id)` lookup via per-entity unique constraints (`uq_*_provider_external`) — no provider-specific columns on domain models.
- **ADR-006 Full-Text Search:** PostgreSQL `tsvector` + GIN planned; current search is SQL `LIKE` over name/date fields.
- **ADR-007 Observability from Day One:** sync runs/jobs logged with timing, rows inserted/updated/skipped/errors; structured JSON logs; Prometheus metrics + health endpoints.

## Sync Engine — Key Properties

- Idempotent upserts per entity (insert-on-conflict, `provider_external` key) — re-runs converge.
- Full / incremental / resume strategies; checkpoints enable crash-resume.
- Dependency-ordered pipeline (promotions → venues → weight classes → fighters → events → competitions → rankings → statistics → broadcasts).
- Reliability layer: exponential backoff, circuit breaker, dead-letter queue, failure classification.
- Observability: `SyncMetrics`, `HealthChecker`, `AlertManager`, structured logging per job/run.

## API Surface (v1)

`/api/v1/events` (+`/upcoming` `/live` `/past` `/{id}`), `/api/v1/fighters`, `/api/v1/fights`, `/api/v1/search`, `/api/v1/recommendations`, `/api/v1/notifications`, `/api/v1/users`, `/api/v1/watchlist`, `/api/v1/auth` (register/login/refresh), `/api/scheduler/*` (admin), `/health` + `/health/live` (Docker/K8s).

Auth: JWT access/refresh tokens, Argon2 hashing, role hierarchy (admin > premium > user), permission-based guards, resource-owner checks.

## Testing

294 tests: unit (repositories, cache, etag, api-cache, sync invalidation), integration (parsers vs fixtures, transactions, integrity, resume, recovery, failure injection, production smoke), API (endpoints, contract), auth (unit + e2e flows), scheduler (all). Runs green against SQLite in-memory.

## Next Milestone: Redis Caching + Production Hardening

**Goal (deliverables-2026-08-02):** Redis-backed transparent cache (ADR-003) with TTLs, key design, invalidation; scheduler hardening; observability completeness; health/readiness; performance (indices, pagination, ETags); config validation; Docker/Compose polish; docs refresh.

**Scope (Phases 1–8):**
1. ~~Redis cache — CacheManager Redis backend, key schema, TTLs, invalidation on sync/upsert, graceful degradation~~ ✅ Done — `RedisCacheManager` (serve-through on outage), cache-aside on 16 endpoints with per-route TTLs, ETag/304 (FTR-2205), sync→cache invalidation via `after_sync` event. Tests: `fakeredis`-style FakeRedis + memory backends.
2. Scheduler hardening — lock/queue Redis integration, jitter, missed-run policy.
3. Observability — Prometheus metric completeness, request metrics, tracing.
4. Health endpoints — `/health` deep checks (DB, providers, Redis, scheduler).
5. ~~Performance — DB indices, N+1 audit, response caching, ETag/304~~ ✅ Partially done — migration `003` (13 hot-path indexes), response caching + ETag/304 on all read routes; N+1 audit still open.
6. Config validation — pydantic-settings schema + startup validation.
7. Docker — compose with Redis, healthchecks, non-root.
8. Docs — RUNBOOK/OPERATIONS refresh + this file.

**Blockers:** None. (Live `alembic upgrade head` against Postgres pending — no Docker daemon/Postgres running in this environment; migration SQL verified offline.)

## Technical Debt

| Item | Severity | Notes |
|---|---|---|
| Migration 003 not yet applied to live DB | Medium | SQL verified offline (`alembic upgrade head --sql`); needs one Postgres run |
| Scheduler Redis lock/queue not integrated | Medium | `src/scheduler/` is Redis-ready; wiring pending |
| Notifications channels | Medium | Event bus exists; push/email/telegram/discord/WS plugins pending |
| SQLite in dev vs Postgres prod | Medium | CI runs SQLite; some SQL (tsvector, upsert constraint syntax) Postgres-specific |
| AI/analytics sibling dirs (`intelligence/`, `prediction/`, `recommendation/`, `data_platform/`) | Low | Vendored extras, not part of backend deliverable; un-declared deps (numpy, scikit-learn, xgboost, joblib); each ships a green `verify.py` + intelligence pytest 31 passed |
| Non-UFC org verification | Medium | Only UFC verified end-to-end; `scripts/verify_additional_organizations.py` |
| pyproject `tests.*` mypy override unused | Low | Tests excluded from mypy; harmless note |

## Environment

`backend/.env.example` — DATABASE_URL, JWT secrets, provider endpoints/keys, scheduler interval, Redis URL (Phase 1), feature flags. Run tests with SQLite defaults; no external services required.

---

## Milestone T01–T18 — "Make the Data Flow + Contract Integrity" (2026-08-06, COMPLETE)

Appended at milestone close; the sections above (2026-08-04/05) remain historical. Full detail
in the root docs: `PROJECT_STATE.md`, `SESSION_STATE.md`, `EXECUTION_PLAN.md`, `PLAN_HISTORY.md`
(08-05 + 08-06 freeze entries). This file covers the backend only; mobile T16/T17 work is
recorded in the root docs.

### What changed in the backend this milestone

1. **Sync write path fixed + proven live (T01–T05):** `BaseUpsert` fills NOT NULL
   `provider`/`external_id`; ESPN pagination re-driven by the probe-proven `limit`+`page`
   contract; FK enrichment for event/competition/fighter; engine per-job commits with
   `sync_runs`/`sync_jobs`; promotion external_id = slug `"ufc"`; ranking job iterates
   promotions; broadcast job fetches events first; ranking upsert sets `provider`.
   **Live acceptance:** 9/9 jobs COMPLETED, promotions 48, fighters 1829 (full pool),
   rankings 110 rows, sync_runs 1.
2. **Degradation (T06–T07):** `/api/scheduler/status` → 503 without Redis; `RedisLock`
   never raises when Redis is unreachable.
3. **Real user data (T08–T10):** favorites DB-backed; preferences persisted
   (`UserPreference`); duplicate notifications router stubs deleted (fixed `/v1/notifications`
   → `[]` and `/read-all` no-op shadowing).
4. **Contract integrity (T11–T15):** pagination shape `{items,total,page,limit,pages}` pinned
   (7 contract tests); `require_uuid()` 404 guards on all 18 UUID `{id}` routes (15 tests);
   **`/v1/weight-classes` + `/{id}`** (FTR-701/702 — table was empty; `_ensure_weight_class()`
   now materializes divisions from inline ESPN data: 14 divisions, 1828 fighters linked);
   **`/v1/fighters/{id}/next-fight`** (FTR-107, `NextFight | null`, 15-min TTL);
   **`/v1/compare?a=&b=`** (FTR-1905/1906/1907 — summaries + head-to-head + common opponents).
5. **Mobile contract alignment (T16–T17, mobile):** base URL un-faked; TS models re-derived
   snake_case from backend schemas (see root docs).

### Current quality gates (final, 2026-08-06)

| Gate | Command (from `backend/`) | Result |
|---|---|---|
| Tests | `python -m pytest -q` | ✅ **419 passed, 1 skipped** (env-gated live sync test) |
| Lint | `python -m ruff check src` | ✅ clean |
| Types | `python -m mypy src` | ✅ no issues in 186 source files |
| Migrations | `alembic upgrade head` on live Postgres | ✅ applied 001→005, 27 tables (2026-08-05) |
| Live sync acceptance | `MMA_LIVE_SYNC=1` (env-gated test) | ✅ PASSED ~4 min (T05); re-run 1831 fighters, 14 weight classes (T13) |
| Mobile (sibling) | `npx tsc --noEmit` + `npx expo export --platform web` | ✅ 0 errors; bundled OK |

Historical counts above (339 → 360 → 374 → 404 → 411 → 419) document the growth; the current
baseline is **419 passed, 1 skipped**.

### Live environment notes (still valid)

PostgreSQL 18 service `postgresql-x64-18` running locally: role/db `mma`/`mma` (superuser
`postgres:REDACTED` — never commit). URL `postgresql+asyncpg://mma:mma@localhost:5432/mma`.
Scheduler/live tests require `MMA_LIVE_SYNC=1`; normal pytest stays offline (SQLite).

### Repository state at close

HEAD `d3ecc68`; the entire T01–T18 working tree is **uncommitted** (~83 files). Commit only on
user request. Next work: Backlog items in `EXECUTION_PLAN.md` §Backlog.
