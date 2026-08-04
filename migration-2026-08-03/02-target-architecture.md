# Target Architecture — reconstructed from deliverables-2026-08-03

Reconstructed from data-specification, feature-master-plan, espn-api-ref (part1/2),
product-requirements, and the zaro-* verification chain. Grounded in actual V10 code.

---

## 1. Repository layout (target)

```
mma-app-zaro-ai-repo/
├── backend/                  FastAPI + SQLAlchemy async + ESPN/TSDB/Octagon sync
│   ├── src/
│   │   ├── api/              main.py (lifespan: scheduler ON), v1/ routers, cache.py, etag.py
│   │   ├── auth/             JWT + Argon2 + RBAC (works, needs tables)
│   │   ├── db/models/        core, event, fighter, support, auth — 27 tables
│   │   ├── db/repositories/  ON CONFLICT upserts
│   │   ├── dependencies/     DI container
│   │   ├── domain/models/    re-export shims → db.models (compat layer)
│   │   ├── features/         feature flags
│   │   ├── logging/          structured logging
│   │   ├── metrics/          Prometheus
│   │   ├── middleware/       auth, cache (Redis/Memory), rate_limit
│   │   ├── monitoring/       health, alerts, providers, exception_tracker
│   │   ├── providers/        espn/ (client, parsers, jobs), tsdb/, octagon/, base, dto/
│   │   ├── scheduler/        manager, jobs, locks, queue, retry, live_mode, monitor
│   │   ├── schemas/          pydantic response schemas
│   │   ├── services/         auth_service, fighter_service
│   │   ├── sync/             engine, pipeline, plan, context, upserts/, state, cache_invalidation
│   │   └── telemetry/        tracer
│   ├── alembic/versions/     001 → 002 → 003 → 004(auth) → 005(schema fixes) [head=005]
│   ├── tests/                unit (300 green) + integration + api + auth + contract
│   ├── sync.py               CLI → real engine API (FIX REQUIRED)
│   ├── scheduler.py          standalone scheduler entry
│   └── docs/, *.md           honest status
├── mobile/                   Expo/React Native app (RESTORE/REPAIR REQUIRED)
├── prediction/  recommendation/  intelligence/  platform/   → DELETE (no AI)
├── docs/                     planning docs
└── deliverables-*            prompt sets (read-only)
```

## 2. Data flow (target, all verified against code)

```
ESPN public API ──▶ ESPNProvider/parsers ──▶ DTOs ──▶ UpsertEngine (ON CONFLICT)
      │                                                        │
      └── 9 SyncJobs (promotion…weight_class)                   ▼
                                             async_session → Postgres (27 tables)
      scheduler (SyncManager in lifespan, SYNC_ENABLED)        │
      sync.py --full (real API)                                 ▼
                                              cache invalidation (after_sync event)
                                                       │
      REST API (91 OpenAPI paths) ◀── ETag/304 + cache-aside ◀┘
      mobile app (8 routes) ◀── EXPO_PUBLIC_API_URL
```

**Critical path (the blocker):** model↔migration drift (first_event_date, time_utc,
syncable columns) → every INSERT fails → DB empty → all screens empty.

## 3. Endpoint surface (target)

- Data (exists): fighters list/detail/statistics/history/next-fight, events
  list/upcoming/live/past/detail, fights list/detail, rankings
  list/mens/womens/p4p/{division}, promotions list/detail/{slug}/events/fighters,
  venues list/detail/events, weight-classes, search, health×3, auth, me/*,
  notifications, scheduler dashboard.
- **MISSING (add):** `GET /champions`, `GET /champions/{division}`,
  `GET /events/results`, `GET /events/{id}/card`, `GET /fighters/compare`,
  `GET /fighters/{id}/record`, `GET /weight-classes/{slug}/fighters`,
  `GET /promotions/{slug}/rankings`.
- Optional (espn ref): `/fights/{id}/stats` (FightStatistic), `/fights/{id}/officials`.

## 4. Schema targets (per table, drift to fix)

| Table | Drift to fix |
|---|---|
| promotions | first_event_date String(20)→Date; fanart_urls Text→JSONB (check); syncable trio ok via 002 |
| events | time_utc String(10)→Time; date_utc ok |
| fighters | is_active ok; add record fields (wins/losses/draws, method breakdowns) optional |
| rankings | source_provider/version (002 loop ✓ but 001↔002 conflict must be resolved) |
| statistics | synced_at exists in 001; updated_at missing? (add in 005) |
| broadcasts | updated_at missing? (add in 005) |
| competitors | syncable trio missing (not in 002 loop) → add in 005 |
| sync_runs | metrics columns exist via 002 ✓ (verified) |
| sync_jobs | duration_ms int vs float drift (005) |
| users/…auth | NO table exists → migration 004 |

## 5. Tests target

- 300 unit green (kept); add: migration-coverage test (models ↔ `inspect` diff),
  auth e2e against real schema, sync-engine row-write test (SQLite-compatible or
  documented Postgres-only), champions endpoint tests.

## 6. Constraints (locked)

NO AI of any kind · NO betting · NO paid services · anonymous/local-mode MVP ·
account layer optional (Phase 5) · TheSportsDB is a legal free on-ramp (key "3").
