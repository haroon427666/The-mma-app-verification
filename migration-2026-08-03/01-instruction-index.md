# Instruction Index — deliverables-2026-08-03 (all 15 prompts)

Extracted 2026-08-03. Every instruction is tagged with source file. Claims from the
zaro-* verification/audit docs are marked **VERIFIED** (re-checked against actual V10
code on 2026-08-03) or **STALE** (contradicted by current V10 code).

---

## 1. continuation-prompt.md (shared, identical to 08-02)

| # | Instruction | Files affected |
|---|---|---|
| C1 | Finish Production Readiness Phase 1: Redis cache-aside (DI-overridable, fakeredis in tests), scheduler job-store hardening, structured logging + Prometheus, health endpoints (`/health/ready`, dependency checks), performance audit, config hardening, production Dockerfile, docs | backend/src, backend/docs |
| C2 | Redis first — it was interrupted at design | backend |
| C3 | Also: flip on TheSportsDB client for logos/images (low-risk) | backend/src/providers/tsdb |
| C4 | After Phase 1, expose already-synced data (rankings/champions endpoints) | backend/src/api/v1 |
| C5 | Continue only from the point where the previous session was cut off | — |

Status: C1 is ~90% DONE in V10 (cache-aside, ETag, 003 migration, 300 tests, health
fixed). Remaining: scheduler job-store hardening, Prometheus, prod Dockerfile, live
DB verification of migration 003.

## 2. assessment.md (new in 08-03)

| # | Instruction |
|---|---|
| A1 | Same-state assessment: Phase 1 was interrupted; nothing was committed; test count 48 (stale baseline) |

Verified reality: 300 tests green; Phase 10 ✅ in PROJECT_STATUS; alembic head 003.
Assessment is **STALE** (written before the previous session's work).

## 3. data-specification.md (shared, identical)

| # | Instruction | Files |
|---|---|---|
| D1 | 4-tier scheduler jobs: foundation (promotions, weight classes, venues), fighters, events+competitions, rankings/statistics/broadcasts — with cadences (events 3 min live-mode, 6h otherwise; rankings 12h; etc.) | backend/src/scheduler, src/sync |
| D2 | Cache TTL policy (data-spec defines per-entity TTLs) | backend/src/api/cache.py |
| D3 | Multi-provider sync (ESPN primary; TSDB + Octagon enrichment) | backend/src/providers |
| D4 | Sync state machine (FULL/INCREMENTAL/RESUME/FORCE), checkpointing, dead-letter | backend/src/sync |
| D5 | DB design: 27 tables, JSONB payload store, external_ids, sync_runs metrics | backend/alembic, backend/src/db |

## 4. espn-mma-api-reference.md / espn-api-ref-part1.md / espn-api-ref-part2.md (reference + 2 new)

| # | Instruction | Files |
|---|---|---|
| E1 | Store headshot_url on Fighter (construct from athlete ID) | backend/src/db/models/fighter.py, sync/upserts |
| E2 | Add W/L/D/NC + method breakdown + title record fields to Fighter (records/0) | fighter model, espn/parsers/records.py |
| E3 | Add per-fight `FightStatistic` model (40+ fields) | new model + migration |
| E4 | Add `Official`/`CompetitionOfficial` models (referee/judges) | new models + migration |
| E5 | Add logo_url to Promotion, Broadcast | models |
| E6 | Multi-league sync (PFL, Rizin) — same code path, change slug | espn provider |
| E7 | Recommended endpoints: `/rankings`, `/rankings/{wc}`, `/champions`, `/events/upcoming|live|results`, `/events/{id}/card`, `/fighters/{id}/fights|stats|record|compare`, `/weight-classes/*`, `/fights/*`, `/promotions/{slug}/events`, `/venues/{id}/events`, `/referees/*` | backend/src/api/v1 |

Note: many already exist in V10 (rankings list/mens/womens/p4p/{division}, events
upcoming/live/past, fighters history/statistics). Champions endpoint **does not exist**
(verified).

## 5. feature-master-plan.md (new in 08-03)

| # | Instruction | Priority |
|---|---|---|
| F1 | Phase 1: Production Readiness (Redis cache, scheduler hardening, logging/metrics, health, N+1 audit, prod Dockerfile, docs) + flip on TheSportsDB | P0 |
| F2 | Phase 2: `GET /rankings` (+filters), `GET /champions`, event status filter, fighters-in-division, roster-by-promotion, global search | P1 (data already in DB) |
| F3 | Phase 3: client-first (local favorites, local notifications, calendar, compare) | P2 |
| F4 | Phase 4: computed/aggregate (records, streaks, leaderboards, H2H) | P3 |
| F5 | Phase 5: accounts/auth/push (optional; MVP is account-free) | P4 (optional) |
| F6 | Hard constraints: NO AI, NO betting, NO paid APIs | policy |

## 6. feature-registry.md (shared, identical)

| # | Instruction |
|---|---|
| FR1 | Feature registry lists ~48 backend-ready features; must be kept truthful |

## 7. flutter-audit.md (shared, identical)

| # | Instruction |
|---|---|
| FA1 | Earlier audit against the old Flutter codebase — superseded (repo is RN/Expo now) |

## 8. product-requirements.md (shared, identical)

| # | Instruction |
|---|---|
| P1 | MVP scope: browse events/cards, live status, fighter profiles + stats/history, rankings & champions, search, compare, calendar, on-device favorites + reminders; NO accounts, NO push server, NO AI, NO paid | policy |

## 9. zaro-ai-audit-analysis.md (new; v1 zip review)

| # | Finding → instruction |
|---|---|
| Z1 | Fix sync pipeline syntax error, SyncManager commented out, missing routes, JSX-in-.ts, missing deps, JSONB-in-SQLite, AI modules, stubs | — |
| Z2 | Verify every claim by running code, not docstrings | process |

Mostly **STALE** for backend (fixed in later iterations).

## 10. zaro-v2-verification.md (new; v2 zip)

| # | Finding → instruction | V10 status |
|---|---|---|
| ZV2-1 | Auth has NO migration tables (register/login 500) | **STILL TRUE (verified)** — no migration creates users etc. |
| ZV2-2 | Migration 002 re-adds `synced_at` to rankings/statistics already in 001 → DuplicateColumnError on fresh DB | **CONFIRMED in current 001+002** (001 line 219 rankings.synced_at; 002 loop line 147–150 re-adds) — but note audit claimed v9 fixed it; current repo still shows the conflict |
| ZV2-3 | Sync cannot persist: `sync.py --full` crashes (SyncPlan API mismatch); scheduler jobs never write | **CONFIRMED (verified)** — sync.py:151 `SyncPlan(entity_types=...)` vs real no-arg `SyncPlan()`; SyncEngine(context=...) vs real `SyncEngine(jobs=...)`; SyncPipeline(engine=...) vs real `pipeline.execute(ctx, state, ...)` |
| ZV2-4 | Rankings 500 (schema drift) | **PARTIALLY FIXED** — 002 loop now includes rankings (verified line 148), but 001↔002 conflict blocks clean apply; source_provider would exist if 002 applies |
| ZV2-5 | `src/domain/` missing (18 upsert files import it) | **FIXED (verified)** — domain shims exist in V10 |
| ZV2-6 | Tests 212/30/17 | **FIXED (verified)** — 300 passed |
| ZV2-7 | Mobile: zip corruption, missing assets, JSX-in-.ts, phantom routes | **STILL TRUE in this repo** (mobile byte-identical to reference baseline) |

## 11. zaro-v3-verification.md (new; v3 zip)

| # | Finding → instruction | V10 status |
|---|---|---|
| ZV3-1 | `sync.py` NameError `SyncPlan` not imported | **FIXED** — import exists (sync.py:132); but API mismatch remains (ZV2-3) |
| ZV3-2 | `src.domain` missing → 18 upsert files dead | **FIXED** — shims exist |
| ZV3-3 | rankings.source_provider missing | See ZV2-4 |
| ZV3-4 | expo-asset missing, JSX-in-.ts (40 errors), assets missing | **STILL TRUE (mobile baseline)** |
| ZV3-5 | AI modules (prediction/recommendation/intelligence) still present + Predict tab | **STILL TRUE (verified)** — dirs exist; mobile tab wired |

## 12. zaro-v4-verification.md (new; v4 zip = reference repo's iteration)

| # | Finding → instruction | V10 status |
|---|---|---|
| ZV4-1 | Sync engine fetches ESPN but dies: `sync.py` passes AsyncEngine as db_session; `PromotionUpsert._to_model` sets is_active (no such column) | **PARTIALLY STALE** — current promotion.py has NO is_active in _to_model (verified lines 27–34); but sync.py still passes db_engine wrong (ZV2-3) |
| ZV4-2 | 003_auth_tables.py existed in v9 | **MISSING in V10** — no auth migration anywhere (verified) |
| ZV4-3 | Scheduler status 500 without Redis (LockManager NoneType.exists) | **NOT VERIFIED** — needs live run; main.py SyncManager still commented out |
| ZV4-4 | /health/database failed (check_database without factory) | **FIXED (verified)** — health endpoints OK |
| ZV4-5 | tsc 150 errors; mobile route files exist in v4 | **STALE for this repo** — this repo's mobile has NO route files (matches v1 baseline) |
| ZV4-6 | Contract gap: 33 phantom paths; favorites prefix `/v1/favorites` vs `/v1/me/favorites` | **STILL TRUE (verified)** — mobile endpoints not checked in this repo's baseline |

## 13. zaro-opencode-verification.md (new; v10 = THIS repo)

| # | Finding → instruction | Verified in V10 |
|---|---|---|
| ZV10-1 | Sync engine can never write: model↔migration drift on 14/14 tables. `first_event_date` model=String(20) vs migration=DATE (fatal); `time_utc` model=String(10) vs migration=TIME (fatal) | **CONFIRMED (verified)** — core.py:32 String(20) vs 001:31 Date; event.py:33 String(10) vs 001:141 Time |
| ZV10-2 | Auth tables have no migration (003 deleted) → register 500 | **CONFIRMED (verified)** |
| ZV10-3 | Rankings 500: source_provider missing | See ZV2-4 (002 loop includes rankings now, but 001↔002 conflict) |
| ZV10-4 | sync.py wrong API (4 call sites) | **CONFIRMED (verified)** |
| ZV10-5 | Scheduler never runs (main.py:38-41 commented) | **CONFIRMED (verified)** |
| ZV10-6 | Mobile unroutable, 444 tsc errors, expo-asset missing, assets missing | **CONFIRMED** (mobile = baseline, untouched) |
| ZV10-7 | AI modules still shipped + wired (Predict tab) | **CONFIRMED** |
| ZV10-8 | 43/79 mobile API paths phantom | **NOT RE-VERIFIED** (mobile unchanged since baseline; count likely holds) |
| ZV10-9 | Docs overclaim (PROJECT_STATUS "Phase 7 Scheduler Complete") | **PARTIALLY TRUE** — PROJECT_STATUS updated by previous session (Phase 10 ✅); still lists Scheduler Complete while it never runs |
| ZV10-10 | Tests 300 green, cache/ETag real, health fixed, 003 migration applies | **CONFIRMED (verified)** — 300 passed, ruff clean, compile/import OK |

---

## Consolidated "files to create/restore/modify" register

### Create (new work)
| File | From | Phase |
|---|---|---|
| Migration `004_auth_tables.py` (users, user_sessions, user_preferences, favorite_fighters, favorite_events, watchlist_events, notifications, devices) | models/auth.py | 2 |
| Migration `005_schema_fixes.py` (first_event_date→Date, time_utc→Time, sync_runs columns, sync_jobs.duration_ms, statistics/broadcasts updated_at, competitors syncable cols) | models | 2 |
| `GET /api/v1/champions` (+ `{division}`) | ranking data | 3 |
| `FightStatistic` / `Official` / `CompetitionOfficial` models (optional per ESPN ref part2) | — | 5 (optional) |
| Fighters record/stats fields (wins/losses/draws, headshot_url, gym) | espn ref | 5 (optional) |

### Restore from reference repo
| File | Reason |
|---|---|
| `backend/tests/integration/test_cache.py` | Only file missing in V10 vs reference (content-compare before restore; V10 has unit/test_cache.py + test_api_cache.py which may supersede it) |

### Modify
| File | Change | Phase |
|---|---|---|
| `backend/sync.py` | Rewrite to real API: `SyncEngine(jobs=registry)`, `SyncPlan()`/`FullSyncPlan()`, `execute(plan, provider, db_session=async_session)`; pass AsyncSession not engine | 2 |
| `backend/alembic/versions/002_phase6_support.py` | Remove `"rankings"` from syncable loop (001 already has synced_at) or guard; ensure fresh-DB apply | 2 |
| `backend/src/db/models/core.py` | `first_event_date: Mapped[date] = Date`; fanart_urls JSONB (match migration) | 2 |
| `backend/src/db/models/event.py` | `time_utc: Mapped[time] = Time` | 2 |
| `backend/src/api/main.py` | Wire SyncManager in lifespan with real SyncContext + session factory; `SYNC_ENABLED` flag | 2 |
| `backend/src/scheduler/locks.py`, `queue.py` | Guard `redis is None` (degrade instead of 500) | 2 |
| `backend/src/monitoring/health.py` | (already fixed — verify) | — |
| `backend/src/api/v1/other.py` | Add `/champions`; ensure rankings live | 3 |
| `backend/tests/conftest.py` | Postgres-backed fixtures + migration-coverage test (models vs inspect) | 6 |
| `backend/PROJECT_STATUS.md`, docs | Honest numbers (300 tests, 91 paths, sync status) | 6 |

### Delete (policy: no AI, no betting)
| Path | Reason |
|---|---|
| `prediction/`, `recommendation/`, `intelligence/`, `platform/` (top-level) | User rejected ALL AI |
| `mobile/features/predictions/`, `mobile/features/recommendations/` + Predict/Recommend tabs | AI UI |
| `mobile/features/events/components/FightPredictionCard.tsx`, `OddsCard.tsx` | betting/prediction |
| `backend/src/api/v1/recommendations.py` + mount | AI-adjacent router (decision: delete vs keep rules-based feed) |

### Mobile repair (baseline restore, from v4 reference or rebuild)
| File | Change | Phase |
|---|---|---|
| `mobile/app/index.tsx`, events, fighters, rankings, search, profile, notifications, watchlist `.tsx` | Create route files with default exports | 4 |
| `mobile/app/_layout.tsx` | Fix imports of shell components (create `MaintenanceScreen.tsx`, `OfflineBanner.tsx`) | 4 |
| `mobile/package.json` | Add `expo-asset`, `react-native-web` | 4 |
| `mobile/assets/` | icon.png, splash.png, adaptive-icon.png | 4 |
| 6 files `.ts → .tsx` (design-system, features themes, analytics, notifications managers) | JSX-in-.ts rename | 4 |
| `mobile/app/networking/NetworkConfig.ts` + `services/api.ts` | Single source, `EXPO_PUBLIC_API_URL` | 4 |
| favorites/watchlist/rankings API calls | Align with backend (`/v1/me/favorites/*`, concrete watchlist, `/rankings/{division}`) | 4 |
| Delete `mobile/app/_infra.ts` dead barrel | tsc errors | 4 |

---

## Assumptions (recorded per workflow)
1. Reference repo `from-github (1)` = pre-OpenCode baseline of the SAME monorepo; V10 ⊇ reference at file level (only `tests/integration/test_cache.py` missing). V9/reference is reference-only, never assumed correct.
2. Live Postgres verification is not possible in this environment (no Docker daemon, no psql) → migration apply must be proven via `--sql` + a portable test (SQLite models check) unless a Postgres becomes available.
3. Mobile baseline is broken identically in V10 and reference → mobile work is a restore/repair, not a comparison-diff task.
4. Tests use SQLite + `create_all` (bypasses migrations) → 300 green does NOT prove migration correctness; a migration-coverage test is required.
5. `default_cache()` resolves to Redis-backed manager; tests monkeypatch to MemoryCacheManager (prior-session convention).
6. The v4/v10 audits describe zips; claims were re-verified against actual V10 files (marked above) — several were stale.

## Dependencies & conflicts
- DEP: migration 002/005 fixes must precede any live sync run; schema drift blocks all inserts.
- DEP: sync.py rewrite depends on `async_session_factory()` wiring; scheduler wiring depends on real SyncContext.
- CONFLICT: 001 creates `rankings.synced_at` + `statistics.synced_at` inline; 002 re-adds → fresh-DB DuplicateColumnError. Resolution: drop rankings from 002 loop (statistics not in loop — verified).
- CONFLICT: `fanart_urls` model=Text but 001 type? (check in Phase 2; likely JSON drift).
- CONFLICT: mobile `services/api.ts` vs `NetworkConfig.ts` duplicate configs (resolve to one).
- CONFLICT: `/v1/favorites` (mobile) vs `/v1/me/favorites` (backend); generic watchlist vs concrete.
