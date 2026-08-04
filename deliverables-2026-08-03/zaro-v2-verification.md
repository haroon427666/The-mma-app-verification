# Zaro AI "Corrected" Monorepo — Verification Report

**Date:** 2026-08-03
**Zip analyzed:** `1785751865443000000199_from-github (2).zip` (821 KB, extracted: `mma-app-zaro-ai-repo`)
**Prior audit:** `zaro-ai-audit-analysis.md` (v6) — findings on `from-github (1).zip`
**Method:** Live verification — compileall, app import, full Postgres 15 setup, Alembic migrations, uvicorn boot, live HTTP endpoint tests, pytest suite, `tsc --noEmit`, zip-integrity checks, cross-referenced API-contract diff.

> **TL;DR:** The code that *was* fixed, got fixed. But this "corrected" zip is **worse than the original in two critical ways**: (1) the zip export itself is corrupted — 142 files (including `package.json` and `tsconfig.json`) are placeholder text, and the `assets/` directory is missing entirely, so **the mobile app cannot be installed or booted at all**; (2) live Postgres testing reveals the **auth layer has NO database tables** (register/login 500), the **migrations fail on a fresh database** (duplicate column), and the **sync engine cannot write data** (entrypoint crashes on API mismatch; scheduler jobs never persist). The docs' "production-ready, 48 tests, 91% coverage" claims remain fiction.

---

## 0. Executive Summary

| Dimension | Previous zip (v1) | This zip (v2) | Trend |
|---|---|---|---|
| Backend `pipeline.py` syntax error | 🔴 Broken | ✅ **FIXED** | 🟢 |
| Backend app import | 🔴 Failed (SyncCheckpoint) | 🔴 **Still fails** (missing `__tablename__` — same bug) | 🔴 |
| App import after 1-line patch | — | ✅ Works (95 routes) | 🟢 |
| Scheduler wired into app | 🔴 Commented out | 🔴 **Still commented out** ("deferred to production runtime") | 🔴 |
| Sync entrypoint (`sync.py --full`) | 🔴 | 🔴 **Crashes** — `SyncPlan()` API mismatch | 🔴 |
| Scheduler jobs persist to DB | 🔴 | 🔴 **Never write** — fetch→count→return only | 🔴 |
| Auth tables in migrations | 🔴 | 🔴 **Missing entirely** — register/login 500 | 🔴 |
| Migrations run on fresh DB | ⚠️ untested | 🔴 **Fail** — duplicate `synced_at` column | 🔴 |
| Rankings endpoint | — | 🔴 **500** — model vs migration drift (`updated_at` missing) | 🔴 |
| Mobile route files | 🔴 none | ✅ **FIXED** — 8 route files wired | 🟢 |
| MaintenanceScreen / OfflineBanner | 🔴 missing | ✅ **FIXED** — now exist (but **duplicated** in SplashScreen) | 🟡 |
| JSX-in-.ts files | 🔴 4 files | ✅ **FIXED** — renamed to `.tsx` | 🟢 |
| Mobile `tsc --noEmit` | ~440 errors | 718 total, but **only 28 in valid code** (690 from corrupt placeholders) | 🟡 |
| `package.json` / `tsconfig.json` | ✅ valid | 🔴 **CORRUPTED in zip** (82-byte placeholders) | 🔴 |
| `assets/` dir | ⚠️ | 🔴 **Missing** — Expo cannot boot | 🔴 |
| Phantom API routes | 🔴 ~20 | 🔴 **Still missing** (55/90 mobile paths unmatched) | 🔴 |
| Favorites/profile stubs | 🔴 | 🟡 Partial — `/v1/watchlist/*` real, `/v1/me/favorites/*` still stubs | 🟡 |
| AI modules removed | 🔴 present | 🔴 **Still present** — but 100% corrupted (empty shells) | 🟡 |
| Test suite | 212 pass / 30 fail / 17 err (after fixes) | **212 pass / 30 fail / 17 err** (after 1-line fix) | 🔴 same |
| "48 tests, 91% coverage" claim | False | **Still false** (259 tests, 47 fail/err) | 🔴 |

**Verdict: NOT buildable in the state delivered.** The backend compiles but cannot be populated (sync broken) and cannot authenticate (no user tables). The mobile app cannot even be installed (corrupt manifest files, missing assets). However — and this is the crucial nuance — **the fixes are all small and well-understood**: this is a *scaffolding-integrity* problem, not a *missing-architecture* problem. Estimated 5–8 focused days to reach a genuinely working end-to-end build (see §7).

---

## 1. What the Zip Actually Contains

```
mma-app-zaro-ai-repo/
├── backend/                  # FastAPI backend (395 files, 0 corrupt ✅)
│   ├── src/
│   │   ├── api/              # main.py + v1/ routers (auth, events, fighters, fights,
│   │   │                     #   notifications, other, recommendations, search, users, watchlist)
│   │   ├── auth/             # JWT, Argon2, RBAC, sessions, tokens
│   │   ├── db/               # models/ (8 auth + 7 core + 6 support), repositories, session, UoW
│   │   ├── providers/        # espn/ (client+parsers+jobs), tsdb/, octagon/, registry, merge
│   │   ├── scheduler/        # manager, jobs, locks, queue, retry, live_mode, monitor, notifier
│   │   ├── sync/             # engine, pipeline, plan, upserts/, state, retry, dead_letter (35 files)
│   │   ├── monitoring/       # health, metrics, alerts, providers, config_validator
│   │   ├── middleware/       # auth, cache, rate_limit
│   │   └── services/         # auth_service, fighter_service
│   ├── alembic/              # versions/001_initial_schema.py, 002_phase6_support.py
│   ├── tests/                # 259 tests across api, auth, contract, integration, scheduler, unit
│   ├── scheduler.py          # standalone entry point (SyncContext = dummy!)
│   ├── sync.py               # CLI entry point (CRASHES — see §4)
│   └── *.md                  # 15 doc files (ARCHITECTURE, PROJECT_STATUS, DATA_CONTRACT, etc.)
├── mobile/                   # Expo/React Native app (433 files, 75 CORRUPT 🔴)
│   ├── app/                  # expo-router: index, events, fighters, rankings, search, profile,
│   │                         #   notifications, watchlist + infra (networking, bootstrap, offline, ...)
│   ├── components/           # shell (Splash, Maintenance, Offline), auth, screens
│   ├── features/             # events, fighters, home, rankings, search, watchlist, notifications,
│   │                         #   profile, predictions, recommendations + design-system
│   └── package.json          # 🔴 CORRUPT — 82-byte placeholder
│   └── tsconfig.json         # 🔴 CORRUPT — 82-byte placeholder
│   └── assets/               # 🔴 MISSING entirely (referenced by app.json)
├── prediction/               # AI fight prediction (16 files, 20/20 CORRUPT)
├── recommendation/           # AI recommendations (28 files, 28/28 CORRUPT)
├── intelligence/             # AI embeddings/rankings engine (52 files, 0 corrupt)
├── platform/                 # data platform glue (18 files, 19/19 CORRUPT)
└── docs/blueprint/           # 4 planning docs
```

**Zip integrity — the single biggest problem:**

| Area | Files | Corrupt | % |
|---|---|---|---|
| `backend/` | 395 | 0 | 0% ✅ |
| `mobile/` | 433 | 75 | 17% 🔴 |
| `prediction/` | 20 | 20 | 100% 🔴 |
| `recommendation/` | 28 | 28 | 100% 🔴 |
| `platform/` | 19 | 19 | 100% 🔴 |
| `intelligence/` | 58 | 0 | 0% ✅ |
| **Total** | **957** | **142** | **15%** |

A corrupt file contains exactly: `This file could not be retrieved. Please contact support if the problem persists.` (82 bytes). **The corruption is inside the zip** — verified via `unzip -p` direct stream (same CRC `84df53dd` for both `package.json` and `tsconfig.json`). This is an **export-side failure** from Zaro AI / GitHub's tooling, not a sandbox artifact.

**Critical consequence:** `mobile/package.json` and `mobile/tsconfig.json` are both corrupt → `npm install` and `npx tsc` **cannot run against the delivered zip**. `mobile/assets/` (icon.png, splash.png, adaptive-icon.png) is missing → `app.json` references nonexistent files → **Expo cannot boot**. The mobile app as shipped is **uninstallable and unbootable**.

---

## 2. Verdict per Previously-Reported Issue

| # | Previous finding (v6 audit) | Status | Evidence |
|---|---|---|---|
| B1 | `backend/src/sync/pipeline.py:97` broken f-string | ✅ **FIXED** | `compileall src/` exits 0; line now `f"reason={decision.reason} "` |
| B2 | `SyncCheckpoint` missing `__tablename__` → app import fails | 🔴 **STILL BROKEN** | `from src.api.main import app` → `InvalidRequestError: Class SyncCheckpoint does not have a __table__ or __tablename__` (support.py:76) |
| B3 | Scheduler commented out in `main.py` lifespan | 🔴 **STILL BROKEN** | main.py:31-33 `# manager = SyncManager(context)` / `logger.info("SyncManager — deferred to production runtime")` |
| B4 | AI modules present (user rejected) | 🟡 **STILL PRESENT, but 100% corrupted** | `prediction/` (20/20), `recommendation/` (28/28), `platform/` (19/19) are placeholder files; `intelligence/` intact (52). Backend does NOT import them; but `/v1/recommendations` routes + mobile predictions/recommendations features still exist |
| B5 | Favorites/profile stubs | 🟡 **PARTIALLY FIXED** | `/v1/watchlist/*` now does real DB writes (watchlist.py); `/v1/me/favorites/*` in users.py still pure stubs (`return FavoriteResponse()`, `{"status":"added"}`); notifications & recommendations still hollow |
| B6 | Backend tests — "48 passing" fiction | 🔴 **STILL FICTION** | Full suite: **212 passed / 30 failed / 17 errors** (after 1-line fix). Same numbers as v1. |
| M1 | Mobile has no route files → blank screen | ✅ **FIXED** | `app/index.tsx`, `events.tsx`, `fighters.tsx`, `rankings.tsx`, `search.tsx`, `profile.tsx`, `notifications.tsx`, `watchlist.tsx` all export real screens |
| M2 | `MaintenanceScreen`/`OfflineBanner` missing | ✅ **FIXED** (with regression) | Files now exist in `components/shell/` — but **still duplicated inside `components/shell/SplashScreen.tsx`** (same components redefined) |
| M3 | JSX-in-.ts files (~440 TS errors) | ✅ **FIXED** | `AnalyticsManager.ts→.tsx`, `NotifManager.ts→.tsx`, `images/index.ts→.tsx`, `stories/index.ts→.tsx` |
| M4 | Phantom API routes | 🔴 **STILL BROKEN** | 55/90 mobile API paths have no backend route (full list in §5) |
| M5 | `package.json` missing deps | 🔴 **NEWLY WORSE** | package.json is **corrupt** in this zip (was valid in v1). Old-version deps still lack `@react-navigation/native-stack` etc. |
| M6 | `assets/` dir | 🔴 **NEWLY BROKEN** | Missing entirely; `app.json` references `./assets/icon.png`, `./assets/splash.png`, `./assets/adaptive-icon.png` |
| M7 | Default API base URL is placeholder | 🔴 **STILL BROKEN** | `NetworkConfig.ts:5`: `baseURL: process.env.EXPO_PUBLIC_API_URL \|\| 'https://api.mma-app.com'` — a domain the user doesn't own |

---

## 3. NEW Issues Introduced / Newly Discovered

These were **not** in the v6 audit (mostly because the previous run couldn't test against a live Postgres):

### 🔴 N1 — Auth has NO database tables (register/login 500)
The `users`, `user_sessions`, `user_preferences`, `favorite_fighters`, `favorite_events`, `watchlist_events`, `notifications`, `devices` models exist in `src/db/models/auth.py`, but **no Alembic migration creates them**. After `alembic upgrade head` (19 tables), `POST /api/v1/auth/register` and `/auth/login` both return **500** with `relation "users" does not exist` in Postgres logs. This kills the **entire user layer**: auth, favorites, watchlist, notifications, profile.

### 🔴 N2 — Migrations fail on a FRESH database
`alembic/versions/001_initial_schema.py` already creates `rankings.synced_at` and `statistics.synced_at` inline (lines 219, 236). `alembic/versions/002_phase6_support.py` then unconditionally runs `op.add_column("rankings", synced_at)` (loop over 8 tables, line 148). Result on a clean DB:

```
sqlalchemy.exc.ProgrammingError: column "synced_at" of relation "rankings" already exists
```
Reproduced twice (fresh DB, drop+recreate). `alembic upgrade head` **cannot succeed as shipped**. (I verified a 3-line patch fixes it.)

### 🔴 N3 — Rankings endpoint 500s even with data
`Ranking` model inherits `SyncableMixin → TimestampMixin` (adds `updated_at`), but the migration-created `rankings` table has **only `created_at`** — no `updated_at`. So `SELECT rankings.updated_at` fails → `/api/v1/rankings`, `/rankings/mens`, `/rankings/womens`, `/rankings/p4p`, `/rankings/{division}` all return **500**.
Same drift affects `broadcasts` and `statistics` (created without `updated_at`); `competitors` has neither `updated_at` nor `synced_at`.

### 🔴 N4 — Sync engine is unreachable & cannot persist (the showstopper)
Three independent failures prove data **cannot flow** ESPN→DB through any documented path:
1. **CLI crash:** `python sync.py --full` → `TypeError: SyncPlan.__init__() got an unexpected keyword argument 'entity_types'` (sync.py:151). The CLI was written against a `SyncPlan(entity_types=..., mode=...)` API that doesn't exist — the real `SyncPlan` is a dataclass with `name/description/order` and a no-arg `__init__`. Same for `SyncEngine(context=...)` (sync.py:154,189,212) — real `SyncEngine.__init__` takes `(jobs, statestore, events, reliability)`.
2. **Scheduler jobs never write:** every job function in `src/scheduler/jobs.py` calls `ctx.espn_provider.fetch_*()` then returns `JobResult(records_inserted=len(...))` — **zero `session.add`/upsert/insert** anywhere in the file. Comments literally say "enrichment would go here" and "Upsert competitions with results" (as a comment). Even with a live event, nothing persists.
3. **No wiring:** `grep -r "FighterRepository|EventRepository" src/sync/ src/scheduler/` → **nothing**. The repository/upsert layer (`src/db/repositories/*.py`, `src/sync/upserts/*.py` — real `ON CONFLICT` upserts) exists but **nothing calls it** from the pipeline.

### 🔴 N5 — No weight-class route
`WeightClass` model + sync exist, but no router exposes `/v1/weight-classes` (404). Mobile doesn't call it, but the PRD's weight-class pages have no backend.

### 🟡 N6 — `features/fighters/theme/index.ts` uses `<Image>` without import (27 TS errors in valid code)
The `FighterAvatar` component renders `<Image>` but the file never imports it from `react-native`. Genuine syntax/import error in otherwise-valid code.

### 🟡 N7 — `features/predictions/index.ts` is a mangled single line (1 TS error)
Line 1 contains the entire file's exports with literal `\n` sequences — broken generation.

### 🟡 N8 — Duplicate shell components (regression from M2 fix)
`MaintenanceScreen` + `OfflineBanner` now exist in their own files **and** are still defined inside `SplashScreen.tsx`. The `_layout.tsx` imports from `components/shell/MaintenanceScreen` — the duplicates in SplashScreen are dead code but confusing.

### 🟡 N9 — `PRODUCTION_AUDIT.md` is corrupt
The file that was supposed to document the audit ("9.3/10 production-ready" claims) is itself a placeholder. Same for `mobile/features/watchlist/api/queries.ts` and 73 other mobile files.

### 🟡 N10 — `projects` structure still claims Phase 11 "48 tests, 91% coverage" & Phase 9 "Auth Complete"
Both false under live testing (see §6). `PROJECT_STATUS.md` is a fiction document, unchanged from v1.

---

## 4. Mobile — `tsc --noEmit` Results (reconstructed harness)

Because `package.json`/`tsconfig.json` are corrupt in the zip, I rebuilt a harness: extracted the mobile tree from the new zip, restored the **valid** v1 `package.json` + `tsconfig.json` (from `zaro-audit.zip`), `npm install` (1082 packages OK), then `npx tsc --noEmit`.

| Metric | Value |
|---|---|
| Total errors | **718** |
| Errors from corrupt placeholder files (142 files) | **690** (96%) |
| **Errors in genuinely valid code** | **28** |
| Distinct valid files with errors | 2 (`features/fighters/theme/index.ts` — 27, `features/predictions/index.ts` — 1) |

**Interpretation:** The *hand-written* code is nearly type-clean. The 718 count is dominated by parse errors (`TS1434/TS1005/TS1435`) on placeholder files. Once the zip corruption is fixed (re-export with all files), the real work is **28 errors in 2 files** — trivial.

**But:** the delivered zip cannot reach this state — `npm install` fails (no valid package.json) and Expo can't boot (no assets). The **zip must be re-exported**, not patched.

---

## 5. API Contract Gap — Mobile Calls vs Backend Routes (55 mismatches)

Cross-referenced every API path string in `mobile/` (90 unique) against the backend's 73 `/v1` routes (regex-matched, template-params normalized). **35 match, 55 don't.**

### 5.1 Phantom routes the mobile calls that DON'T exist in the backend

**AI-related (user rejected these anyway):**
```
/v1/predictions/*            (16 paths: /fight/{id}, /event/{id}, /dashboard, /history,
                              /accuracy, /saved, /highlights, /fighter/{id}, .../odds, ...)
/v1/recommendations/fighters  (exists: /v1/recommendations — but /fighters sub-route does not)
```

**Missing feature routes (would need to exist):**
```
/v1/champions               ← champions page
/v1/title-defenses          ← records page
/v1/rankings/goat           ← GOAT list
/v1/rankings/prospects      ← prospects
/v1/rankings/streaks        ← streaks
/v1/rankings/division/{d}   ← backend uses /rankings/{division}
/v1/rankings/history/{id}   ← rank history
/v1/home                    ← home feed
/v1/me/stats                ← profile stats
/v1/me/export               ← profile export
/v1/fighters/compare        ← compare (mobile Endpoints.ts also uses /v1/fighters/compare)
/v1/fighters/search         ← search (backend: /v1/search)
/v1/fighters/{id}/similar   ← similar fighters
/v1/fighters/{id}/fights    ← backend uses /history
/v1/fighters/{id}/stats     ← backend uses /statistics
/v1/fighters/{id}/achievements, /rankings, /rankings/best, /rankings/history,
/v1/fighters/{id}/stats/grappling, /stats/striking, /style-analysis, /timeline
/v1/events/{id}/fights      ← backend embeds competitions in event detail; no sub-route
/v1/events/{id}/results, /statistics
/v1/events/{id}/live
/v1/favorites/fighters/*    ← backend uses /v1/me/favorites/fighters/{fighter_id}
/v1/follows/fighters/{id}
/v1/watchlist/{t}           ← backend: /v1/watchlist/events & /fighters (no generic {t})
/v1/watchlist/events/{id}/status
/v1/watchlist/reminders
/v1/reminders, /v1/reminders/{id}
/v1/remote-config           ← not in backend
/v1/health                  ← backend: /health (no /v1 prefix)
/v1/metrics                 ← backend: /api/metrics
```

### 5.2 Confirmed working matches (35)
`/v1/events`, `/v1/events/upcoming|past|live`, `/v1/events/{id}`, `/v1/fighters`, `/v1/fighters/{id}`, `/v1/fighters/{id}/history|media|statistics`, `/v1/fights`, `/v1/fights/live|recent|upcoming`, `/v1/fights/{id}`, `/v1/rankings`, `/v1/rankings/mens|womens|p4p`, `/v1/rankings/{division}`, `/v1/promotions`, `/v1/promotions/{slug}`, `/v1/promotions/{slug}/events|fighters`, `/v1/venues`, `/v1/venues/{id}`, `/v1/venues/{id}/events`, `/v1/search`, `/v1/search/autocomplete|trending|popular`, `/v1/me`, `/v1/me/preferences`, `/v1/me/sessions`, `/v1/me/favorites`, `/v1/me/favorites/events/{id}`, `/v1/me/favorites/fighters/{id}`, `/v1/me/favorites/promotions/{slug}`, `/v1/me/watchlist`, `/v1/me/watchlist/events/{id}`, `/v1/notifications/*`, `/v1/auth/*`, `/v1/recommendations`.

### 5.3 Home screen specifically
`features/home/api/endpoints.ts` fires 7 parallel calls; **5 of 7 are phantom**: `/v1/home` (main feed — returns nothing), `/v1/fighters/trending`, `/v1/fights?is_title=true`, `/v1/recommendations/fighters`, `/v1/predictions/highlights`. Only `/v1/events?status=LIVE` and `/v1/events/upcoming` work. **The home screen will render empty even when the backend is healthy.**

---

## 6. Live Backend Verification (Postgres 15 + uvicorn)

Environment: Postgres 15 cluster started, `mma` DB created, alembic migrations applied (after 1-line `__tablename__` fix + 002 duplicate-column patch).

### 6.1 Boot & health
```
/health/live   → 200 {"status":"healthy"}
/health/ready  → 200 {"status":"failed","checks":{"database":{"status":"failed"}}}  ← DB check FAILS
```
(`/health/ready` reports database FAILED even though migrations ran — the readiness check expects something the fresh DB doesn't have; needs the scheduler/data check.)

### 6.2 Endpoint matrix (fresh, empty DB)

| Endpoint | Status | Body |
|---|---|---|
| `/api/v1/events` | 200 | `{"items":[],"total":0,...}` |
| `/api/v1/events/upcoming` | 200 | `[]` |
| `/api/v1/events/past` | 200 | `{"items":[],...}` |
| `/api/v1/events/live` | 200 | `[]` |
| `/api/v1/fights` | 200 | `{"items":[],...}` |
| `/api/v1/fighters` | 200 | `{"items":[],...}` |
| `/api/v1/search?q=islam` | 200 | `{"query":"islam","total":0,"results":[]}` |
| `/api/v1/promotions` | 200 | `[]` |
| `/api/v1/venues` | 200 | `{"items":[],...}` |
| `/api/v1/rankings` | **500** | missing `rankings.updated_at` (N3) |
| `/api/v1/rankings/mens` | **500** | same |
| `/api/v1/rankings/p4p` | **500** | same |
| `/api/v1/weight-classes` | **404** | route doesn't exist (N5) |
| `/api/v1/champions` | **404** | phantom (mobile calls it) |
| `/api/v1/rankings/goat` | **500** | hits rankings read → N3 |
| `/api/v1/auth/register` | **500** | `relation "users" does not exist` (N1) |
| `/api/v1/auth/login` | **500** | same |

### 6.3 Test suite (patched copy, full run)
```
30 failed, 212 passed, 17 errors, 17 warnings in 14.00s
```
- **Passing (212):** all unit tests, scheduler tests (43/43), most API tests, JWT/RBAC unit tests, repository tests.
- **Failing (30):** parser DTO tests (`FighterDTO.is_active` missing — test/code contract drift), sync-state tests (`SyncState.last_sync_at` missing), Redis-down tests (fake Redis mismatch), cache invalidation tests, metrics/sync-trigger contract tests, `test_orm_to_schema_no_leak` + `test_schema_from_attributes_mode` (pydantic config drift), auth e2e errors (17 — all trace to missing `users` table).
- The claim "48 tests, 91% coverage" is **false**: 259 tests exist; 47 fail/error.

### 6.4 Why the sync can't populate data (proven)
1. `python sync.py --full --provider espn --entity promotion` → **crash** at `SyncPlan(entity_types=...)` (API mismatch).
2. Scheduler job functions (`jobs.py`) contain **no DB writes** — verified by grep across the whole file.
3. No file in `src/sync/` or `src/scheduler/` imports `FighterRepository`/`EventRepository`.

---

## 7. Remaining Gap vs the v6 5-Phase Plan

| Phase (from v6) | Status now | What remains |
|---|---|---|
| **A. Compile + deps + remove AI** | 🟡 60% | ✅ pipeline.py fixed; ⛔ `SyncCheckpoint.__tablename__` (1 line); ⛔ remove/ignore AI dirs (or keep as dead weight — they're not imported); ⛔ **re-export the zip** (142 corrupt files + missing assets) |
| **B. Make the app boot** | 🔴 20% | ⛔ zip corruption blocks install; ⛔ missing `assets/`; ⛔ fix `fighters/theme/index.ts` (Image import) + `predictions/index.ts` (mangled line); ⛔ delete duplicate shell components; ⛔ set real API base URL |
| **C. Make data flow** | 🔴 5% | ⛔ fix `sync.py` to use real `SyncPlan`/`SyncEngine` API (or delete CLI, wire scheduler jobs to repositories); ⛔ write the persistence step in scheduler jobs; ⛔ wire SyncManager into `main.py` lifespan; ⛔ decide: run scheduler in-process vs standalone `scheduler.py` |
| **D. Close the contract gap** | 🟡 30% | ⛔ 55 phantom mobile routes (decide: add backend routes for the ~15 legit ones — champions, title-defenses, rankings/division, me/stats, events/{id}/fights — and DELETE the ~25 prediction/recommendation paths); ⛔ fix `/v1/favorites` vs `/v1/me/favorites` mismatch; ⛔ implement real favorites/notifications/recommendations or remove them |
| **E. DB integrity** | 🔴 0% | ⛔ **NEW:** add auth migrations (users, sessions, prefs, favorites, watchlist, notifications, devices); ⛔ fix 002 duplicate `synced_at`; ⛔ add `updated_at` to rankings/broadcasts/statistics (+`synced_at` to competitors); ⛔ add `/v1/weight-classes` route; ⛔ fix `/health/ready` DB check |

**Not previously known (added by this audit):** N1 (no auth tables), N2 (migration 002 conflict), N3 (rankings 500), N4 (sync can't persist), N5 (no weight-class route), M5-7 (zip corruption, missing assets), N6-7 (2 real TS errors).

---

## 8. What Actually Works (be fair to the good parts)

- ✅ **ESPN client is genuinely production-grade** — circuit breaker, token bucket rate limiting, retries, pagination; live call returned HTTP 200 against `sports.core.api.espn.com`.
- ✅ **Providers + parsers + DTOs are complete and correct** — 9 ESPN parsers, TSDB client (free key `3`), Octagon client, provider registry, merge engine. The `VERIFICATION_REPORT.md` matches the real ESPN shapes I documented previously.
- ✅ **Repositories have real `ON CONFLICT` upserts** — `fighter.py` (FighterRecord) etc. are proper Postgres upserts.
- ✅ **API surface is broad and well-shaped** — 95 routes registered; events/fighters/promotions/venues/search read paths all return 200 (empty) with correct pagination schemas.
- ✅ **Auth code (JWT + Argon2 + RBAC + rotation) is well-written** — it just has no tables to run against.
- ✅ **Scheduler design is sound** — job registry, cadences, locking, retry, live-mode all thoughtfully specified; it's just not wired or persisting.
- ✅ **Mobile valid code is ~type-clean** — only 28 real TS errors; routes wired; design system is extensive (tokens, components, charts).
- ✅ **Migrations 001 is clean** and creates 15 well-designed tables.

**In one sentence:** every *leaf* component is well-built; the *tree* is not assembled — nothing connects provider → repository → DB → API → app, and the delivery vehicle (zip) is damaged.

---

## 9. Prioritized Action Plan (updated, file-level)

### Step 0 — Get a clean delivery (0.5 day, Zaro AI's job)
Re-export the repo so **zero files** are placeholders and `assets/` is included. Verify: `grep -rl "could not be retrieved" . | wc -l` must be **0**; `ls mobile/assets/` must show icon/splash/adaptive-icon. Nothing else matters until this is true.

### Step 1 — Backend compiles & boots (0.5 day)
- `backend/src/db/models/support.py:76` — add `__tablename__ = "sync_checkpoints"` (1 line; the only import blocker).
- Set `JWT_SECRET` in `.env` (auth refuses the default — by design, good).

### Step 2 — Database integrity (1 day) — NEW
- **Add a new migration `003_auth_tables.py`** creating: `users`, `user_sessions`, `user_preferences`, `favorite_fighters`, `favorite_events`, `watchlist_events`, `notifications`, `devices` (mirror `src/db/models/auth.py` exactly).
- **Patch `002_phase6_support.py`** to skip `rankings`/`statistics` for `synced_at` (they already have it from 001), and add missing `updated_at` to `rankings`, `broadcasts`, `statistics`; add `updated_at`+`synced_at` to `competitors`. (Or, cleaner: squash 001+002+003 into one `001_squashed` and regenerate.)
- Verify: drop DB → `alembic upgrade head` succeeds; `\d rankings` shows `updated_at`; `\dt` shows `users`.

### Step 3 — Make data flow (2–3 days) — the showstopper
- **Fix `sync.py`** (or delete it): either rewrite its calls to the real `SyncPlan`/`SyncEngine` API, or remove the CLI and expose sync only through the scheduler.
- **Write the persistence step in scheduler jobs**: each job must call the matching repository upsert (e.g., `sync_events_upcoming` → `EventRepository.upsert(...)`), commit per batch, record metrics. The `src/sync/upserts/` classes + `src/db/repositories/` already do the write work — **wire them in**.
- **Enable SyncManager**: uncomment `manager = SyncManager(context)` in `main.py` lifespan, with a real context (db engine + session factory + redis if available). Consider a `SYNC_ENABLED` flag defaulting true.
- Verify: `python sync.py --full --provider espn` (after fix) inserts rows; `SELECT count(*) FROM fighters` > 0; `SELECT count(*) FROM events` > 0; `SELECT count(*) FROM rankings` > 0.

### Step 4 — Fix the rankings 500 + weight-classes (0.5 day)
- After Step 2's `updated_at` fix, re-test `/api/v1/rankings*` — should return 200 with categories.
- Add `GET /v1/weight-classes` (query `WeightClass` model — trivial, mirrors venues).

### Step 5 — Mobile: make it boot (1 day)
- With the clean zip: `npm install`, `npx tsc --noEmit` → fix the 28 errors (add `Image` import in `features/fighters/theme/index.ts`; regenerate `features/predictions/index.ts`).
- Delete the duplicate `MaintenanceScreen`/`OfflineBanner` from `components/shell/SplashScreen.tsx`.
- Set real API base URL in `app/networking/NetworkConfig.ts` (via `EXPO_PUBLIC_API_URL`).
- `npx expo start` → app boots to Home.

### Step 6 — Close the contract gap (2–3 days)
- **Backend additions** (legit, data already synced or trivially derivable): `/v1/champions` (from `rankings.is_champion`), `/v1/title-defenses`, `/v1/rankings/{division}` alias for `/division/{d}`, `/v1/fighters/{id}/fights` alias for `/history`, `/v1/fighters/{id}/stats` alias for `/statistics`, `/v1/events/{id}/fights` (from embedded competitions), `/v1/me/stats`, `/v1/fighters/compare` (accept 2 ids), `/v1/fighters/{id}/rankings`.
- **Mobile deletions** (AI — user rejected): all `predictions/` feature code, `/v1/predictions/*` endpoints, prediction UI cards; `recommendations` → keep only if you want the trending feed, else remove.
- **Mobile realignment**: `favorites` → `/v1/me/favorites/fighters/{id}`; `watchlist` → `/v1/watchlist/events|fighters`; `home` → compose from `/events/live`, `/events/upcoming`, `/rankings` (drop `/v1/home`).
- Verify: re-run the contract diff script — 0 missing paths.

### Step 7 — Real user features (2–3 days)
- Implement `/v1/me/favorites/*` for real (they're the last stubs), or decide favorites live on-device (PRD option) and remove the endpoints.
- Implement notifications read/unread against the real table (or defer — requires push infra).
- Decide AI modules fate: **delete `prediction/`, `recommendation/`, `platform/`** from the repo (they're 100% corrupt shells anyway + user rejected AI) and strip `intelligence/` or keep as a separate sandbox.

### Step 8 — Tests green (1 day)
- Add auth-table fixtures (or run e2e against Postgres via a test DB URL).
- Fix DTO drift: add `is_active` to `FighterDTO`, `last_sync_at` to `SyncState`, pydantic `from_attributes` config.
- Target: 250+ pass, 0 fail, 0 error.

**Total: ~5–8 focused days** to a genuinely working build. Not weeks — but only because the fixes are mechanical. The architecture is good; the assembly is incomplete.

---

## 10. Corrective Prompt to Send Zaro AI

> Your second delivery (`from-github (2).zip`) is **not buildable**. Verified against a live Postgres 15 + uvicorn + tsc:
>
> 1. **The zip itself is corrupted**: 142 of 957 files are the placeholder string "This file could not be retrieved" — including `mobile/package.json` and `mobile/tsconfig.json` — and `mobile/assets/` (icon.png, splash.png, adaptive-icon.png) is missing. `npm install` and `expo start` are impossible. **Re-export the repo with every file present and the assets directory included.** Verify: `grep -rl "could not be retrieved" . | wc -l` == 0.
> 2. **Auth has no tables**: `src/db/models/auth.py` defines users/sessions/favorites/watchlist/notifications/devices, but no migration creates them. `POST /v1/auth/register` → 500 (`relation "users" does not exist`). Add migration 003.
> 3. **Migrations don't run on a fresh DB**: 002 re-adds `synced_at` to `rankings`/`statistics` which 001 already created → `DuplicateColumnError`. Fix 002 and add missing `updated_at` to rankings/broadcasts/statistics, `synced_at`/`updated_at` to competitors.
> 4. **Sync cannot persist data**: (a) `sync.py --full` crashes — `SyncPlan(entity_types=...)` doesn't match the real no-arg dataclass; (b) `src/scheduler/jobs.py` job functions fetch from ESPN but **never write to the database** (no session/upsert anywhere); (c) nothing imports the repositories from the sync/scheduler layers. Wire provider → repository → DB, and enable SyncManager in `main.py` lifespan.
> 5. **Rankings endpoints 500** until (3) is fixed — `rankings.updated_at` missing.
> 6. **Mobile**: fix the 2 files with real TS errors (`features/fighters/theme/index.ts` missing `Image` import; `features/predictions/index.ts` mangled), delete duplicate shell components in `SplashScreen.tsx`, and stop calling 55 non-existent API paths (list attached) — either add the ~15 legitimate backend routes or remove the mobile calls.
> 7. **Remove the AI modules** (`prediction/`, `recommendation/`, `platform/`, and mobile `predictions/` + `recommendations/`) — the client explicitly does not want AI predictions, AI chat, or AI recommendations. Keep only non-AI features.
> 8. Your `PROJECT_STATUS.md` claims (Phase 9 Auth Complete, Phase 11 "48 tests, 91% coverage") are false: 259 tests exist, 30 fail + 17 error, and auth 500s. Update the docs to reality.
>
> Deliver: (a) a clean zip with zero placeholder files, (b) working migrations (drop → `alembic upgrade head`), (c) a sync path that actually inserts rows (show `SELECT count(*)` before/after), (d) `tsc --noEmit` == 0 errors, (e) test suite 0 fail/0 error.

---

## 11. Evidence Trail (commands run)

```
unzip -v zaro_v2.zip → package.json & tsconfig.json: 82 bytes, CRC 84df53dd (placeholder)
unzip -p zaro_v2.zip "*mobile/package.json" → "This file could not be retrieved..."
python3 -m compileall -q backend/src/ → exit 0 (pipeline.py fixed)
JWT_SECRET=x python3 -c "from src.api.main import app" → InvalidRequestError: SyncCheckpoint no __tablename__
[+1-line patch] → app imports, 95 routes
python3 -m pytest tests/ (patched) → 30 failed, 212 passed, 17 errors
alembic upgrade 001 → 15 tables OK
alembic upgrade 002 → ProgrammingError: column "rankings"."synced_at" already exists
[+002 patch] → upgrade head OK (19 tables)
uvicorn src.api.main:app → boots
curl /health/live → 200; /health/ready → database FAILED
curl /api/v1/rankings → 500 (rankings.updated_at does not exist — Postgres log)
curl /api/v1/auth/register → 500 (relation "users" does not exist — Postgres log)
curl /api/v1/events, /fighters, /promotions, /venues, /search → 200 empty pagination
curl /api/v1/weight-classes → 404
python3 sync.py --full --provider espn --entity promotion → TypeError: SyncPlan() unexpected keyword 'entity_types'
grep session.add|upsert src/scheduler/jobs.py → none
grep FighterRepository src/sync/ src/scheduler/ → none
npx tsc --noEmit (rebuilt harness) → 718 errors: 690 corrupt-placeholder, 28 valid-code
Contract diff (90 mobile paths vs 73 backend v1 routes) → 35 matched, 55 missing
grep -rl "could not be retrieved" → 142 files (backend 0, mobile 75, prediction 20, recommendation 28, platform 19)
```

---

## 12. Final Verdict

**Is this now good enough to build on?** — **No, not as delivered.** Three things block a working app today, in order of severity:

1. **The zip is damaged** (142 placeholder files, missing assets) → the mobile app cannot be installed or run. This is Zaro AI's export failure and must be fixed by them (re-export), or by reconstructing ~142 files from the previous zip where they overlap.
2. **No data can reach the database** (sync CLI crashes, scheduler jobs never persist, SyncManager disabled) → every screen is empty even after everything else is fixed.
3. **Auth/user layer has no tables** (register/login 500, all user endpoints dead) → no accounts, no favorites, no notifications.

**The good news:** none of this is architectural. Every subsystem is well-designed in isolation; the assembly and delivery are broken. With a clean re-export + the 8 steps in §9, this becomes a real, buildable product in **5–8 focused days**. The alternative — revert to the v1 zip (which at least had a valid package.json) and apply the same fixes — is also viable.

**Recommendation:** send the §10 corrective prompt, demand the clean export + working migrations + a sync path that demonstrably inserts rows, and in parallel apply Steps 1–4 yourself (0.5 + 1 + 2–3 + 0.5 days) since they're mechanical and you have the source in the zip.
