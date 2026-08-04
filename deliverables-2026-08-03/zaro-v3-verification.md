# Zaro AI Monorepo — Third Iteration Verification Report (v3 of the zip)

**Date:** 2026-08-03
**Zip analyzed:** `1785754168717000000377_from-github (3).zip` (980 KB, extracted: `mma-app-zaro-ai-repo`, 793 files)
**Prior audits:** `zaro-ai-audit-analysis.md` (v6 — zip 1), `zaro-v2-verification.md` (v7 — zip 2)
**Method:** Live verification, nothing taken on faith — zip integrity scan, `compileall`, app import, real **Postgres 15** setup, Alembic migrations from scratch, uvicorn boot, live HTTP endpoint tests (auth, rankings, events, favorites), sync engine run with **DB row counts before/after**, full pytest suite, `npm install` + `tsc --noEmit`, expo export attempt, mobile↔backend API-contract diff against the **live OpenAPI spec**, and cross-checks of every doc claim.

> **TL;DR — the delivery is finally clean, the backend finally boots, auth finally works end-to-end, and the mobile app is finally structurally sound — but the sync engine still cannot write a single row to the database, the rankings feature still 500s on a schema-drift bug that survived three iterations, the mobile app cannot be bundled (`expo-asset` missing), the test suite is exactly as red as v2 (212/30/17), and the AI modules you explicitly rejected are still in the repo AND still wired into the mobile UI as tabs.**
>
> **Verdict: FIXED ≈ 65% of the v7 blockers; the remaining 35% are precisely the ones that block "data on screen." This is the closest iteration yet — but it is still NOT buildable end-to-end as delivered. Roughly 4–6 focused days remain (down from 5–8).**

---

## 0. Executive Summary — v2 → v3 Scorecard

| # | Dimension | v2 (zip 2) | v3 (zip 3) | Trend |
|---|---|---|---|---|
| 1 | Zip integrity (placeholders) | 🔴 142/957 corrupt | ✅ **0/793 corrupt** | 🟢 |
| 2 | `package.json` / `tsconfig.json` | 🔴 82-byte placeholders | ✅ **Real, valid** | 🟢 |
| 3 | `assets/` directory | 🔴 missing | 🔴 **STILL missing** (app.json references it) | 🔴 |
| 4 | Backend `compileall` | ✅ pass | ✅ **pass** | 🟢 |
| 5 | Backend app import | 🔴 fails (`SyncCheckpoint.__tablename__`) | ✅ **Imports, 119 routes** | 🟢 |
| 6 | Scheduler wired into app | 🔴 commented out | ✅ **Wired in lifespan** (SyncManager.start) | 🟢 |
| 7 | Alembic migrations fresh DB | 🔴 DuplicateColumnError | ✅ **001→002→003 apply cleanly** | 🟢 |
| 8 | Auth tables exist | 🔴 none | ✅ **All 7 created** (users, sessions, favorites×2, watchlist, notifications, devices) | 🟢 |
| 9 | Register / Login live | 🔴 500 | ✅ **201 / 200 with JWT** | 🟢 |
| 10 | Favorites endpoint | 🔴 stubs | ✅ **Real** (`/v1/me/favorites` returns real shape) | 🟢 |
| 11 | Rankings / Champions endpoints | 🔴 500 (drift) | 🔴 **STILL 500** — `rankings.source_provider` missing | 🔴 |
| 12 | `sync.py --full` entrypoint | 🔴 crashes (`SyncPlan()` arg mismatch) | 🔴 **STILL crashes** — `SyncPlan` never imported; then `src.domain` missing | 🔴 |
| 13 | Scheduler jobs write to DB | 🔴 fetch→count→return only | 🟡 **Structurally fixed** (`_persist` → `UpsertEngine`) but **blocked by `src.domain` imports** | 🟡 |
| 14 | **Rows actually written by sync** | 🔴 0 | 🔴 **0 (proven)** | 🔴 |
| 15 | Mobile route files | ✅ 8 wired | ✅ **8 wired + default exports** (`index.tsx → HomeScreen`) | 🟢 |
| 16 | `_layout.tsx` boot path | ✅ exists | ✅ **Full provider tree + splash/maintenance/offline** | 🟢 |
| 17 | Shell components (Maintenance/Offline) | ✅ exist | ✅ **exist, imported in `_layout`** | 🟢 |
| 18 | JSX-in-`.ts` files | ✅ fixed (renamed) | 🟡 **1 file regressed** (`features/rankings/theme/index.ts`) | 🟡 |
| 19 | `tsc --noEmit` errors | 718 (690 corrupt + 28 real) | **40, all in ONE file** | 🟢 |
| 20 | `npm install` | 🔴 impossible | ✅ **Works (1283 packages)** | 🟢 |
| 21 | App bundle (expo export) | 🔴 impossible | 🔴 **Fails: `expo-asset` missing from deps** (NEW issue) | 🔴 |
| 22 | Default API base URL | 🔴 `api.mma-app.com` placeholder | 🟡 **`api.mma-platform.com`** (prod) / `localhost:8000` (dev) — still a placeholder host | 🟡 |
| 23 | Phantom API calls (mobile→backend) | 🔴 55/90 | 🟡 **40/136 phantom** (96 matched, 70%) — mostly AI + prefix bugs | 🟡 |
| 24 | AI modules (prediction/recommendation/intelligence) | 🔴 present (corrupted shells) | 🔴 **STILL PRESENT — 106 real files, and wired into mobile tabs** | 🔴 |
| 25 | Test suite | 212 pass / 30 fail / 17 err | **212 pass / 30 fail / 17 err** (259 collected vs 243) | 🔴 same |
| 26 | "48 tests, 91% coverage" claim | 🔴 false | 🔴 **still false** | 🔴 |

**Fair read:** This iteration fixed everything that was *broken about the delivery* (corruption, missing manifests, unimportable backend, dead scheduler, no auth tables, broken migrations, unroutable app) — a genuinely large, verifiable improvement. What remains broken is *exactly the part that puts data on a screen*: the sync write path, the rankings schema, and the app bundle. Plus scope violations (AI) and test debt that have now survived all three iterations.

---

## 1. Zip Integrity Report — CLEAN (finally)

| Check | Result | Evidence |
|---|---|---|
| Files in zip | 793 | `find extracted -type f \| wc -l` |
| Placeholder text ("This file could not be retrieved") | **0** | `grep -rl` across extracted tree → 0 hits (v2: 142) |
| `mobile/package.json` | ✅ Real JSON, 32 deps + 7 devDeps | `head -30` shows valid manifest, `npm install` works |
| `mobile/tsconfig.json` | ✅ Real (765 B) | `ls -la` |
| `mobile/app.json` | ✅ Real — but references `./assets/icon.png`, `./assets/splash.png`, `./assets/adaptive-icon.png` | `cat app.json` |
| `mobile/assets/` | 🔴 **STILL MISSING** | `ls mobile/assets/` → no such directory |
| Backend `pyproject.toml` | ✅ Real | `pip install -e .` works |

**Verdict:** The corruption problem is **solved**. The `assets/` omission is a real but trivial defect (Expo falls back to defaults with warnings; `expo export` may still proceed for native) — worth one-line mention to Zaro, not a blocker on its own.

---

## 2. Verdict per Previously-Reported Issue (v7 list, item by item)

### 2.1 Backend

**✔️ FIXED — `pipeline.py` syntax error (v1/v2-era).**
`src/sync/pipeline.py` now has a valid f-string:
```python
f"{job.entity_type.value}: mode={decision.mode.value} "
f"reason={decision.reason} "
f"page={decision.start_page} offset={decision.start_offset}"
```
`python -m compileall src/` → exit 0, zero errors.

**✔️ FIXED — `SyncCheckpoint.__tablename__` missing.**
`src/db/models/support.py:78` now declares `__tablename__ = "sync_checkpoints"`. The app imports cleanly: `from src.api.main import app` → **IMPORT_OK, 119 routes** (requires `JWT_SECRET` env now — a security guard that refuses the default secret, which is *good*).

**✔️ FIXED — Scheduler wired into startup.**
`src/api/main.py` lifespan now constructs `ESPNProvider`, `SyncContext`, `SyncManager(context)`, and calls `await manager.start()` with `set_sync_manager(manager)`. TSDB/Octagon are optional non-blocking. Startup log: `Application startup complete` + `SyncManager started — scheduled jobs active`.

**✔️ FIXED — Migrations apply on a fresh database.**
On a brand-new Postgres 15 DB: `alembic upgrade head` runs all three revisions cleanly:
```
Running upgrade  -> 001, Initial schema
Running upgrade 001 -> 002, Phase 6 support tables + syncable columns
Running upgrade 002 -> 003, Phase 6 — Auth tables
```
The v2 `DuplicateColumnError` is gone (migration 002 now uses `_make_syncable_columns()` with fresh column objects and drops the duplicate `synced_at` addition).

**✔️ FIXED — Auth tables exist and auth works end-to-end.**
Migration `003_auth_tables.py` creates: `users`, `user_sessions`, `favorite_fighters`, `favorite_events`, `watchlist_events`, `notifications`, `devices`, `user_preferences`. Verified live:
- `POST /api/v1/auth/register` `{email, password, username}` → **200/201 with `access_token` + `refresh_token`** (real JWT, verified payload: `sub`, `role: user`, `permissions`, `exp`)
- `POST /api/v1/auth/login` → **200 with tokens** (previously 500)
- `GET /api/v1/me/favorites` with Bearer token → **200 `{"fighters":[],"events":[],"promotions":[],"weight_classes":[]}`** — real DB-backed response, no stubs
- `GET /api/v1/notifications/unread-count` → **200 `{"count":0}`**

**🔴 STILL BROKEN — Rankings & Champions 500 (schema drift, third iteration in a row).**
```
GET /api/v1/rankings  → 500  ProgrammingError: column rankings.source_provider does not exist
GET /api/v1/champions → 500  same
```
Root cause, proven from source:
- `src/db/models/core.py:88` — `class Ranking(Base, SyncableMixin)` → the model **requires** `synced_at`, `source_provider`, `version` columns.
- `alembic/versions/002_phase6_support.py:147` — the syncable-columns loop covers only `["fighters","events","competitions","promotions","venues","broadcasts","weight_classes","competitors"]`. **`rankings` is absent.**
- Line 153 adds only `updated_at` to rankings — not the SyncableMixin trio.

This is the *same class* of bug I flagged in v7 ("model expects updated_at, migration doesn't create it" — that part got fixed, but the deeper `SyncableMixin` drift on rankings was not). **Fix is one line in migration 002 (add `"rankings"` to the loop) + a new migration 004 for existing DBs.**

**🔴 STILL BROKEN — Sync engine writes zero rows (the showstopper).**

Chain of evidence, run live:

1. `python sync.py --full --provider espn --entity fighter --dry-run` → parses, banner, "DRY RUN" — no crash at CLI parse level. ✅ (v2 crashed at arg parsing)
2. `python sync.py --full --provider espn --entity event` (no dry-run) → **crashes**:
   ```
   [ERROR] sync: Sync failed: name 'SyncPlan' is not defined
   File "sync.py", line 158, in run_full_sync
       plan = SyncPlan(name=f"single_{entity_filter}", ...
   ```
   `run_full_sync` imports `FullSyncPlan, RankingsPlan, EventsPlan, FighterPlan, FoundationPlan` but **not `SyncPlan`** — one missing name in the import list.
3. I applied that 1-line import fix in a throwaway copy → the run progressed: live ESPN calls succeeded (`GET /leagues/ufc/events?limit=25&offset=0 → 200`, `GET /events/600060621 → 200`, "Fetched 1 events from ESPN (ufc)"), then died:
   ```
   [ERROR] Sync job event: No module named 'src.domain'
   [ERROR] Critical job failed: event. Aborting plan 'single_event'.
   ```
4. **Root cause:** **18 files** under `src/sync/upserts/` (fighter, event, competition, promotion, ranking, statistics, broadcast, venue, weight_class) import `from src.domain.models.X import X` — but **`src/domain/` does not exist anywhere in the repo**. The models actually live at `src/db/models/{fighter,event,core,support}.py`. (`find . -type d -name domain` → nothing.)
5. **Row counts after every attempt: all zero.**
   ```
   fighters | 0   events | 0   rankings | 0   sync_runs | 0
   ```
   `sync_runs` being empty is itself damning — the engine never even records a run.

**What got structurally better (credit where due):** the v7 finding "scheduler jobs fetch from ESPN and never write to DB" is **fixed at the jobs layer**. `src/scheduler/jobs.py` now has a real `_persist()` helper that calls `UpsertEngine.upsert_entity()` (ON CONFLICT upserts), and `sync_events_upcoming` / `sync_rankings` / `sync_results` all use it with `ctx.db_session_factory()`. The ESPN job classes (`ESPN_FighterSyncJob._upsert` etc.) call `FighterUpsert(resolver).upsert_batch(dtos)` + `ctx.db.flush()`. **The write machinery exists — it is just unreachable because every upsert module fails to import.**

So the data-flow verdict is: **ESPN → fetch ✅ → parse ✅ → upsert-module import 🔴 → DB (0 rows).**

### 2.2 Mobile

**✔️ FIXED — Route files wired, app boot path exists.**
```
app/index.tsx          → export { HomeScreen as default }
app/events.tsx, fighters.tsx, rankings.tsx, search.tsx, profile.tsx,
app/notifications.tsx, watchlist.tsx, +not-found.tsx
```
`app/_layout.tsx` has the complete boot tree: `GestureHandlerRootView → SafeAreaProvider → QueryProvider → AuthProvider → NotificationProvider → AppContent (Splash → Maintenance → OfflineBanner → Slot)`. `HomeScreen.tsx` exists; `hooks/useTheme.ts`, `hooks/useNetwork.ts`, `stores/ui.ts`, all providers exist. The v7 "unroutable, boot to blank" problem is **solved**.

**✔️ FIXED — Shell components exist and are used.**
`components/shell/` contains `ErrorBoundary.tsx`, `MaintenanceScreen.tsx`, `OfflineBanner.tsx`, `SplashScreen.tsx` — all imported by `_layout.tsx`.

**✔️ FIXED — `npm install` works.**
`added 1283 packages in 43s`. package.json is valid.

**🟢 MAJOR IMPROVEMENT — TypeScript is nearly clean.**
`npx tsc --noEmit` → **40 errors, all in one file**: `features/rankings/theme/index.ts` (contains JSX in a `.ts` file — needs `.tsx` rename). Compare: v2 = 718 errors (690 from corrupt placeholders + 28 real). The 690 corrupt-file errors are gone because the zip is clean. **40 → rename one file to `.tsx` and it's likely 0.**

**🔴 NEW ISSUE — App cannot bundle: `expo-asset` missing.**
```
npx expo export --platform ios →
Error: The required package `expo-asset` cannot be found
```
`package.json` lists 15 expo packages but **not `expo-asset`**, which `expo` ~52 requires. `npx expo install expo-asset` fixed it (added plugin), but as *delivered* the app will not start. (After installing, the export then died with `Killed` exit 137 — the sandbox cgroup memory cap is 2 GB (`/sys/fs/cgroup/memory.max` = 2147483648) and Metro needs more; that part is a **sandbox limitation, not a code defect**, and I could not complete a full bundle here. The `tsc` result above is the reliable signal.)

**🟡 PARTIALLY FIXED — API base URL.**
`mobile/services/api.ts`: `__DEV__ ? 'http://localhost:8000/api' : 'https://api.mma-platform.com/api'`. The old placeholder host `api.mma-app.com` is gone, but `api.mma-platform.com` is still a made-up production host — must be replaced with the real deployed backend URL. (There are **two** API configs: `services/api.ts` and `app/networking/NetworkConfig.ts` — the latter still defaults to `https://api.mma-app.com`. Duplication to resolve.)

**🟡 MINOR REGRESSION — one JSX-in-`.ts` file.**
`features/rankings/theme/index.ts` contains `RankProgressionChart` / `MovementTimelineChart` with JSX. Rename to `.tsx` (or delete — they're chart placeholders anyway).

### 2.3 AI Modules — 🔴 STILL PRESENT (scope violation, third iteration)

- `prediction/` + `recommendation/` + `intelligence/` = **106 files** (96 Python + configs), now **real, complete code** (v2's were corrupted shells — so this is *worse* in the sense that they're now fully usable AI code the user never asked for).
- `mobile/features/predictions/` and `mobile/features/recommendations/` are **wired into the tab bar** (`MainNavigator.tsx`: `<Tab.Screen name="predictions" component={PredictionsStack} options={{ tabBarLabel: 'Predict' }} />`) — the user would see an "AI Predict" tab.
- Backend `src/` has **zero references** to `prediction/recommendation/intelligence` — they are dead weight (no backend routes for `/v1/predictions/*` — confirmed phantom).
- `mobile/PRODUCTION_AUDIT.md` still lists Predictions and Recommendations as "**Production**" features with "10 endpoints" each — none of those endpoints exist.

### 2.4 Docs Claims vs Reality

| Claim (docs) | Reality |
|---|---|
| `PRODUCTION_AUDIT.md`: **"OVERALL 9.3/10, Production-ready"** | False — app cannot bundle (`expo-asset`), backend sync writes 0 rows, rankings 500 |
| `PROJECT_STATUS.md`: **"48 tests, 91% coverage, Phase 11 Complete"** | False — 259 tests collected; **212 pass / 30 fail / 17 errors** (identical to v2) |
| `verify_espn.py`: **"100%" field coverage tables** | A static printed table — not a live verification; the docstring fantasy persists |

---

## 3. Live Endpoint Test Results (Postgres 15 + uvicorn on :8090)

| Endpoint | Method | Status | Body / Note |
|---|---|---|---|
| `/health` | GET | **200** | `{"status":"ok","app":"MMA Backend API","version":"1.0.0"}` |
| `/api/v1/auth/register` (no username) | POST | 422 | correct validation error (schema requires `username`) |
| `/api/v1/auth/register` (full) | POST | **200/201** | JWT access + refresh tokens (verified payload) |
| `/api/v1/auth/login` | POST | **200** | JWT tokens (was 500 in v2) |
| `/api/v1/me/favorites` (Bearer) | GET | **200** | `{"fighters":[],"events":[],"promotions":[],"weight_classes":[]}` — real |
| `/api/v1/rankings?division=heavyweight` | GET | **500** | `column rankings.source_provider does not exist` |
| `/api/v1/champions` | GET | **500** | same column error |
| `/api/v1/events?limit=2` | GET | **200** | `{"items":[],"total":0,...}` (empty — no sync) |
| `/api/v1/events/upcoming` | GET | **200** | `[]` (empty — no sync) |
| `/api/v1/fighters?limit=2` | GET | **200** | empty page |
| `/api/v1/search?q=jon` | GET | **200** | `{"query":"jon","total":0,"results":[]}` |
| `/api/v1/venues` | GET | **200** | empty page |
| `/api/v1/notifications/unread-count` | GET | **200** | `{"count":0}` |
| `/api/v1/me/stats` | GET | **404** | mobile calls it; route doesn't exist |
| `/api/v1/me/export` | GET | **404** | mobile calls it; route doesn't exist |
| `/api/v1/fighters/nonexistent/statistics` | GET | 500 | invalid-UUID → 500 instead of 400 (minor robustness gap) |
| `/openapi.json` | GET | **200** | 101 paths served |

**OpenAPI live route count:** 101 paths (119 app.routes incl. middleware/static).

---

## 4. Sync Engine Data-Flow Proof (row counts before/after)

```
PRE-SYNC:   fighters=0  events=0  competitions=0  rankings=0  promotions=0  sync_runs=0
ATTEMPT 1:  python sync.py --full --provider espn --entity event
            → NameError: name 'SyncPlan' is not defined   (sync.py:158)
ATTEMPT 2:  (patched import in throwaway copy)
            → live ESPN 200s, "Fetched 1 events", then
              [ERROR] Sync job event: No module named 'src.domain'
POST-SYNC:  fighters=0  events=0  rankings=0  sync_runs=0   ← ZERO ROWS WRITTEN
```

**Blocking chain (both must be fixed):**
1. `sync.py:131` imports plans but omits `SyncPlan` (1-line fix).
2. `src/sync/upserts/*.py` (18 files) import `src.domain.models.*` — nonexistent package; models live in `src/db/models/`. Fix: either create `src/domain/models/__init__.py` re-export shim, or rewrite the 18 imports to `src.db.models.*`. A 1-file shim is the cheapest and safest.

**Positive finding:** the scheduler's `_persist()` → `UpsertEngine.upsert_entity()` pipeline and the ESPN job `_upsert()` → `FighterUpsert.upsert_batch()` plumbing are real and correctly structured. Once the imports resolve, the write path should work — that's why this is "close."

---

## 5. Test Suite Results (v7 → v8 comparison)

| Metric | v7 (zip 2) | v8 (zip 3) |
|---|---|---|
| Tests collected | 243 | **259** |
| Passed | 212 | **212** |
| Failed | 30 | **30** |
| Errors | 17 | **17** |
| Unit tests (`tests/unit`) | — | 20 passed (clean) |
| Root cause of failures | structural: tests reference removed fields (`SyncState.last_sync_at`), JSONB-in-SQLite, sync FakeRedis | **identical structural issues** — e.g. `AttributeError: 'SyncState' object has no attribute 'last_sync_at'` |

The suite is exactly as red as v2. The tests were written against an *older* internal API (`SyncState.last_sync_at`, `SyncPlan(entity_types=...)`) that the current code no longer has — the sync refactor and the tests drifted apart and nobody reconciled them. 30+17=47 failing/erroring tests is a lot of signal that **nobody has run this suite since the refactor**.

---

## 6. Mobile ↔ Backend API Contract (136 calls vs 101 live routes)

Method: extracted every `/v1/...` string from mobile `.ts/.tsx`, normalized path params, matched against the **live OpenAPI** of the running backend.

**Result: 96 matched (70%) / 40 phantom.**

### The 40 phantom calls, grouped:

| Group | Calls | Status |
|---|---|---|
| **AI predictions** (16) | `/v1/predictions/*` (fight, event, fighter, matchup, saved, history, dashboard, accuracy, highlights, odds, monte-carlo, factors, share) | 🔴 No backend routes — user rejected AI; **mobile UI (Predict tab) is dead weight** |
| **Generic watchlist** (7) | `/v1/watchlist/${type}`, `/${type}/${id}`, `/${type}/${id}/status`, `/${type}/bulk`, `/v1/watchlist/collections`, `/v1/watchlist/reminders*` | 🟡 Backend has concrete `/v1/watchlist/events/*` + `/v1/watchlist/fighters/*` + `/v1/me/watchlist/*` — mobile uses a **different generic design**; needs unification |
| **Favorites prefix mismatch** (4) | `/v1/favorites/fighters`, `/${id}`, `/${id}/status` | 🟡 Backend = `/v1/me/favorites/fighters/{fighter_id}` — **mobile prefix wrong** (missing `/me`) |
| **Stub-adjacent / missing** (5) | `/v1/me/stats`, `/v1/me/export`, `/v1/reminders`, `/v1/reminders/${id}`, `/v1/follows/fighters/${id}` | 🟡 No routes; features are modeled but not built |
| **Wrong base for infra** (4) | `/v1/health`, `/v1/metrics`, `/v1/home`, `/v1/remote-config` | 🟡 Backend has `/health`, `/api/metrics`, no `/home`, no `/remote-config` |
| **Computed/analytic** (3) | `/v1/composite`, `/v1/elo`, `/v1/search/voice` | 🟡 No routes (composite/elo were never implemented; voice search is fantasy) |
| **Ranking sub-features** (1 real gap) | `/v1/rankings/division/${d}`, `/v1/rankings/history/${id}`, `/v1/rankings/movement`, `/v1/rankings/prospects`, `/v1/rankings/changes`, `/v1/rankings/p4p` — wait, `/p4p` EXISTS | Backend has `/rankings`, `/rankings/{division}`, `/rankings/mens`, `/rankings/womens`, `/rankings/p4p`, `/rankings/goat`, `/rankings/streaks`. Phantom: `division/{d}` (should be `/{d}`), `history/{id}`, `movement`, `prospects`, `changes` |

**Notable:** every AI/recommendation call the mobile makes is phantom **except** `/v1/recommendations/*` which DOES exist in the backend (`/recommendations`, `/discover`, `/feedback`, `/dismiss/{rec_id}`, `/because/follow`, `/because/watched`, `/profile`, `/events`, `/fighters`) — so the backend has a recommendations API even though the user rejected AI features. **Decision needed: delete or keep.** My recommendation: delete — it violates the no-AI constraint.

---

## 7. What Actually Works Now (be fair — the good parts)

- ✅ **Zip delivery integrity** — finally clean, installable.
- ✅ **Backend compiles, imports, boots** with 119 routes and 101 OpenAPI paths; lifespan starts the scheduler.
- ✅ **Migrations** apply from scratch on real Postgres 15 (001→002→003).
- ✅ **Auth is fully functional live**: register (JWT), login (JWT), me/favorites, notifications/unread-count — no 500s, no stubs.
- ✅ **All 27 tables** created including auth tables.
- ✅ **Scheduler architecture is real**: SyncManager in lifespan, jobs registry, distributed locks, retries, metrics, `_persist`→UpsertEngine write path, live-mode detection.
- ✅ **ESPN client works live** (leagues/events/athletes 200s), parsing works ("Fetched 1 events").
- ✅ **Mobile boot path wired**: routes, providers, shell components, home screen.
- ✅ **`npm install` works; `tsc` is 40 errors in one file** (rename → likely clean).
- ✅ **60% of mobile API calls match live backend routes** (96/136).

---

## 8. Remaining Gap Analysis vs the v6/v7 Remediation Plan

| Plan item (from v6 §7 / v7 §9) | Status in v8 |
|---|---|
| Step 0: Demand clean re-export (no placeholders, assets included) | 🟡 **Half** — placeholders gone; **assets/ still missing** |
| Step 1: Backend boot (compile, import, JWT guard) | ✅ **Done** |
| Step 2: Migrations + auth tables | ✅ **Done** (001–003 clean) |
| Step 3: Fix rankings schema drift | 🔴 **Not done** (`source_provider` on rankings) |
| Step 4: Sync engine write path | 🔴 **Not done** (`SyncPlan` import + `src.domain` (18 files)) |
| Step 5: Mobile boot (deps, bundle) | 🟡 **Half** — routes/deps fine; **`expo-asset` missing → cannot bundle** |
| Step 6: Contract gap (55 phantom) | 🟡 **Reduced to 40** — AI(16) should be deleted not fixed; favorites prefix + watchlist generic need unification |
| Step 7: Tests green | 🔴 **Unchanged** (212/30/17) |
| Step 8: Remove AI modules + docs | 🔴 **Not done** — 106 files, mobile tabs wired |

---

## 9. NEW Issues Introduced by This Iteration

1. **`expo-asset` missing from `package.json`** (v2's corruption masked this) — app cannot bundle as delivered. 🔴
2. **`features/rankings/theme/index.ts` — JSX in `.ts`** — 40 tsc errors in one file (v2 had renamed these; this file is new/regressed). 🟡
3. **Two API config files disagree** — `services/api.ts` uses `api.mma-platform.com`, `app/networking/NetworkConfig.ts` still defaults to `api.mma-app.com`. 🟡
4. **Duplicate OpenAPI operation ID** — `mark_all_read` defined twice in `notifications.py` (harmless warning, sloppy). 🟡
5. **Invalid UUID → 500** instead of 422/404 on `fighters/{id}/statistics` — should be a FastAPI UUID type or friendly 400. 🟡
6. **`sync_runs` never populated** even on failed runs — metrics/observability gap; a run record should be written even on failure. 🟡

---

## 10. Updated Prioritized Action Plan (file-level, 4–6 focused days)

### Phase A — Unblock the sync write path (Day 1, ~4h) 🔴
1. `backend/sync.py:131` — add `SyncPlan` to the `from src.sync.plan import ...` line. (1 line)
2. **Create shim** `backend/src/domain/__init__.py` + `backend/src/domain/models/__init__.py` that re-exports from `src.db.models.*`:
   ```python
   # src/domain/models/__init__.py
   from src.db.models.fighter import Fighter, FighterRecord
   from src.db.models.event import Event, Competition, Competitor
   from src.db.models.core import Promotion, Venue, WeightClass, Ranking, Statistic, Broadcast
   # plus module files fighter.py, event.py, core.py equivalents if imports are `from src.domain.models.fighter import Fighter`
   ```
   (11 distinct `from src.domain.models.X import Y` patterns — match each with a shim file, or rewrite the 18 imports. Shim = 30 min, no risk.)
3. Re-run `python sync.py --full --provider espn --entity event` → expect rows > 0 in `events`. Then run full sync. **Acceptance: `SELECT count(*) FROM events` > 0 and `sync_runs` has a row.**

### Phase B — Fix rankings schema drift (Day 1, ~1h) 🔴
4. `alembic/versions/002_phase6_support.py:147` — add `"rankings"` to the syncable-columns loop.
5. Author migration `004_rankings_syncable_columns.py`: `ALTER TABLE rankings ADD COLUMN synced_at ..., source_provider ... DEFAULT 'espn', version ... DEFAULT 1`.
6. Apply on fresh DB + existing DB. **Acceptance: `GET /api/v1/rankings` → 200, `GET /api/v1/champions` → 200.**

### Phase C — Make the mobile app bundle (Day 2, ~4h) 🟡
7. `mobile/package.json` — add `expo-asset` (matching expo ~52): `npx expo install expo-asset`.
8. Rename `features/rankings/theme/index.ts` → `.tsx` (40 errors → 0). If the charts are placeholders ("Chart (Victory/Reanimated)"), consider deleting the file + its imports instead.
9. Unify API config: single source (e.g. `app/networking/NetworkConfig.ts`), delete the duplicated `services/api.ts` BASE_URL, set real prod URL via `EXPO_PUBLIC_API_URL`.
10. Add `mobile/assets/` (icon.png, splash.png, adaptive-icon.png) — or strip references from `app.json`.
11. **Acceptance: `npx tsc --noEmit` → 0 errors; `npx expo export --platform ios` completes** (may need to run where cgroup memory allows; locally on your machine this is fine).

### Phase D — Contract cleanup (Day 2–3, ~8h) 🟡
12. Mobile favorites: `/v1/favorites/fighters/*` → `/v1/me/favorites/fighters/*` (backend is correct). Fix `features/fighters/api/endpoints.ts`, `hooks/index.ts`, `mutations/index.ts`.
13. Watchlist: pick the backend's concrete design (`/v1/watchlist/events/{id}`, `/v1/watchlist/fighters/{id}`, `/v1/me/watchlist`) and rewrite the generic `/v1/watchlist/${type}/*` calls (7 places).
14. Rankings: `/v1/rankings/division/${d}` → `/v1/rankings/${d}`; delete calls to `/rankings/history`, `/movement`, `/prospects`, `/changes` unless you build them (data for history IS in the DB via ranking rows with timestamps — nice-to-have).
15. Delete or stub-remove: `/v1/me/stats`, `/v1/me/export`, `/v1/reminders/*`, `/v1/follows/*` from the mobile UI until backend routes exist (or build them — reminders are P2).
16. **Acceptance: every mobile API call resolves to a live route (re-run the contract script → 0 phantom, excluding intentionally-removed AI).**

### Phase E — Delete the AI scope violation (Day 3, ~2h) 🔴 (policy)
17. Delete `prediction/`, `recommendation/`, `intelligence/` from the monorepo.
18. Mobile: remove `features/predictions/`, `features/recommendations/` + the two `<Tab.Screen>` entries in `MainNavigator.tsx` (keep the tab bar clean: Home, Events, Fighters, Rankings, Search, Profile, Watchlist, Notifications).
19. Remove the backend `/api/v1/recommendations/*` router if you truly want zero-AI (it exists and has no ESPN data source).
20. Rewrite `PRODUCTION_AUDIT.md` + `PROJECT_STATUS.md` to reflect reality (or delete them — they're currently misinformation).

### Phase F — Tests (Day 4, ~8h) 🟡
21. Fix the 30 failures + 17 errors. Two structural causes:
    - Tests reference removed internals (`SyncState.last_sync_at`, old `SyncPlan(entity_types=...)`): update tests to the current `SyncState`/`SyncPlan` API (or add back-compat properties — cheaper).
    - SQLite/JSONB + sync-FakeRedis issues: either run tests against Postgres (docker-compose exists) or make models use portable types for tests.
22. **Acceptance: `pytest` → ≥ 250 green.**

### Phase G — Documentation (Day 4–5, ~4h)
23. Regenerate/align `DATA_CONTRACT.md`, `FIELD_COVERAGE.md`, `verify_espn.py` with the actual 27 tables and 101 routes. Make `verify_espn.py` do live HTTP checks (it currently prints a hardcoded table).

---

## 11. Corrective Prompt to Send Zaro AI (v3)

```
Your third delivery (from-github (3).zip) fixed the delivery integrity
(0 placeholder files), the backend boot (119 routes), migrations (001-003
clean on fresh Postgres), auth (register/login 201/200 with JWTs), and
mobile routing (all 8 routes wired). Genuine progress. But it is still
NOT buildable end-to-end. Fix these before re-exporting:

BACKEND (blocking):
1. backend/sync.py line ~158: SyncPlan is used but never imported —
   NameError on every sync run.
2. ALL 18 files in src/sync/upserts/ import 'src.domain.models.*'
   but src/domain/ does not exist. Models live in src/db/models/.
   Either create the domain shim or fix the imports. PROOF: after
   fixing #1, 'python sync.py --full --provider espn --entity event'
   fails with "No module named 'src.domain'". Row counts in every
   table remain 0. The sync engine must actually write rows.
3. GET /api/v1/rankings and /api/v1/champions return 500:
   "column rankings.source_provider does not exist". Migration 002
   adds syncable columns to 8 tables but NOT rankings. Add "rankings"
   to that list + ship migration 004 for existing DBs.

MOBILE (blocking):
4. package.json is missing expo-asset — 'npx expo export' fails with
   "The required package expo-asset cannot be found". Install it.
5. features/rankings/theme/index.ts contains JSX in a .ts file
   (40 tsc errors). Rename to .tsx.
6. assets/ directory is still absent (app.json references icon.png,
   splash.png, adaptive-icon.png).

POLICY (user requirement):
7. The AI modules (prediction/, recommendation/, intelligence/) and
   the mobile Predict/Recommendations tabs are STILL in the delivery.
   The user explicitly excluded ALL AI features. Remove them entirely,
   including backend /v1/recommendations/* and the mobile tabs.

TESTS & DOCS:
8. Test suite: 212 pass / 30 fail / 17 errors (259 collected). The
   failures are structural (tests reference removed SyncState fields;
   JSONB-on-SQLite). Reconcile tests with the current code.
9. Delete or rewrite PRODUCTION_AUDIT.md (claims 9.3/10
   "Production-ready") and PROJECT_STATUS.md (claims "48 tests, 91%
   coverage"). Both are false and will mislead anyone reading them.

ACCEPTANCE for the next delivery:
- python sync.py --full writes rows (SELECT count(*) > 0 on events,
  fighters, rankings; sync_runs has records)
- GET /api/v1/rankings and /champions return 200
- npx tsc --noEmit → 0 errors; expo export --platform ios completes
- no prediction/ recommendation/ intelligence/ anywhere
- pytest → 250+ passing
- assets/ present; no placeholder files; no api.mma-app.com /
  api.mma-platform.com placeholder hosts
```

---

## 12. Final Verdict

**Is this version good enough to build on? No — not yet. But it is the first version whose problems are all *small, named, and mechanical*.**

| | v1 (zip 1) | v2 (zip 2) | v3 (zip 3) |
|---|---|---|---|
| Delivery integrity | OK | broken (142 corrupt) | ✅ clean |
| Backend boots | 🔴 | 🔴 | ✅ |
| Auth works | — | 🔴 | ✅ |
| Migrations clean | — | 🔴 | ✅ |
| Sync writes rows | — | 🔴 | 🔴 (0 rows, 2 named import bugs) |
| Rankings API | — | 🔴 | 🔴 (1 missing column) |
| Mobile routes | 🔴 | 🟡 | ✅ |
| Mobile bundles | — | 🔴 | 🔴 (1 missing dep) |
| tsc errors | ~440 | 718 (690 corrupt) | 40 (1 file) |
| Tests | — | 212/30/17 | 212/30/17 |
| AI removed | 🔴 | 🔴 | 🔴 |

**The exact remaining work:** 2 import bugs + 1 migration column (sync + rankings), 1 npm dependency + 1 file rename + assets (mobile bundle), favorites/watchlist contract unification, AI removal, and a test reconciliation pass. **4–6 focused days.** Every single item is verifiable with one command. If you hand this to Zaro again, use the Section 11 prompt verbatim and demand the acceptance criteria be met — or take it over yourself; at this point a competent engineer (or me) can close it faster than another full Zaro round-trip.

**The strongest signal in the whole report:** `sync_runs` has zero rows. The engine has never completed a run in any of the three deliveries. Until `python sync.py --full` ends with `Total: N inserted` and the events/fighters/rankings tables are populated, *nothing else matters* — the backend is an empty shell with excellent plumbing. Fix that first.
