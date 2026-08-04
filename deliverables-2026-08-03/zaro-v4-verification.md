# Zaro AI Monorepo — Iteration 4 Verification Report (v9)

**Zip analyzed:** `from-github (4).zip` (1785755898536000000518)
**Date:** 2026-08-03
**Method:** Every claim verified by running the code — compile, import, fresh Postgres migrations, live HTTP tests, sync with DB row counts before/after, full pytest, npm install, tsc, expo export attempt, mobile↔backend OpenAPI contract diff.

---

## 1. Executive Summary

**Verdict: This is the first iteration that is genuinely CLOSE. ~80% of previously-reported blockers are fixed and verified. The remaining 20% is one core problem: the sync engine still cannot write data to the database — which means the API serves empty responses and the app shows no real data.**

### What improved (verified, with evidence)
| Area | v8 | v9 | Evidence |
|---|---|---|---|
| Zip integrity | 0 placeholders | **0 placeholders (793→711 files)** | `grep -rl "This file could not be retrieved"` → 0 |
| package.json / tsconfig.json | real | **real** | parsed successfully |
| assets/ dir | present | **present (but 1×1 px placeholder PNGs)** | `file assets/*.png` → `1 x 1, 8-bit/color RGBA` |
| Backend compiles | ✅ | **✅ (clean)** | `python -m compileall src/ tests/ sync.py` → exit 0 |
| App imports | ✅ | **✅ (117 routes)** | `from src.api.main import app` OK |
| Scheduler wired | ✅ | **✅ in lifespan** | `main.py:61` `SyncManager(context)` |
| SyncCheckpoint `__tablename__` | ✅ | **✅** | `support.py:79` `__tablename__ = "sync_checkpoints"` |
| Migrations fresh DB | ✅ | **✅ (001→004, no DuplicateColumnError)** | alembic upgrade head → 27 tables |
| Auth tables exist | ✅ | **✅** | users, user_sessions, devices, notifications, favorites, watchlist in `\dt` |
| Auth register/login live | 201/200 | **201/200 with real JWT** | register `{"access_token": ...}`, login 200 |
| Rankings/Champions 500 | 🔴 | **✅ 200 (empty)** | `{"categories":[],"synced_at":null}` |
| src/domain/models | ❌ missing | **✅ shims exist** | `src/domain/models/fighter.py` → `from src.db.models.fighter import Fighter` |
| Migration 004 (rankings columns) | ❌ | **✅ created** | `004_rankings_syncable_columns.py` |
| Mobile routes wired | ✅ | **✅ (8 routes, default exports)** | app/events.tsx etc. |
| Predict tab | 🔴 present | **✅ removed from tab bar** | `_layout.tsx` has no Predict |
| npm install | ✅ | **✅ (1283 pkgs)** | `added 1283 packages` |
| expo-asset in package.json | 🔴 missing | **✅ present** | `"expo-asset": "~11.0.0"` |
| Mobile tsc errors | 40 | **150 (but different root cause)** | see §4 |

### What is STILL BROKEN (the core problem)
| Issue | Status | Evidence |
|---|---|---|
| **Sync writes ZERO rows** | 🔴 **STILL BROKEN** | `python sync.py --full` → fetches 48 promotions from ESPN, then FAILS at upsert: `'is_active' is an invalid keyword argument for Promotion` + `'AsyncEngine' object has no attribute 'execute'`; row counts all 0 |
| **Sync uses engine, not session** | 🔴 | `sync.py` passes `db_engine` (AsyncEngine) as `db_session`; `IdResolver._db.execute()` fails on AsyncEngine |
| **PromotionUpsert._to_model sets is_active** | 🔴 | `Promotion` model has NO `is_active` column — the derived field doesn't exist |
| **Rankings/Champions return EMPTY** | 🟠 | `{"categories":[],"synced_at":null}` — no rows because sync never writes |
| **All data endpoints empty** | 🟠 | events/fighters/fights → `{"items":[],"total":0}` |
| **Tests still 212/30/17** | 🔴 | identical to v8 |
| **tsc 150 errors** | 🟠 | down from 40 (which was 1 file); now spread across ~55 files |
| **AI modules still present** | 🟠 | `mobile/intelligence/` (9 files), `recommendation/` (28 files), `platform/` (18 files) — but orphaned (imported by nothing) |
| **API base URL still placeholder** | 🟡 | `services/api.ts:9` → `'https://api.mma-platform.com/api'`; `NetworkConfig.ts:5` → `'https://api.mma-app.com'` |
| **Scheduler status 500s without Redis** | 🟠 | `AttributeError: 'NoneType' object has no attribute 'exists'` in LockManager |
| **/health/database always fails** | 🟡 | `check_database()` called without factory → returns False |
| **Assets are 1×1 placeholder PNGs** | 🟡 | 70-byte files |

---

## 2. Zip Integrity Report

| Check | Result |
|---|---|
| File count | **711** (v8: 793) |
| Corruption markers ("This file could not be retrieved") | **0** (v8: 0) |
| package.json | **real, valid JSON** |
| tsconfig.json | **real, valid JSON** |
| assets/ dir | **exists** — but 3 PNGs are 1×1 pixel placeholders |
| Extraction | clean, no errors |
| Top-level dirs | `backend/ mobile/ platform/ recommendation/ docs/` |

**Verdict: Delivery is clean this time. No placeholders.** The only asset concern: the three app icons (icon.png, splash.png, adaptive-icon.png) are 70-byte 1×1 transparent PNGs — the app will build but show no branding.

---

## 3. Structure Diff vs v8

### New in v9
- **`backend/src/domain/models/`** — 11 files, all re-export shims (`from src.db.models.X import X`). This was the exact missing piece that broke all 18 upsert files in v8.
- **`backend/alembic/versions/004_rankings_syncable_columns.py`** — new migration adding `source_provider` + `version` to `rankings`.
- **`backend/src/api/sync.py`** — scheduler dashboard endpoints (status/jobs/metrics/sync triggers).
- **`backend/src/scheduler/`** — full scheduler package (manager, jobs, locks, queue, monitor, live detector).
- **`backend/src/providers/espn/jobs/`** — 9 real SyncJob implementations (promotion, fighter, event, competition, broadcast, ranking, statistics, venue, weight_class).
- **`mobile/intelligence/`** — 9 AI-engine files (assistant, personalization, predictions, scouting).
- **`mobile/app/_infra.ts`** — dead barrel re-exporting 14 infra modules (16 tsc errors).
- **`mobile/PRODUCTION_AUDIT.md`** + `backend/PROJECT_STATUS.md` + `backend/DATA_AUDIT.md` — the (inaccurate) status claims.

### Removed vs v8
- **`prediction/`** (top-level) — GONE ✅
- **`backend/src/sync/upserts/` is now reachable** — all files import `src.domain.models.*` which now resolves ✅

### Still present (AI / out-of-scope)
- **`recommendation/`** (28 files) — orphaned, imported by nothing in backend/src or mobile
- **`mobile/intelligence/`** (9 files) — orphaned, imported by nothing except its own index files
- **`platform/`** (18 files) — orphaned enterprise framework
- **Mobile deep-links + Endpoints.ts still contain prediction/recommendation constants** — dead but present

---

## 4. Mobile Verification

### npm install
✅ `added 1283 packages in 1m` — no errors. `expo-asset` present in package.json (`~11.0.0`).

### TypeScript check (`npx tsc --noEmit`)
**150 errors** across ~55 files (v8: 40 errors in 1 file; v7: 718).

The 40-error file from v8 is fixed, but the codebase grew and new errors surfaced. Breakdown:

| File | Errors | Root cause |
|---|---|---|
| `features/fighters/screens/index.tsx` | 16 | missing exports referenced |
| `app/_infra.ts` | 16 | dead barrel; 3 missing modules (`./security`, `./release`, `./audit`) + 13 ambiguous re-exports |
| `features/fighters/components/index.tsx` | 13 | missing exports |
| `features/rankings/navigation/RankingsStack.tsx` | 9 | lazy screens return `() => null` stubs |
| `hooks/index.ts` | 7 | re-exports non-existent hooks |
| `theme/motion.ts` | 5 | shorthand property names |
| `features/events/...` | ~17 | type mismatches (ExtendedEvent missing fields) |
| `design-system/...` | ~8 | missing exports (ThemeContextValue, AvatarImage, PosterImage) |
| `app/bootstrap/BootstrapState.ts` | 1 | top-level await |
| `app/networking/Interceptors.ts` | 1 | top-level await |
| `app/session/SessionDevice.ts` | 2 | undefined `sessionManager` |
| missing modules | ~10 | `@hookform/resolvers/zod`, `@tanstack/query-async-storage-persister`, `react-query-persist-client`, `NetworkAnalytics`, `FightPredictionCard`, `OddsCard`, `LiveEventBanner`, `EventStatisticsScreen`, `ModalNavigator`, `./models` (×4) |

**Bottom line: tsc is NOT clean.** 150 errors is worse than the 40 in v8 numerically, but the error classes are now mundane (missing exports, missing deps, type mismatches) — fixable in a focused day.

### Expo export / bundle
❌ **Could not verify.** Metro bundler was killed by sandbox memory limits (OOM) on both android and web attempts — this is an environmental limitation of the sandbox, NOT a code verdict. The web export additionally requires `react-native-web` (not in package.json — a real gap for web target).

### Routes & screens
✅ All 8 routes wired with default exports: `index/events/fighters/rankings/search/profile/notifications/watchlist.tsx`.
✅ `_layout.tsx` has full provider tree (QueryProvider → AuthProvider → NotificationProvider → AppContent with Splash/Maintenance/OfflineBanner).
✅ **Predict tab is gone** from the tab bar (was the AI wiring in v8).

### AI modules
- `mobile/intelligence/` (9 files) — **present but orphaned** (imported by nothing in features/components/app).
- `recommendation/` (28 files) — **present but orphaned**.
- `platform/` (18 files) — **present but orphaned**.
- **No `/api/v1/predictions/*` routes in backend** ✅ (verified via OpenAPI).
- But `Endpoints.ts`, `DeeplinkTypes.ts`, `hooks/index.ts` still reference predictions — dead constants.

### API base URL
🟡 **Still placeholder:**
- `mobile/services/api.ts:9` → `'https://api.mma-platform.com/api'` (dev: `http://localhost:8000/api`)
- `mobile/app/networking/NetworkConfig.ts:5` → `'https://api.mma-app.com'`

---

## 5. Backend Verification

### 5.1 Compile
✅ `python -m compileall -q src/ tests/ sync.py` → exit 0, no errors.

### 5.2 App import + routes
✅ Imports cleanly with `JWT_SECRET` set (refuses to run with default secret — good security practice).
**117 routes registered**, including all previously-phantom endpoints:
- `GET /api/v1/champions`, `/api/v1/title-defenses`, `/api/v1/rankings/goat`, `/api/v1/rankings/streaks`
- `GET /api/v1/fighters/compare`, `/api/v1/fighters/{id}/rankings`, `/media`
- `POST /api/v1/me/favorites/...`, `/api/v1/me/watchlist/...`
- `GET /api/v1/recommendations*` (10), `/api/v1/search/*`, `/api/v1/notifications/*`
- `GET /api/v1/venues`, `/api/v1/weight-classes`, `/api/v1/promotions/*`
- Scheduler: `/api/scheduler/jobs`, `/status`, `/metrics`, `/sync/full`, `/sync/{entity}`

### 5.3 Migrations from scratch (fresh Postgres 15)
✅ **Clean apply 001→002→003→004 — no DuplicateColumnError this time.**
27 tables created: fighters, events, competitions, competitors, promotions, venues, weight_classes, rankings, statistics, broadcasts, fighter_records, users, user_sessions, devices, notifications, favorite_events, favorite_fighters, watchlist_events, user_preferences, sync_runs, sync_jobs, sync_checkpoints, provider_payloads, provider_conflicts, dead_letters, external_ids, alembic_version.

### 5.4 THE BIG ONE — sync engine data-flow proof

**Before sync:** fighters=0, events=0, rankings=0, sync_runs=0, competitions=0, promotions=0

**Command:** `python sync.py --full` (ESPN live)
**Result:**
```
src.providers.espn.provider: Fetched 48 promotions from ESPN
src.sync.engine: promotion: fetched 48 items
[ERROR] src.sync.upserts.id_resolver: Bulk resolve failed for promotion: 'AsyncEngine' object has no attribute 'execute'
[ERROR] src.sync.engine: Sync job promotion: 'is_active' is an invalid keyword argument for Promotion
[ERROR] src.sync.engine: Critical job failed: promotion. Aborting plan 'full_sync'.
Sync run finished: ... status=FAILED jobs=1 inserted=0 updated=0 errors=1
```

**After sync:** fighters=0, events=0, rankings=0, sync_runs=0, promotions=0

**Root causes (traced):**
1. **`sync.py` passes `db_engine` (AsyncEngine) as `db_session`** — `SyncContext.db` expects `AsyncSession` (`context.py:106`), and `IdResolver` calls `self._db.execute(...)` which AsyncEngine doesn't have. This is the #1 blocker.
2. **`PromotionUpsert._to_model()` sets `is_active=`** — but the `Promotion` model (`core.py:13-43`) has **no `is_active` column**. The upsert writes a field that doesn't exist in the schema. (The derived field lives only in the upsert's `_special_fields` logic, which is fine — but `_to_model` must not pass it.)
3. **The write path exists and is otherwise complete**: every job implements `_fetch()` + `_upsert()` calling `IdResolver` + `*Upsert.upsert_batch()`, and the pipeline calls `ctx.db.flush()`.

**What this means:** the sync engine now successfully *fetches* from ESPN (48 promotions, real HTTP 200s to sports.core.api.espn.com) but *cannot persist*. The two bugs are each 1-3 lines:
- `sync.py`: create an `async_sessionmaker(engine)` and pass a session (or make `IdResolver` handle both).
- `PromotionUpsert._to_model`: drop `is_active=` from the constructor call (compute it in `_apply_special_fields` only).

**Estimate to fix: 1-2 hours.** After that, sync should persist promotions → fighters → events → competitions → rankings in dependency order.

### 5.5 Live endpoint tests (uvicorn on 127.0.0.1:8010)

| Endpoint | Result | Body |
|---|---|---|
| `GET /health` | **200** | `{"status":"ok","app":"MMA Backend","version":"1.0.0"}` |
| `POST /api/v1/auth/register` | **201** | `{"access_token":"eyJ...","refresh_token":"eyJ..."}` (real JWT, 30-min expiry) |
| `POST /api/v1/auth/login` | **200** | token |
| `GET /api/v1/rankings` | **200 (empty)** | `{"categories":[],"synced_at":null}` |
| `GET /api/v1/champions` | **200 (empty)** | `{"categories":[],"synced_at":null}` |
| `GET /api/v1/title-defenses` | **200 (empty)** | `{"categories":[],"synced_at":null}` |
| `GET /api/v1/events` | **200 (empty)** | `{"items":[],"total":0,"page":1,"limit":50,"pages":0}` |
| `GET /api/v1/fighters` | **200 (empty)** | `{"items":[],"total":0,...}` |
| `GET /api/v1/me/favorites` | **200** | `{"fighters":[],"events":[],"promotions":[],"weight_classes":[]}` |
| `POST /api/v1/me/favorites/events/{id}` | **201** | `{"status":"added","event_id":"..."}` — **real DB write** |
| `GET /api/v1/me/favorites` (after) | **200** | event id persisted ✅ |
| `GET /api/scheduler/jobs` | **200** | 6 jobs registered (events_upcoming 900s, events_live 30s disabled, results 120s, rankings daily, ...) |
| `GET /api/scheduler/status` | **500** | `AttributeError: 'NoneType' object has no attribute 'exists'` — `LockManager` gets `context.redis=None` (no Redis running) |
| `GET /health/database` | **failed** | `check_database()` called with no factory → returns False |
| `GET /health/ready` | **failed** | `{"status":"failed","checks":{"database":{"status":"failed"}}}` |

**Key insight:** auth (register/login/favorites) is fully functional and DB-backed. All read endpoints work — but return empty arrays because the sync engine has never written a row. The app would boot, log in, and show nothing.

### 5.6 Test suite
**212 passed / 30 failed / 17 errors (259 collected) — IDENTICAL to v8.**

Failures cluster:
- `tests/api/test_endpoints.py` (2) — serialization expectations
- `tests/contract/test_api.py` (2) — metrics/sync response schema
- `tests/integration/test_cache.py` (5) — Redis down tests (no Redis)
- `tests/integration/test_failure_injection.py` (2) — retry policy
- `tests/integration/test_parsers.py` (7) — fighter/competition/ranking parsers
- `tests/integration/test_production.py` (1) — weak password
- `tests/integration/test_resume.py` (12) — SyncState/SyncStrategy (tests reference removed internals)
- `tests/auth/test_auth.py` (1) — RBAC payload role TypeError

Errors (17) — all `tests/auth/test_e2e_flows.py`: **SQLite has no `users` table** (`sqlite3.OperationalError: no such table: users`). Tests use SQLite fixtures; auth models are Postgres-only (JSONB, etc.). This is the same test-infra gap as v8: **e2e auth tests cannot pass without a real Postgres test DB or portable column types.**

**Claim check:** `PROJECT_STATUS.md` says "48 tests, 91% coverage" and `PRODUCTION_AUDIT.md` says "9.3/10 production-ready, 73 endpoints, all wired". Actual: **259 tests, 212 passing, 30 failing, 17 errors; 117 routes; sync writes nothing.** The documents are stale/false.

---

## 6. Issue-by-Issue Verdict (vs v8 remediation list)

| # | v8 issue | v9 status | Evidence |
|---|---|---|---|
| 1 | Zip corruption (142 placeholders) | ✅ **FIXED** | 0 placeholders |
| 2 | SyncCheckpoint missing `__tablename__` | ✅ **FIXED** | `support.py:79` |
| 3 | Auth no tables → register 500 | ✅ **FIXED** | migration 003; register 201 |
| 4 | Migration 002 DuplicateColumnError | ✅ **FIXED** | 001→004 clean |
| 5 | Rankings/statistics/broadcasts schema drift (500) | ✅ **FIXED** | rankings/champions/title-defenses all 200 |
| 6 | Sync writes zero rows | 🔴 **STILL BROKEN** | engine-vs-session + is_active bugs; rows all 0 |
| 7 | Scheduler commented out | ✅ **FIXED** | wired in lifespan; jobs endpoint 200 |
| 8 | 55/90 phantom API calls | 🟠 **PARTIALLY FIXED** | 33/76 phantom now (see §7) |
| 9 | Favorites stubs | ✅ **FIXED** | real DB write verified (201 + persisted) |
| 10 | AI modules present + Predict tab | 🟠 **PARTIALLY FIXED** | Predict tab removed; modules orphaned but present |
| 11 | Default API base URL placeholder | 🟡 **NOT FIXED** | still `api.mma-app.com` / `api.mma-platform.com` |
| 12 | Tests 212/30/17 | 🔴 **NOT FIXED** | identical numbers |
| 13 | JSONB-in-SQLite test issues | 🔴 **NOT FIXED** | auth e2e errors confirmed SQLite missing tables |
| 14 | Mobile routes unwired | ✅ **FIXED** | 8 routes with default exports |
| 15 | Shell components missing | ✅ **FIXED** | MaintenanceScreen/OfflineBanner exist |
| 16 | expo-asset missing | ✅ **FIXED** | in package.json |
| 17 | tsc 40 errors in 1 file | 🟠 **REGRESSED** | now 150 errors across 55 files (different causes) |

---

## 7. Mobile ↔ Backend Contract Diff (33 phantom paths)

Method: extracted all `/v1/...` strings from mobile `.ts/.tsx` (76 concrete), compared against live backend OpenAPI (101 paths, template-matched). **33 have no backend route:**

**AI-related (16 — should be DELETED, not implemented):**
`v1/predictions/accuracy`, `/dashboard`, `/highlights`, `/history`, `/matchup`, `/saved/*`, `/fight/*`, `/event/*`, `/fighter/*`, `v1/recommendations/dashboard`, `/events/similar`, `/fighters/because`, `/fighters/similar`, `/hidden-gems`, `/metrics`

**Genuinely missing (17 — backend work needed):**
- `v1/composite` (home aggregate)
- `v1/elo`
- `v1/fighters/search` (backend uses `GET /fighters?q=` instead)
- `v1/fighters/similarity`, `v1/fighters/trending`
- `v1/home`
- `v1/me/devices`, `v1/me/export`, `v1/me/stats`
- `v1/rankings/changes`, `v1/rankings/movement`, `v1/rankings/prospects`
- `v1/reminders`, `v1/reminders/{id}`
- `v1/search/suggestions`, `v1/search/voice`
- `v1/watchlist/collections`, `v1/watchlist/reminders`

**Also mismatched (not counted):**
- Favorites: mobile uses `/v1/favorites/fighters/*`; backend is `/v1/me/favorites/fighters/*` (prefix mismatch, 4 paths)
- Watchlist: mobile `/v1/watchlist/{type}/...` generic; backend is concrete `/v1/watchlist/events/{id}` etc.

---

## 8. New Issues Introduced in v9

1. **`app/_infra.ts`** — dead barrel referencing 3 non-existent modules (`./security`, `./release`, `./audit`) + ambiguous re-exports → 16 tsc errors. Imported by nothing — **DELETE it**.
2. **150 tsc errors** (up from 40) — mostly new feature code added since v8 with missing exports/types. Root cause: features/fighters + rankings + events + design-system have type inconsistencies.
3. **`/api/scheduler/status` 500s without Redis** — `LockManager` unconditionally calls `self._redis.exists()` when `context.redis=None`. Should degrade gracefully.
4. **`/health/database` + `/health/ready` report failed with healthy DB** — `check_database()` called without the session factory arg; returns False. Health endpoint is wrong by construction.
5. **Assets are 1×1 transparent PNGs** (icon/splash/adaptive) — app icon will be invisible.
6. **`recommendation/` and `platform/` dirs still shipped** (46 files) — orphaned but present; out of scope per user constraints.
7. **Duplicate Operation ID** in OpenAPI (`mark_all_read`) — FastAPI warning, minor.
8. **`react-native-web` missing** — `expo export --platform web` fails; only matters if web target is used.

---

## 9. Test Suite Comparison (v7 → v8 → v9)

| Metric | v7 (zip 2) | v8 (zip 3) | v9 (zip 4) |
|---|---|---|---|
| Backend compile | ✅ | ✅ | ✅ |
| App import / routes | ✅ 95 | ✅ 119 | ✅ **117** |
| Migrations fresh DB | ✅ | ✅ | ✅ 001→004 |
| Auth register | ✅ 201 | ✅ 201 | ✅ **201** |
| Auth login | ✅ 200 | ✅ 200 | ✅ **200** |
| Rankings/champions | 500 | 500 | ✅ **200 (empty)** |
| Sync writes rows | ❌ 0 | ❌ 0 | ❌ **0 (fetch works, persist fails)** |
| pytest pass/fail/error | 212/30/17 | 212/30/17 | **212/30/17** |
| npm install | ✅ | ✅ | ✅ 1283 |
| tsc errors | 718 (690 corrupt) | 40 | **150** |
| Zip placeholders | 142 | 0 | **0** |
| Routes wired | 8 | 8 | **8** |
| Predict tab | present | present | **removed** |
| Phantom API paths | 55 | 40 | **33** |

---

## 10. Remaining Gap Analysis (vs full remediation plan)

### Phase A — Make sync write data (BLOCKER, 1-2h)
- [ ] `backend/sync.py`: pass an `AsyncSession` (from `async_sessionmaker(engine)`) to `SyncEngine.execute()` instead of the engine
- [ ] `backend/src/sync/upserts/promotion.py`: remove `is_active=` from `Promotion(...)` constructor in `_to_model` (field doesn't exist on model)
- [ ] Verify: `python sync.py --full` → promotions > 0, then fighters > 0, etc.

### Phase B — Graceful degradation (2-3h)
- [ ] `backend/src/scheduler/locks.py` + `queue.py`: guard `redis is None` (return healthy-degraded instead of 500)
- [ ] `backend/src/api/main.py` + `src/monitoring/health.py`: inject the real session factory into `check_database()`; fix `/health/ready`
- [ ] Re-run: `/api/scheduler/status` → 200; `/health/database` → healthy

### Phase C — Mobile type cleanup (0.5-1 day)
- [ ] **DELETE** `mobile/app/_infra.ts` (dead barrel, 16 errors)
- [ ] Fix `features/fighters/screens/index.tsx` + `components/index.tsx` (29 errors): export the actual hooks (`useFighters`, `useFighterDetail`, `FighterStats`, `useFavoriteFighter`, `useHistory`)
- [ ] Fix `hooks/index.ts` + `features/index.ts` (10 errors): re-export real symbols or delete dead re-exports
- [ ] Fix `features/rankings/navigation/RankingsStack.tsx` (9): replace `() => null` lazy stubs with real screen imports
- [ ] Add missing deps: `@hookform/resolvers` (zod), `@tanstack/query-async-storage-persister`, `@tanstack/react-query-persist-client`
- [ ] Create missing modules: `NetworkAnalytics.ts`, `FightPredictionCard` (or delete), `OddsCard` (or delete), `LiveEventBanner`, `EventStatisticsScreen`, `ModalNavigator`
- [ ] Fix `theme/motion.ts` shorthand props; `app/bootstrap/BootstrapState.ts` + `Interceptors.ts` top-level awaits (wrap in async fn)

### Phase D — Contract gap (0.5-1 day)
- [ ] DELETE all 16 prediction/recommendation-AI API calls from `Endpoints.ts`, `hooks/index.ts`, `features/events/detail/index.tsx`, `features/events/index.ts`, `DeeplinkTypes.ts`, `integration/index.ts`
- [ ] Align favorites calls: `/v1/me/favorites/fighters/*` (4 paths)
- [ ] Align watchlist calls: concrete `/v1/watchlist/events/{id}`, `/v1/watchlist/fighters/{id}`
- [ ] Add backend: `GET /v1/home` (composite), `GET /v1/fighters/search`, `GET /v1/me/stats`, `GET /v1/rankings/movement`, `GET /v1/reminders`, `GET /v1/search/suggestions` — or remove from mobile
- [ ] Set real API base URL (from env `EXPO_PUBLIC_API_URL`)

### Phase E — Remove AI / out-of-scope (1h)
- [ ] Delete `mobile/intelligence/` (9 files)
- [ ] Delete `recommendation/` (28 files)
- [ ] Delete `platform/` (18 files) — or move to a separate repo if ever wanted
- [ ] Delete `mobile/PRODUCTION_AUDIT.md` + `backend/PROJECT_STATUS.md` + `backend/DATA_AUDIT.md` false claims, or rewrite honestly

### Phase F — Tests green (1-2 days)
- [ ] Run auth e2e tests against real Postgres (set `TEST_DATABASE_URL`) instead of SQLite, OR add SQLite-compatible auth migrations
- [ ] Fix `tests/integration/test_resume.py` (12): tests reference removed `SyncState.last_sync_at` — update to current `checkpoints.py` API
- [ ] Fix `test_parsers.py` (7) + `test_cache.py` (5, needs fakeredis) + `test_contract` (2) + `test_failure_injection` (2)
- [ ] Target: 259/259 green

### Phase G — Production polish (1 day)
- [ ] Real app icons (replace 3 placeholder PNGs)
- [ ] `react-native-web` if web target needed
- [ ] Redis for scheduler locks + cache (or guard None)
- [ ] `.env.example` with `EXPO_PUBLIC_API_URL`, `JWT_SECRET`, `DATABASE_URL`

---

## 11. Updated Prioritized Action Plan

### Week 1 — make it real
| Day | Work | Exit criteria |
|---|---|---|
| 1 | Phase A (sync write fix) | `sync.py --full` → promotions>0, fighters>0, sync_runs>0 |
| 1 | Phase B (graceful degradation) | `/scheduler/status` 200, `/health/database` healthy |
| 2 | Phase C (tsc cleanup) | `tsc --noEmit` → 0 errors |
| 3 | Phase E (delete AI/scope) | repo contains zero AI modules |
| 3-4 | Phase D (contract align) | 0 phantom paths; real base URL |
| 5 | Phase F (tests) | pytest green (or documented Postgres-only) |
| 6-7 | Phase G (polish) | icons, env, redis |

### "Continue with Zaro AI or take over manually?"
**Recommended: Take over manually for the backend sync fix (Phase A+B — 4 hours), keep Zaro for the mobile type cleanup (Phase C+D — mechanical, well-scoped).** Rationale:
- The remaining backend blockers are 2 named 1-line bugs + 2 dependency-injection bugs. A fresh prompt to Zaro risks re-introducing the same class of regression (they've now shipped 4 iterations, each fixing some and breaking others).
- The mobile work is large but mechanical (delete dead code, fix missing exports) — ideal for a well-specified prompt with the exact file list above.
- The docs claims are untrustworthy in every iteration (9.3/10 each time) — any future Zaro submission MUST be gated on a runnable acceptance test (the corrective prompt below).

---

## 12. Evidence Trail (commands run)

```
# zip integrity
unzip -q -o zaro_v4.zip -d zaro_v4 && find zaro_v4 -type f | wc -l        → 711
grep -rl "This file could not be retrieved" . | wc -l                      → 0
file assets/*.png                                                          → 1x1 PNG

# backend
python -m compileall -q src/ tests/ sync.py                               → exit 0
JWT_SECRET=... python -c "from src.api.main import app; ..."               → 117 routes
alembic upgrade head                                                       → 001→004 OK, 27 tables
python sync.py --full                                                      → fetch 48 promos, FAIL persist
sudo -u postgres psql -d mma_v9 -t -c "SELECT count(*) ..."               → all 0 before/after
pytest tests/ -q --no-header                                              → 212 passed, 30 failed, 17 errors
uvicorn src.api.main:app --port 8010                                       → booted
curl /health, /api/v1/auth/register, /api/v1/auth/login, /api/v1/rankings,
     /api/v1/champions, /api/v1/events, /api/v1/me/favorites (GET+POST),
     /api/scheduler/jobs, /api/scheduler/status                           → 200s (empty), 201, 500

# mobile
npm install --no-audit --no-fund                                         → 1283 packages
npx tsc --noEmit --pretty false                                           → 150 errors
npx expo export --platform android|web                                    → Killed (sandbox OOM)
grep -rhoE 'v1/...' mobile → /tmp/mobile_paths.txt (76)                    → 33 phantom vs OpenAPI
```

---

## 13. Verdict

**Is THIS version good enough to build on? — CONDITIONALLY YES, with one hard blocker.**

The blocker: **the sync engine still cannot write a single row to the database.** Everything else — auth, migrations, routes, scheduler registration, mobile boot path, favorites persistence — works. Fix the two named bugs in `sync.py` and `promotion.py` (1-2 hours) and the entire data layer becomes live: the 117 routes will serve real ESPN data, and the app becomes a real product.

This is the closest of the four iterations by a wide margin. The remaining work is small, named, and mechanical (~1 week total). Do NOT send this back to Zaro for a "fix everything" pass — hand them a tightly-scoped spec for the mobile type errors only, and fix the backend sync yourself.
