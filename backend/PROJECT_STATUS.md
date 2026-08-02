# PROJECT_STATUS.md

**Last updated:** 2026-08-02
**Repository:** MMA Backend

---

## Milestone Progress

| Phase | Name | Status | Date Completed | Artifacts |
|---|---|---|---|---|
| Phase 0 | Project Foundation (Architecture) | ✅ Complete | 2026-08-01 | `backend/ARCHITECTURE.md` |
| Phase 1 | Database Design | ✅ Complete | 2026-08-01 | `backend/DATABASE_DESIGN.md` |
| Phase 2 | ESPN Data Layer | ✅ Complete | 2026-08-01 | `backend/src/providers/` |
| Phase 3 | Sync Engine | ✅ Complete | 2026-08-02 | `backend/src/sync/` |
| Phase 4 | Repository Layer | ✅ Complete | 2026-08-02 | `backend/src/db/repositories/` |
| Phase 5 | Service Layer | ✅ Complete | 2026-08-02 | `backend/src/services/` |
| Phase 6 | REST API | ✅ Complete | 2026-08-02 | `backend/src/api/v1/` |
| Phase 7 | Advanced API | ✅ Complete | 2026-08-02 | `backend/src/api/v1/other.py`, `backend/src/api/v1/search.py` |
| Phase 8 | Notifications | ✅ Complete (v1 routes) | 2026-08-02 | `backend/src/api/v1/notifications.py` |
| Phase 9 | Authentication | ✅ Complete (v1 routes/services) | 2026-08-02 | `backend/src/api/v1/auth.py`, `backend/src/auth/` |
| Phase 10 | Redis Caching | ⚠️ Partial | — | `backend/src/middleware/cache.py` (in-memory abstraction present; Redis wiring not finalized) |
| Phase 11 | Testing | ✅ Active | 2026-08-02 | `backend/tests/` |
| Phase 12 | Production | ⏳ In progress | — | health/metrics/monitoring scaffolding in `backend/src/monitoring/` |

---

## Architecture Decisions

### ADR-001: Provider-First Architecture
**Date:** 2026-08-01
**Decision:** Every data source implements `BaseDataProvider` Protocol. ESPN is the first implementation, not the only one. `ProviderRegistry` maps promotion slugs to provider instances.
**Rationale:** Adding ONE Championship, PFL, Tapology, etc. should require zero changes to services or repositories.

### ADR-002: Event-Driven Notifications
**Date:** 2026-08-01
**Decision:** Internal pub/sub event bus. Notification channels (Push, Email, Telegram, Discord, WebSocket) are plugins implementing `BaseNotificationChannel`.
**Rationale:** Adding a new delivery channel should require one new file, no business logic changes.

### ADR-003: Transparent Redis Cache
**Date:** 2026-08-01
**Decision:** `CacheManager` abstraction in `core/cache.py`. Services use `CacheManager` and never know if data came from PostgreSQL or Redis.
**Rationale:** Every expensive query gets cache invalidation + configurable TTL without service-layer awareness.

---

## State Reconciliation (2026-08-02)

This repository has advanced beyond the earlier "Phase 2 only" snapshot. The following capabilities are already implemented and should not be treated as blocked:

- Rankings APIs are live (`/api/v1/rankings`, `/api/v1/rankings/{division}`, `/api/v1/rankings/p4p`, gender splits).
- Broadcast data model + sync upserts are implemented (`src/db/models/core.py`, `src/sync/upserts/broadcast.py`, ESPN broadcast parser/job).
- Competition-level status/result handling is implemented in competition parsing + upserts and exposed via event/fight endpoints.
- Live and high-frequency event synchronization flows are implemented (`events_live`, `results`, `events_upcoming` job definitions).
- Weight-class parsing, DTO flow, persistence, and sync upserts are implemented (`weight_class` parser/job/upsert path).
- Scheduler execution is implemented with lock-aware APScheduler orchestration, misfire/coalesce/max_instances controls, manual trigger support, and run history (`src/sync/scheduler.py`).

### ADR-004: Modular Sync Jobs
**Date:** 2026-08-01
**Decision:** Each sync job (fighters, events, rankings, etc.) is independently runnable. Scheduler only orchestrates — no business logic.
**Rationale:** Debug individual jobs, coordinate via DB locks for horizontal scaling.

### ADR-005: Provider-Neutral External IDs
**Date:** 2026-08-01
**Decision:** Single `external_ids` table with `(provider, external_id)` as the lookup key. No `espn_id` column on any domain model.
**Rationale:** When Tapology or Sherdog syncs the same fighter, they add a row to `external_ids` pointing to the same entity UUID — no schema migration needed.

### ADR-006: PostgreSQL Full-Text Search
**Date:** 2026-08-01
**Decision:** Use PostgreSQL's built-in `tsvector` + GIN index for search across fighters, promotions, events, venues. No Elasticsearch.
**Rationale:** Search scope is modest. Eliminates an additional service dependency.

### ADR-007: Observability from Day One
**Date:** 2026-08-01
**Decision:** `sync_jobs` table logs execution time, API calls, records inserted/updated/skipped/errors. Structured JSON logging for production.
**Rationale:** Production debugging without SSH/log access.

---

## Current Focus: Production Readiness

### Delivered (implemented in codebase)
- Provider layer (`src/providers/`) + sync orchestration (`src/sync/`) are implemented.
- Repository + service + REST routing layers are implemented (`src/db/repositories/`, `src/services/`, `src/api/v1/`).
- Rankings, broadcasts, competition result/status flows, live-event polling, and weight-class sync paths are all implemented.
- Lock-aware scheduler execution and run observability are implemented (`src/sync/scheduler.py`, `src/scheduler/`).
- Health, metrics, and monitoring scaffolding are in place (`src/monitoring/`, `src/metrics/`).

### In progress
- Redis cache hardening: move from in-memory cache abstraction to production Redis wiring and invalidation discipline.
- Production hardening pass across configuration, validation, and deployment runbooks.

---

## Next Milestone: Phase 10+ Production Hardening

**Goal:** Complete production readiness without reworking already-shipped sync/API foundations.

**Priority scope:**
- Finalize Redis-backed cache behavior and failure-mode fallback.
- Tighten readiness/operational checks and deployment defaults.
- Keep scheduler locking/overlap guarantees stable under multi-instance deployment.

---

## Product Blueprint Reference

The product blueprint (Flutter app design) lives in `docs/blueprint/`:
- `00_OVERVIEW.md` — Master blueprint overview
- `01_PRD.md` — Product requirements
- `03_DEVELOPMENT_PHASES.md` — Development phases
- `06_DATABASE_ENTITY_MAP.md` — Entity relationship map
- Plus 7 additional documents covering features, screens, navigation, API coverage, data sources, notifications, design system, and product review.

---

## Technical Debt

| Item | Severity | Notes |
|---|---|---|
| Redis integration is partial | High | `src/middleware/cache.py` is still in-memory-first; production Redis behavior needs finalization. |
| Cross-org fighter identity (FIGHT-07) | Medium | External ID groundwork exists; conflict resolution rules still need stronger operational playbooks. |
| Non-UFC organization verification | Medium | UFC paths are strongest; additional orgs still require deeper provider-level verification. |

---

## Environment Setup

*Documented in `backend/.env.example`.*
