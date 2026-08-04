# v10 Verification Report — OpenCode-Edited MMA Monorepo

**Date:** 2026-08-03 | **Auditor:** Super Agent (independent verification)
**Artifact:** `this is edited with opencod..zip` (1785771583599000000147), session log `session-ses_0387.md`
**Method:** Run everything — compile, import, migrate on fresh Postgres 15, live endpoints, real sync with row counts, full pytest, npm/tsc/expo, mobile↔backend OpenAPI contract diff, and a verbatim cross-check of the OpenCode session log. No claims taken at face value.

---

## 1. Executive Summary

### Verdict: **PARTIALLY FIXED — the backend is meaningfully better (tests 300 green, real caching/ETag, health fixed), but the core blocker (no data in the database) remains, and the mobile app regressed badly.**

**What OpenCode actually accomplished (verified true):**

| Claim | Verdict | Evidence |
|---|---|---|
| Cache-aside on read endpoints with per-route TTLs | ✅ **REAL** | `src/api/cache.py` exists; `curl /api/v1/events` → `Cache-Control: public, max-age=300` |
| Content-hash ETag + 304 on If-None-Match | ✅ **REAL** | `curl -H "If-None-Match: <etag>"` → **HTTP 304** (empty body) |
| Sync→cache invalidation via `after_sync` event | ✅ REAL (but never fires) | `src/sync/cache_invalidation.py` registered; sync never runs |
| Index migration `003_phase8_performance` (13 indexes) | ✅ **REAL** | applies cleanly on fresh Postgres |
| Tests: **300 passed**, ruff clean | ✅ **REAL** | `pytest -q` → **300 passed, 0 failed, 0 errors**; `ruff check src` → clean |
| Backend compiles + app imports | ✅ **REAL** | compileall clean; 91 OpenAPI paths (73 under /api/v1) |

**What is still broken (each proven below):**
- 🔴 **The sync engine can never write data.** Deepest root cause found across all five iterations: **model↔migration schema drift on 14/14 tables**. `promotions.first_event_date` is `String(20)` in the model but `DATE` in migration 001; the ESPN parser produces strings; every insert → `DatatypeMismatchError`. I proved the engine DOES reach ESPN (fetched 25 real promotions), DOES reach the DB (real bulk INSERT attempted), then dies on the type mismatch. **Row counts after: 0 everywhere, sync_runs = 0.**
- 🔴 **Auth tables have no migration.** `003_auth_tables.py` (present in v9) was **deleted** in this repo. `users`, `user_sessions`, `favorite_fighters`, `favorite_events`, `watchlist_events`, `notifications`, `devices` exist as models but NO migration creates them. **Live `POST /api/v1/auth/register` = 500** (`relation "users" does not exist`). Auth e2e tests pass only because they use SQLite in-memory + `create_all`, bypassing migrations.
- 🔴 **`GET /api/v1/rankings` = 500** — `column rankings.source_provider does not exist` (v9 bug, NOT fixed; 002's syncable-columns loop still omits `rankings`).
- 🔴 **`sync.py` entry point still uses the wrong API** — `SyncPlan(entity_types=...)` / `SyncEngine(context=...)` / `SyncContext(db=...)` at `sync.py:151,154,189,212`. **OpenCode's own session log spotted this mismatch (lines ~3657–3659) and dismissed it**: *"Let me not worry; that's a top-level script possibly from the old codebase port."* It never fixed it.
- 🔴 **Scheduler never runs** — `SyncManager` still "deferred to production runtime" (commented out, `main.py:38-41`); `/api/scheduler/status` = 503.
- 🔴 **Mobile app is unroutable and doesn't compile** — **444 tsc errors** (vs v9's 40). 5 files renamed `.tsx → .ts` still contain JSX; `app/index.ts` is a barrel (no route); `_layout.tsx` imports 2 missing shell components; `assets/` missing; `expo-asset` missing.
- 🔴 **AI modules still shipped + wired** — `intelligence/` (52 py), `prediction/` (16), `recommendation/` (28), `platform/` (18); mobile `features/predictions/` still mounted as the **"Predict" tab**.
- 🟠 **43 of 79 mobile API paths are phantom** (vs v9's 33) — the new predictions module added ~10.
- 🟠 **Docs still overclaim** — PROJECT_STATUS marks "Phase 7 Scheduler Complete" while the scheduler never runs and sync writes nothing.

### The bottom line
OpenCode did **good, narrow, verifiable work** (cache/ETag/tests) and honestly logged its limits ("live DB pending — no Docker daemon", "Migration 003 not yet applied to live DB", "Scheduler Redis lock/queue not integrated"). But it **did not fix any of the data-path blockers**, and the **mobile regressions are pre-existing from the Zaro v4 baseline** (OpenCode touched 0 mobile files). The codebase is **still not buildable end-to-end**: an empty database powers an app that doesn't compile.

---

## 2. Session Log Analysis (session-ses_0387.md)

### 2.1 What OpenCode did
- **Model:** DeepSeek V4 Flash Free (New) | **Duration:** ~3h17m (17:05 → 20:22 local) | **~94 tool calls** (33 bash, 28 edit, 10 read, 8 grep, 4 write, 1 todowrite)
- **Environment:** Windows / PowerShell; venv `C:\Users\-\AppData\Local\Temp\opencode\mma-venv`
- **Scope (verified via git diff):** **177 backend files changed (+3836/−2601), 0 mobile files.** New files: `src/api/cache.py`, `src/api/etag.py`, `src/middleware/redis.py`, `src/sync/cache_invalidation.py`, `alembic/versions/003_phase8_performance.py`, `tests/unit/test_api_cache.py`, `tests/unit/test_etag.py`, `tests/unit/test_sync_cache_invalidation.py`, `src/domain/models/` shims.
- **Direct edits (~10 files):** `src/api/v1/fighters.py`, `events.py`, `fights.py`, `other.py`, `src/sync/engine.py` (cosmetic), `PROJECT_STATUS.md`, `PERFORMANCE.md`.
- **Commands run:** `pytest -q` (last = **300 passed**), `ruff check src` (clean), `alembic upgrade head --sql` (**offline SQL only — never applied to a live DB**).
- **Final summary (verbatim, honest):** "Migration 003 not yet applied to live DB — SQL verified offline; needs one Postgres run", "Scheduler Redis lock/queue not integrated — wiring pending", "Notifications channels pending".

### 2.2 Problems OpenCode identified but chose NOT to fix
1. **`sync.py` API mismatch** — session log: *"Let me not worry; that's a top-level script possibly from the old codebase port."* — **still broken in this zip**.
2. **Migration 003 never applied to a live DB** — logged as "Medium"; consequence: migration drift (auth tables, rankings columns) went unseen.
3. **Scheduler Redis integration** — logged as "Medium", not done.
4. **Notifications channels** — logged as "Medium", not done.

---

## 3. Backend Verification (all run, all evidence below)

### 3.1 Compile + Import
```
$ python -m compileall -q src tests sync.py scheduler.py   → clean (no errors)
$ python -c "from src.api.main import app"                  → imports OK
OpenAPI paths: 91 total; 73 under /api/v1
```
(v9 had 117 route objects; v10 has 91 OpenAPI paths — some endpoints merged/consolidated, e.g. favorites under `/me/favorites/*`.)

### 3.2 Migrations on fresh Postgres 15
```
$ alembic upgrade head  (on fresh mma_v10 DB)
Running upgrade  -> 001, Initial schema
Running upgrade 001 -> 002, Phase 6 support tables + syncable columns
Running upgrade 002 -> 003, Phase 8 performance indices
→ OK, no DuplicateColumnError. 19 tables created.
```
**But: ZERO auth tables.** `users`, `user_sessions`, `favorite_fighters`, `favorite_events`, `watchlist_events`, `notifications`, `devices` — none exist. Migration 001 creates 14 data tables; 002 adds 4 support tables; **`003_auth_tables.py` (which existed in v9) was deleted in this repo** and nothing replaced it.

### 3.3 THE SYNC WRITE-PATH TEST (the big one)

**Row counts BEFORE: fighters=0, events=0, rankings=0, sync_runs=0**

**Attempt 1 — documented entry point:**
```
$ python sync.py --full --provider espn
SyncPlan.__init__() got an unexpected keyword argument 'entity_types'   ← sync.py:151
```
`sync.py` still uses the wrong API (`SyncPlan(entity_types=...)`, `SyncEngine(context=...)`, `SyncContext(db=...)`).

**Attempt 2 — the REAL engine API, properly wired (9-job registry + FullSyncPlan + AsyncSession):**
```
Bulk resolve failed for promotion: database "mma" does not exist      ← then fixed by creating DB
[SQL: INSERT INTO promotions (...) VALUES (...)]
asyncpg.exceptions.DatatypeMismatchError: column "first_event_date" is of type date but
expression is of type character varying
Critical job failed: promotion. Aborting plan 'full_sync'.
RESULT: SyncStatus.FAILED
```

**Row counts AFTER: fighters=0, events=0, rankings=0, sync_runs=0, promotions=0, weight_classes=0**

**This is the deepest root cause found across all five iterations:**
- The engine **works** — it fetched 25 real promotions from ESPN, built proper ORM objects, issued a real bulk INSERT.
- The **model says** `first_event_date: Mapped[str | None] = mapped_column(String(20))` (`src/db/models/core.py:32`)
- The **migration created** `sa.Column("first_event_date", sa.Date())` (`001_initial_schema.py:31`)
- **Model ↔ migration drift** → every promotion insert fails → plan aborts before any other entity runs.

**Schema-drift scan (all migrated tables):**

| Table | Drift |
|---|---|
| promotions | **first_event_date model=STRING vs migration=DATE** (fatal), fanart_urls model=TEXT vs JSON, synced_at/source_provider/version missing |
| events | **time_utc model=STRING vs migration=TIME** (fatal), synced_at/source_provider/version missing |
| fighters | synced_at/source_provider/version missing |
| rankings | **source_provider/version/updated_at missing** (→ the 500) |
| statistics | updated_at missing |
| sync_runs | 7 columns missing (total_inserted, total_updated, total_skipped, total_errors, api_calls, duration_ms, updated_at) |
| sync_jobs | duration_ms model=INT vs migration=FLOAT, updated_at missing |
| venues / weight_classes / competitors / external_ids / dead_letters | synced_at/source_provider/version/updated_at/matched_by missing |

**TOTAL: 14/14 tables have model↔migration drift.** Migration 001 was auto-generated from an older model state; models evolved; the migration was never regenerated. **No sync can ever write until this is fixed.**

### 3.4 Live endpoint results (uvicorn on Postgres, all tested)

| Endpoint | Result | Cause |
|---|---|---|
| `POST /api/v1/auth/register` | **500** | `relation "users" does not exist` — auth tables never migrated |
| `POST /api/v1/auth/login` | **500** | same |
| `GET /api/v1/rankings` | **500** | `column rankings.source_provider does not exist` |
| `GET /api/v1/champions` | **404** | no route |
| `GET /api/v1/title-defenses` | **404** | no route |
| `GET /api/v1/events` | **200** `[]` | empty DB |
| `GET /api/v1/fighters?q=jon` | **200** `[]` | empty DB |
| `GET /api/v1/search?q=jon` | **200** `[]` | empty DB |
| `GET /api/v1/me/favorites` | **401** | auth required (expected) |
| `GET /api/scheduler/jobs` | **200** — 7 jobs listed | real config |
| `GET /api/scheduler/status` | **503** | "SyncManager not initialized" (deferred) |
| `GET /health` | **200** | ✅ |
| `GET /health/database` | **200 healthy** | ✅ (v9 bug FIXED) |
| `GET /health/ready` | **200** (database healthy, redis failed) | ✅ graceful (v9 bug FIXED) |
| `GET /api/v1/events` (ETag flow) | **200 → 304** | ✅ OpenCode's cache verified live |

### 3.5 Test suite — the big improvement

| Version | Passed | Failed | Errors | Collected |
|---|---|---|---|---|
| v7 (zip 2) | 212 | 30 | 17 | 259 |
| v8 (zip 3) | 212 | 30 | 17 | 259 |
| v9 (zip 4) | 212 | 30 | 17 | 259 |
| **v10 (zip 5, OpenCode)** | **300** | **0** | **0** | **300** |

**What fixed it:** OpenCode fixed the `tests/conftest.py` fixtures-path bug (`parent.parent` → `parent`) and added 20 new tests (ETag, cache, invalidation). **Why it's still misleading:** the auth e2e tests run on **SQLite in-memory + `Base.metadata.create_all`**, which creates auth tables directly from models — **bypassing the broken migrations entirely**. Hence 24/24 auth tests pass while live register 500s. The suite validates logic, not deployment.

---

## 4. Mobile Verification

### 4.1 Structure (all pre-existing from Zaro v4 baseline — OpenCode touched 0 mobile files)

The v10 mobile is a **major reorganization that broke v9's working state**:

**REMOVED vs v9:** `app/index.tsx`, `app/events.tsx`, `app/fighters.tsx`, `app/rankings.tsx`, `app/search.tsx`, `app/profile.tsx`, `app/watchlist.tsx`, `app/notifications.tsx` (all route files), `assets/icon.png`, `assets/splash.png`, `assets/adaptive-icon.png`, `components/shell/MaintenanceScreen.tsx`, `components/shell/OfflineBanner.tsx`. (`app/_infra.ts` — v9's dead barrel — was actually removed, good.)

**RENAMED `.tsx → .ts` (still contain JSX → broken):** `app/analytics/AnalyticsManager`, `app/notifications/NotifManager`, `design-system/images/index`, `design-system/stories/index`, `features/fighters/theme/index`, `features/rankings/theme/index`.

**ADDED:** `features/predictions/` (full AI module), `features/events/components/FightPredictionCard.tsx`, `OddsCard.tsx`.

### 4.2 Hard numbers
- **npm install:** ✅ completes (616 packages)
- **`npx tsc --noEmit`: 444 errors** (vs v9's 40) — breakdown:
  - `design-system/stories/index.ts` — **241** (JSX in .ts, minified)
  - `design-system/images/index.ts` — **127** (JSX in .ts)
  - `features/rankings/theme/index.ts` — **40** (JSX in .ts)
  - `features/fighters/theme/index.ts` — **27** (JSX in .ts)
  - `app/notifications/NotifManager.ts` — 4, `app/analytics/AnalyticsManager.ts` — 4, `features/predictions/index.ts` — 1
- **expo export (android):** ❌ fails — **`expo-asset` missing from package.json** (v8's bug, REGRESSED; v9 had it)
- **expo export (web):** ❌ fails — `react-native-web` missing
- **Routes:** `app/` has `index.ts` (barrel, **no default export**) + `_layout.tsx` + `+not-found.tsx` only → **no expo-router routes exist** → app cannot boot
- **`_layout.tsx` imports `MaintenanceScreen` and `OfflineBanner` from `components/shell/`** — **both missing** (only ErrorBoundary + SplashScreen exist) → import error at boot
- **`assets/` dir missing** but `app.json` references `./assets/icon.png` etc. → build fails

### 4.3 AI scope (user explicitly rejected AI)
- Backend: `intelligence/` (52 py), `prediction/` (16), `recommendation/` (28), `platform/` (18) — **all still present**, fully functional code
- Mobile: `features/predictions/` **mounted as "Predict" tab** (`MainNavigator.tsx:53`: `<Tab.Screen name="predictions" component={PredictionsStack} .../>`)
- 16 mobile API calls hit `/v1/predictions/*`-style paths that have no backend routes

### 4.4 Contract diff (mobile calls vs live OpenAPI)
- Mobile unique API paths: **79** | Backend v1 paths: **73** | Covered: 36 | **Phantom: 43** (vs v9's 33)
- Phantom categories: ~16 AI/predictions (should be deleted), ~4 favorites prefix mismatch (`/v1/favorites` vs backend `/v1/me/favorites`), ~7 watchlist generic-vs-concrete, ~16 genuinely missing

### 4.5 Config
- **API base URL still placeholder:** `https://api.mma-platform.com/api` (prod) / `http://localhost:8000/api` (dev)
- **App icons:** `assets/` missing entirely → app.json references nonexistent icons

---

## 5. Verdict Table (v9 issue → v10 status)

| # | v9 issue | v10 status | Evidence |
|---|---|---|---|
| 1 | Zip corruption (142 placeholder files) | ✅ **FIXED** | 0 placeholders; package.json/tsconfig valid |
| 2 | Backend won't compile | ✅ **FIXED** | compileall clean; app imports; 91 paths |
| 3 | Sync writes zero rows | 🔴 **STILL BROKEN — deeper cause found** | engine reaches ESPN + DB, dies on `first_event_date` type drift; rows 0→0 |
| 4 | `SyncPlan(entity_types=...)` crash in sync.py | 🔴 **STILL BROKEN** | `sync.py:151` — OpenCode dismissed it in its own log |
| 5 | Auth register/login 500 (no tables) | 🔴 **STILL BROKEN — WORSE** | **`003_auth_tables.py` deleted**; 0 auth tables in any migration; register 500 |
| 6 | Rankings 500 (source_provider missing) | 🔴 **STILL BROKEN** | `rankings.source_provider does not exist`; 002 loop still omits rankings |
| 7 | App can't bundle (expo-asset missing) | 🔴 **STILL BROKEN (REGRESSED)** | expo-asset absent from package.json (v9 had it) |
| 8 | AI modules present | 🔴 **STILL BROKEN** | 114 py files + Predict tab wired |
| 9 | Tests 212/30/17 | ✅ **FIXED — 300/0/0** | reproduced; conftest fixtures-path fix |
| 10 | 33/136 phantom calls | 🟠 **WORSE — 43/79** | new predictions module added ~10 |
| 11 | Placeholder API base URL | 🟡 **UNCHANGED** | api.mma-platform.com |
| 12 | 1×1 transparent icons | 🟡 **WORSE** | assets/ deleted entirely |
| 13 | Mobile unroutable | 🔴 **WORSE** | 444 tsc errors, 0 route files, missing shell components |
| 14 | Scheduler commented out | 🟠 **UNCHANGED** | `main.py:38-41` "deferred"; /scheduler/status 503 |
| 15 | /health/database broken | ✅ **FIXED** | returns healthy with DB up |
| 16 | Docs overclaim | 🟠 **PARTIAL** | PROJECT_STATUS honestly lists pending items, but "Phase 7 Scheduler Complete" masks a non-running scheduler |

**Regression check (v8 fixes that must stay fixed):** zip integrity ✅ | backend boots ✅ | migrations apply ✅ | auth register 201 ❌ (**REGRESSED** — now 500) | mobile routes ❌ (**REGRESSED**) | _layout provider tree ✅ | tsc 40-in-one-file ❌ (**REGRESSED** to 444 in 7 files).

---

## 6. New Issues Introduced (by this iteration)

1. 🔴 **`003_auth_tables.py` deleted** → auth tables have NO migration anywhere. (Repo baseline, not OpenCode — but the delivered zip ships it.)
2. 🔴 **Mobile route files deleted, `.tsx→.ts` JSX renames** → 444 tsc errors, unroutable app. (Zaro baseline, not OpenCode.)
3. 🔴 **`expo-asset` removed** from package.json (was present in v9).
4. 🔴 **`assets/` directory removed** entirely.
5. 🟠 **`features/predictions/` added + mounted as "Predict" tab** — more AI scope, more phantom API calls.
6. 🟠 **Mobile API path count grew** 33 → 43 phantoms.
7. 🟡 `app.json` now references icons that don't exist.

---

## 7. Zip Integrity Report

| Check | Result |
|---|---|
| Total files | 1766 (extracted); 711 tracked non-node_modules |
| Placeholder scan ("This file could not be retrieved") | **0 files** ✅ |
| package.json / tsconfig.json | valid JSON ✅ |
| mobile/assets/ | ❌ **MISSING** |
| Git history | baseline commit "Initial upload" Aug 2; OpenCode's 177-file diff = the session's edits; **0 mobile files changed** |
| Fallback zip | byte-identical (MD5 `61861ec1…`) ✅ |

---

## 8. Remaining Gap Analysis (vs the full remediation plan)

| Phase | Goal | Status |
|---|---|---|
| A | Backend compiles + boots | ✅ DONE |
| B | Data flows (sync writes to DB) | 🔴 **BLOCKED** — model↔migration drift (14/14 tables); sync.py wrong API; auth tables unmigrated |
| C | App boots (routes, compile) | 🔴 **BLOCKED** — 444 tsc errors, no routes, missing deps/assets |
| D | Contract gap (43 phantom calls) | 🟠 36/79 covered; predictions module should be deleted not implemented |
| E | User features real (favorites/watchlist/notifications) | 🔴 auth 500 → all user features dead |
| F | Tests meaningful (Postgres-backed) | 🟡 300 green but SQLite-masked; needs Postgres CI + migration-coverage tests |
| G | Production polish (real base URL, icons, docs) | 🟡 placeholder base URL; assets missing; docs improved but still mask blockers |

---

## 9. Updated Prioritized Action Plan (file-level)

### Phase 0 — Demand a clean delivery (30 min)
Acceptance: mobile/ has `assets/` (3 icons), all `.ts` files containing JSX renamed `.tsx`, `expo-asset` in package.json, all route files present, no `prediction/`/`recommendation/`/`intelligence/`/`platform/` dirs, no `features/predictions/`.

### Phase 1 — Fix schema drift so sync can write (1 day) — THE critical path
1. `backend/src/db/models/core.py:32` — change `first_event_date` to `Mapped[date | None] = mapped_column(Date)` (model must match migration; parser must produce `date`)
2. **Or regenerate migrations**: delete 001–003, `alembic revision --autogenerate`, and **verify `alembic upgrade head` on fresh Postgres** — the only real fix
3. **Restore `003_auth_tables.py`** (recover from v9) OR fold auth tables into the regenerated 001 — **register/login must work on Postgres**
4. `002_phase6_support.py` syncable-columns loop — add `"rankings"` and `"statistics"` (or regenerate)
5. `sync.py` — rewrite to the real API: `SyncEngine(jobs=registry)` + `execute(plan, provider, db_session=session)` using `async_session_factory()` (mirror §3.3 attempt-2 wiring)
6. `main.py:38-41` — construct `SyncManager` with a real `SyncContext` + session factory
7. Fix `sync_runs` missing columns (total_inserted etc.) in migration
8. **Proof:** `python sync.py --full` → fighters/events/rankings/sync_runs row counts > 0; `/api/v1/rankings` returns 200

### Phase 2 — Make auth + user features real on Postgres (0.5 day)
1. After Phase 1.3: `POST /auth/register` = 201, `/auth/login` = 200 (verify live)
2. `GET /me/favorites` CRUD against real tables
3. Add Postgres-backed integration tests (override DATABASE_URL; run migrations in fixture)

### Phase 3 — Mobile: restore bootability (1–2 days)
1. Rename back to `.tsx`: `design-system/stories/index`, `design-system/images/index`, `features/fighters/theme/index`, `features/rankings/theme/index`, `app/analytics/AnalyticsManager`, `app/notifications/NotifManager`
2. Restore `assets/icon.png`, `splash.png`, `adaptive-icon.png` (or remove refs from app.json)
3. Add `expo-asset` (+ `react-native-web` for web) to package.json
4. Restore route files `app/index.tsx`, `events.tsx`, `fighters.tsx`, `rankings.tsx`, `search.tsx`, `profile.tsx`, `watchlist.tsx`, `notifications.tsx` with default exports (recover from v9)
5. Create `components/shell/MaintenanceScreen.tsx` + `OfflineBanner.tsx` (or strip imports)
6. **Proof:** `tsc --noEmit` = 0; `expo export --platform android` succeeds

### Phase 4 — Kill the AI scope (0.5 day)
1. Delete: `backend/src/intelligence/`, `backend/src/prediction/`, `backend/src/recommendation/`, `backend/src/platform/`
2. Delete: `mobile/features/predictions/`, `mobile/features/events/components/FightPredictionCard.tsx`, `OddsCard.tsx`
3. Remove `predictions` Tab.Screen from `MainNavigator.tsx`; remove predictions exports from `features/index.ts`
4. Delete the 16 phantom prediction API calls
5. Re-diff contract: phantom count should drop to ~25 (real missing endpoints only)

### Phase 5 — Contract gap + polish (1–2 days)
1. Fix favorites prefix: mobile `/v1/favorites` → backend `/v1/me/favorites`
2. Align watchlist calls with the backend's concrete design
3. Set real API base URL via `app.config.ts` env (EXPO_PUBLIC_API_URL)
4. Update PROJECT_STATUS/PRODUCTION_AUDIT with verified numbers (300 tests, 91 paths, 0 rows synced — honest)

### Phase 6 — Test infrastructure that reflects reality (0.5–1 day)
1. `tests/conftest.py`: add Postgres-backed fixtures (run alembic on a scratch DB)
2. Add a migration-coverage test: `alembic upgrade head` on fresh DB + assert auth tables exist + assert no model↔migration drift (compare metadata vs `inspect`)
3. CI: run pytest against both SQLite (fast) and Postgres (real)

---

## 10. Continue with OpenCode/Zaro, or take over manually?

**Recommendation: take over the backend fix manually; keep AI tooling only for narrow, verifiable tasks.**

Reasoning:
- OpenCode's 3h17m produced real, verified value (cache, ETag, 300 green tests) — but it **explicitly declined to fix the sync entry point** ("let me not worry"), and the delivery chain (Zaro re-export) keeps **re-breaking things it never touched** (mobile, migrations).
- The remaining blockers are **small, named, mechanical**: 1 type fix, 1 migration restoration, 1 sync.py rewrite, 6 file renames, 2 missing components, 1 npm dep. Each is a one-liner to a few lines. Phase 1 + 2 + 4 can be done in ~1.5 days.
- The risk of another round-trip: the next re-export re-breaks mobile again (it has 3 times in a row: v8 expo-asset, v9 40 errors, v10 444 errors).

**If you continue with an AI tool:** the session log shows it works best with ONE narrow, verifiable task and a runnable acceptance test (its cache work was exactly that). Gate the corrective prompt on: *"the repo must pass `python sync.py --full && SELECT count(*) FROM fighters > 0` on fresh Postgres"* — not on doc claims.

---

## 11. Evidence Trail (commands + outputs)

```
# Zip integrity
unzip -l from-github(4).zip | wc -l                      → 1766 files
grep -rl "This file could not be retrieved" . | wc -l     → 0

# Compile + import
python -m compileall -q src tests sync.py scheduler.py    → clean
python -c "from src.api.main import app"                  → OK, 91 OpenAPI paths (73 v1)

# Migrations on fresh Postgres
alembic upgrade head                                      → 001 → 002 → 003 OK; 19 tables; NO auth tables

# Sync (documented entry point)
python sync.py --full --provider espn                     → SyncPlan unexpected kwarg 'entity_types' (sync.py:151)

# Sync (real engine API — proves write path + exposes fatal drift)
SyncEngine(jobs=registry); FullSyncPlan(); ESPNProvider() → fetched 25 promotions, INSERT failed:
DatatypeMismatchError: column "first_event_date" is of type date but expression is of type character varying

# Row counts before/after sync
fighters=0 events=0 rankings=0 sync_runs=0 promotions=0 weight_classes=0   (unchanged)

# Live endpoints
POST /api/v1/auth/register  → 500 (relation "users" does not exist)
POST /api/v1/auth/login     → 500
GET  /api/v1/rankings       → 500 (column rankings.source_provider does not exist)
GET  /api/v1/events         → 200 []
GET  /api/scheduler/jobs    → 200 (7 jobs)
GET  /api/scheduler/status  → 503 (SyncManager not initialized)
GET  /health/database       → 200 healthy
GET  /api/v1/events (ETag)  → 200, then 304 on If-None-Match

# Tests
python -m pytest -q                                     → 300 passed, 0 failed, 0 errors
python -m pytest tests/auth/test_e2e_flows.py -q        → 24 passed (SQLite in-memory + create_all)

# Mobile
npm install                                             → OK (616 pkgs)
npx tsc --noEmit                                        → 444 errors (241+127+40+27+4+4+1)
npx expo export --platform android                      → FAIL (expo-asset missing)
npx expo export --platform web                          → FAIL (react-native-web missing)

# Contract diff
Mobile paths 79 vs backend 73 → covered 36 → PHANTOM 43 (16 AI, 4 favorites prefix, 7 watchlist, ~16 missing)

# OpenCode scope (git)
git diff --name-only HEAD | grep -c '^mobile/'          → 0
git diff --name-only HEAD | wc -l                        → 177 (all backend)
```

---

## 12. Final Verdict

**This version is NOT good enough to build on end-to-end, but it is the first version where the backend's quality bar (tests, caching, health) is genuinely production-adjacent.** The single decision point is data: until `python sync.py --full` writes rows to Postgres, every screen in the app shows empty lists. That fix is now fully diagnosed — it is 5–8 mechanical changes, roughly one focused day — and this report names every file and line.

**Do next:** (1) have me fix Phase 1 + 2 + 4 directly (backend data path + auth + AI removal, ~1.5 days), (2) hand only the mobile repair (Phase 3) back to Zaro with acceptance criteria (`tsc --noEmit` = 0, `expo export` succeeds), (3) refuse further deliveries until the zip contains assets, `.tsx` extensions, no AI modules, and a passing live-DB sync — verified by running, not by reading PROJECT_STATUS.md.
