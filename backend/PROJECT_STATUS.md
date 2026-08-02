# PROJECT_STATUS.md

**Last updated:** 2026-08-01
**Repository:** MMA Backend

---

## Milestone Progress

| Phase | Name | Status | Date Completed | Artifacts |
|---|---|---|---|---|
| Phase 0 | Project Foundation (Architecture) | ✅ Approved | 2026-08-01 | `backend/ARCHITECTURE.md` |
| Phase 1 | Database Design | ✅ Approved | 2026-08-01 | `backend/DATABASE_DESIGN.md` |
| Phase 2 | ESPN Data Layer | ✅ Complete | 2026-08-01 | `backend/src/providers/` |
| Phase 3 | Sync Engine | 🔜 Next | — | — |
| Phase 4 | Repository Layer | ⏳ Future | — | — |
| Phase 5 | Service Layer | ⏳ Future | — | — |
| Phase 6 | REST API | ⏳ Future | — | — |
| Phase 7 | Advanced API | ⏳ Future | — | — |
| Phase 8 | Notifications | ⏳ Future | — | — |
| Phase 9 | Authentication | ⏳ Future | — | — |
| Phase 10 | Redis Caching | ⏳ Future | — | — |
| Phase 11 | Testing | ⏳ Future | — | — |
| Phase 12 | Production | ⏳ Future | — | — |

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

## Current Phase Details: Phase 2 (Complete)

### Delivered
- `BaseDataProvider` Protocol — contract for all data providers (14 async methods)
- `ProviderRegistry` — maps promotion slugs to provider instances; zero code changes to add a provider
- Internal DTOs — 10 provider-agnostic dataclasses (`PromotionDTO`, `FighterDTO`, etc.)
- ESPN HTTP client — async httpx client with:
  - Token bucket rate limiter (10 req/s, 15 burst)
  - Exponential backoff retry (3 attempts, 429 + 5xx)
  - Circuit breaker (5 consecutive failures → open for 60s)
  - Configurable timeouts (30s request, 10s connect)
  - Async pagination generator
  - Structured logging per API call
- ESPN `$ref` resolver — cached resolution within a sync run, parallel resolve_all
- 9 response parsers — pure functions: raw ESPN JSON → DTO
  - `promotion.py` — leagues → PromotionDTO
  - `fighter.py` — athletes → FighterDTO (including record parsing, physical stats, headshot)
  - `event.py` — events → EventDTO (with status mapping, date parsing, slug generation)
  - `competition.py` — competitions → CompetitionDTO + CompetitorDTOs (corner, outcome, result method/round/time)
  - `ranking.py` — rankings → RankingDTO (per-category, trend, is_champion)
  - `broadcast.py` — broadcasts → BroadcastDTO (network, region, type)
  - `statistics.py` — statistics → StatisticDTO (category + label + value)
  - `weight_class.py` — weight classes → WeightClassDTO
  - `venue.py` — venues → VenueDTO (address, coordinates, capacity)
- `ESPNProvider` — complete BaseDataProvider implementation tying together client, resolver, and all parsers
- ESPN config — all API endpoint URLs, league IDs, status mapping, client defaults

### Pending
- Phase 2 unit tests (parsers tested against real ESPN fixture data)
- Phase 2 integration tests (ESPN client with mocked httpx)

---

## Next Milestone: Phase 3 — Sync Engine

**Goal:** Build the sync engine that fetches from providers and writes to the database.

**Scope:**
- `SyncEngine` orchestrator — runs jobs in dependency order within transactions
- 9 sync jobs — one per entity, each idempotent (re-run produces same DB state)
- Upsert strategies — merge vs. replace per entity
- Change diff — detect what changed for notification triggers
- Integration with `ExternalId` table for provider-neutral lookups
- Full observability via `sync_runs` + `sync_jobs` tables

**Blockers:** None — Phase 3 can begin immediately.

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
| Auth milestone not yet started | High | Blocks all personalized features. Must be scoped before Flutter work begins. |
| Cross-org fighter identity (FIGHT-07) | Medium | No backend design exists yet. ExternalId table lays the groundwork. |
| Non-UFC organization verification | Medium | Only UFC is fully verified. Gated on `scripts/verify_additional_organizations.py`. |

---

## Environment Setup

*Documented in `backend/.env.example` — to be created during Phase 2 implementation.*
