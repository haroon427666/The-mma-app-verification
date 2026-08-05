# Migration Plan — 7 Phases (V10 → target)

Scope: fix the data path (the core blocker), restore mobile bootability, apply policy
removals, prove with tests. Executed incrementally — **no bulk file copies**; each change
is validated (importable, tested) before the next.

Environment constraints: no Docker daemon, no psql → **live Postgres cannot run here**.
Proof strategy: `alembic upgrade head --sql` for SQL validity + a new migration-coverage
test (SQLAlchemy `inspect` on SQLite against models where portable) + existing green suite.

---

## Status (2026-08-04)

| Phase | Status |
|---|---|
| 1 — Schema resolution | ✅ Backend complete — 002 rankings/synced_at + duration_ms Float fixed; 004 auth tables; 005 schema fixes; `--sql` chain 001→005 coherent |
| 2 — Sync write path | ✅ Backend complete — `sync.py` on real SyncEngine/SyncPlan; scheduler wiring via `SYNC_ENABLED`; Redis None-guards confirmed. Full run against live Postgres still NOT executed (no DB here) |
| 3 — Rankings & champions | ✅ Complete — `GET /v1/champions`, `/v1/champions/{division}` return 200 (10 tests). `/v1/champions/history` is an explicit empty stub (lineage table unmodeled) |
| 4 — Mobile bootability | ✅ Complete (2026-08-05) — `tsc --noEmit` = **0 errors** (was 67); `npx expo export` bundles web + android + iOS successfully. Items 1–7 verified already-present (routes, assets, expo-asset/react-native-web, `.tsx` renames) or fixed this session (favorites prefix `/v1/favorites` → `/v1/me/favorites` in `features/rankings/hooks/index.ts`; un-resolvable `./README.md` doc export removed from `app/bootstrap/index.ts`). Phantom paths deferred to Phase 7 item 5 keep/delete report |
| 5 — Policy removals (AI/betting) | ⛔ **SUPERSEDED (2026-08-05)** — deletion directive revoked by user; all 161 AI files restored from checkpoint `ff74cd8` + validated (see `SESSION_STATE.md` §5). Do NOT re-apply |
| 6 — Tests & docs | ✅ Backend complete — migration-coverage (9) + champions (10) tests added; suite **319 passed**; docs updated this session |
| 7 — Final verification | 🔄 Backend portion done (compileall, `--sql`, import scan, ruff clean); restoration verified (V9↔V10 diff + per-package self-checks + backend gates); mobile tsc re-verified 0 errors. Live-Postgres apply remains when a Postgres is available |

---

## Phase 1 — Schema resolution (drift + conflict) 【backend, ~half day】
**Goal:** fresh-DB `alembic upgrade head` is coherent; model↔migration drift eliminated.

1. `002_phase6_support.py`: remove `"rankings"` from the syncable-columns loop
   (001 already created `rankings.synced_at` at line 219 → DuplicateColumnError on fresh DB).
   Also confirm `statistics` is intentionally excluded (001 has synced_at at 236) and add
   whatever SyncableMixin columns the model requires that 001 lacks.
2. New migration `004_auth_tables.py`: create `users`, `user_sessions`,
   `user_preferences`, `favorite_fighters`, `favorite_events`, `watchlist_events`,
   `notifications`, `devices` (mirror `src/db/models/auth.py`; UUID PKs `gen_random_uuid()`,
   `TimestampMixin` cols).
3. New migration `005_schema_fixes.py`:
   - `promotions.first_event_date` → `Date`; `fanart_urls` → `JSONB` (match model).
   - `events.time_utc` → `Time`.
   - Add `updated_at` where models need it: `statistics`, `broadcasts`; add syncable
     trio (`synced_at/source_provider/version`) to `competitors`.
   - Fix `sync_jobs.duration_ms` type drift (check model).
4. Auto-gen is NOT used (drift comes from auto-gen); hand-tune to match models.
5. **Acceptance:** `alembic upgrade head --sql` shows 001→002→003→004→005 without
   duplicate `ALTER TABLE … ADD COLUMN synced_at` on the same table; model metadata vs
   migration column types agree on the fields we touched.

## Phase 2 — Sync write path (the blocker) [~1 day]
**Goal: `python sync.py --full` writes rows (proven with SQLite-compatible test / live Postgres).**

1. `sync.py`: rewrite `run_full_sync`/`run_enrichment_sync`/`run_rankings_sync` to the
   real API:
   - Build `jobs` registry (9 `SyncJob`s from `src/providers/espn/jobs`), `FullSyncPlan()`.
   - `SyncEngine(jobs=registry)`; `await engine.execute(plan, provider=espn, db_session=session)`.
   - Replace `SyncContext(db=engine, …)` usage per real dataclass (provider, async session).
   - Pass an `AsyncSession` (from `async_sessionmaker`) — never the engine.
2. `main.py` lifespan: construct real `SyncContext` + `SyncManager(context)`, `await
   manager.start()` behind `settings.sync_enabled` (default true, honor env).
3. `scheduler/locks.py` + `queue.py`: guard `redis is None` → healthy-degraded.
4. **Acceptance:** scheduler jobs register (`/api/scheduler/jobs` 200); `sync.py --full`
   in the test harness completes (or the exact next exception is fixed and documented);
   `sync_runs` row recorded.

## Phase 3 — Rankings & champions (data already in DB) [~2h]
1. Ensure `GET /api/v1/rankings*` returns 200 (unblocked by Phase 1).
2. Add `GET /api/v1/champions` + `GET /api/v1/champions/{division}` from `Ranking`
   where `is_champion=true` (reuse `_ranking_to_entry` pattern, cache-aside TTL 600s).
3. **Acceptance:** `curl /api/v1/champions` → 200 schema (empty or populated); tests added.

## Phase 4 — Mobile bootability (baseline restore/build) [~1–2 days]

> ✅ **COMPLETE (2026-08-05)** — typecheck + Metro export acceptance both green. Status per item:

1. Create `mobile/app/*.tsx` routes (index=Home, events, fighters, rankings, search,
   profile, notifications, watchlist) with default exports → screen components.
   — ✅ already present (all 10 route files tracked, incl. `_layout.tsx` + `+not-found.tsx`).
2. Create `mobile/components/shell/MaintenanceScreen.tsx` + `OfflineBanner.tsx`.
   — ✅ already present (also `ErrorBoundary.tsx`, `SplashScreen.tsx`).
3. Rename 6 JSX-containing `.ts` → `.tsx` (design-system/images, design-system/stories,
   features/fighters/theme, features/rankings/theme, app/analytics/AnalyticsManager,
   app/notifications/NotifManager).
   — ✅ already renamed; all tracked.
4. `mobile/package.json`: add `expo-asset`, `react-native-web` (web), remove Predict deps.
   — ✅ already present (`expo-asset ~11.0.1`, `react-native-web ^0.19.13`).
5. Add `mobile/assets/` (icon/splash/adaptive) or strip refs from `app.json`.
   — ✅ already present (icon.png, splash.png, adaptive-icon.png; referenced in `app.json`).
6. Single API base URL via `EXPO_PUBLIC_API_URL`; delete dead `app/_infra.ts`.
   — ✅ `app/_infra.ts` never existed; live client `services/api.ts` + `NetworkConfig.ts`
      both key off `EXPO_PUBLIC_API_URL`. `app/networking` barrel (AxiosClient/Endpoints/
      RequestBuilder) had no importers — **deleted in Phase 7 item 5**.
7. Align favorites (`/v1/me/favorites/*`), watchlist (concrete), rankings
   (`/rankings/{division}`) calls.
   — ✅ fixed `features/rankings/hooks/index.ts:61` `/v1/favorites/fighters/{id}` →
     `/v1/me/favorites/fighters/{id}`. Watchlist concrete calls (`/v1/me/watchlist/events`)
     verified everywhere live; rankings live client uses `/v1/rankings/{division}` +
      `/v1/rankings/p4p`. Phantom paths (status/goat/prospects/movement/streaks/history/
      changes) → resolved in Phase 7 item 5 (goat/prospects/movement/streaks now real
      backend endpoints; history/changes/status removed or list-derived).
8. **Acceptance:** `npx tsc --noEmit` → 0 project errors; `npx expo export` completes
   (subject to sandbox memory).
   — ✅ `tsc --noEmit` = 0 errors; `npx expo export` → Web 3435ms / Android 6528ms / iOS 10185ms
     bundled, 47 assets, exported to `dist/`. One blocker fixed en route: `app/bootstrap/index.ts`
     exported `BootstrapDocs` from `./README.md` (Metro cannot resolve `.md` runtime imports;
     no metro.config registers the ext; export was unreferenced → removed, tsc still 0).

## Phase 5 — Policy removals (no AI / no betting) [~hours day]

> ⛔ **SUPERSEDED (2026-08-05):** the user revoked the no-AI deletion directive. All seven AI
> areas (161 files) were restored from checkpoint `ff74cd8` and validated (`SESSION_STATE.md`
> §5). The steps below are retained for the historical record only — **do not execute them.**

1. Delete `prediction/`, `recommendation/`, `intelligence/`, `platform/` top-level dirs.
2. Delete `mobile/features/predictions/`, `mobile/features/recommendations/`, remove
   Predict/Recommend tab entries in `MainNavigator.tsx`.
3. Delete `mobile/features/events/components/FightPredictionCard.tsx`, `OddsCard.tsx`.
4. Decision: keep or remove backend `src/api/v1/recommendations.py` (rules-based feed).
   Default per policy: **remove** (no-AI), unless user wants the "because watched" feed.
5. **Acceptance:** `grep -ri prediction|recommendation|intelligence backend/src mobile/app mobile/features` → only docs/comments.

## Phase 6 — Tests & docs [half day]
1. Restore `backend/tests/integration/test_cache.py` from reference ONLY if it still
   applies after cache rewrite (else delete ref file as superseded).
2. Add migration-coverage test (model metadata vs `alembic`-declared columns on touched
   tables + auth tables exist).
3. Add champions endpoint tests; auth e2e already passes (SQLite) — add an integration
   check that the auth SQL schema exists in our migrations.
4. Update `PROJECT_STATUS.md` + `docs/PERFORMANCE.md` with verified numbers
   (300 tests, 91 paths, alembic head 005, sync status — honest).
5. **Acceptance:** `pytest -q` green (still 300+, no regressions); `ruff check src` clean.

## Phase 7 — Final verification [(~ first half day of next session)]
1. `python -m compileall -q src tests sync.py scheduler.py` → clean.
2. `alembic upgrade head --sql` → coherent 001→005 chain, no duplicate adds.
3. Orphan/dead-import scan: after Phase 5, run a fresh import scan of `backend/src`
   (`python -c "import src.api.main"` + each module) to confirm nothing references
   deleted dirs.
4. Circular-import + duplicate-export scan (grep `from src.domain` resolves; no `prediction`
   refs remain in `pyproject`, Docker, docker-compose, docs).
5. Contract re-diff (mobile vs OpenAPI) after Phase 4 → report remaining phantoms with a
   keep/delete decision. **✅ Complete (2026-08-05) — implemented:** `/v1/rankings/goat|prospects|movement|streaks`,
   `/v1/title-defenses`, `/v1/fighters/{id}/similar` (+ `is_title` filter on `/v1/fights`) —
   13 new tests, pytest **332 passed**, ruff/mypy clean. **Removed as not-feasible (no data model):**
   rank/champion history screens+hooks (no snapshot lineage; `/v1/champions/history` is an empty
   stub), `/v1/predictions/*`, `/v1/fighters/trending`, style-analysis, timeline/achievements,
   `elo`/`composite` rankings, watchlist reminders, follows, `/status` membership checks (now
   list-derived). **Fixed wrong paths:** home live → `/v1/events/live`, fighter stats/history →
   `/statistics`/`/history`, watchlist list → `/v1/watchlist/events`, favorites → `/v1/me/favorites`.
    **Deleted dead code:** `app/networking/`, `components/screens/HomeScreen.tsx`,
    `features/rankings/screens/RankingsScreen.tsx`, `features/rankings/api/queries.ts`,
    `features/watchlist/WatchlistModule.tsx`, phantom fighter/rankings API constants + hooks.
    Mobile: `tsc --noEmit` **0 errors**, `npx expo export` bundles web/android/iOS.
    **Round 2 (2026-08-05) — full contract audit:** scripted cross-reference of all **100 backend
    routes** vs mobile literal URLs found **39 phantom paths**; all resolved. **Implemented**
    `GET /v1/events/{id}/fights|results|statistics` (+`EventStatisticsResponse` schema, 7 tests in
    `backend/tests/api/test_event_extras.py`); **fixed** fighters history (`/v1/fighters/{id}/fights`
    → `/history`), watchlist list (`/v1/me/watchlist/events` → `/v1/watchlist/events`), favorites
    list (`/v1/me/favorites/fighters` → `/v1/me/favorites`, ID→detail mapping), push-token register
    (`/v1/me/devices` → `/v1/notifications/push-token`); **deleted as dead/unwired** the
    `features/predictions/` + `features/recommendations/` modules (latter imported but never
    rendered — no tab), events reminder/prediction api+hooks+mutation+store+components, dead
    `watchlist/api/queries.ts`, `search/types-and-api.ts`, `profile/index.ts` +
    `profile/screens/ProfileScreen.tsx` + `profile/api/queries.ts`, profile `/v1/me/stats|export`
    calls, notifications device-unregister call (no backend route). Re-audit:
    **PHANTOM_COUNT 0**. Gates: pytest **339 passed**, ruff clean, mypy clean (184 files),
    tsc 0 errors, expo export green.
6. `pytest -q` final → target 300+ / 0 fail. **✅ 339 passed / 0 fail.**

---

## Ordering rationale
Schema first (blocks everything), then the sync write path (the core blocker), then
endpoints, then mobile, then policy, tests, verify. Each phase ends with a runnable check.

## Open questions for user
1. **Account layer (Phase 5 of feature-master-plan)** — build JWT auth UX in mobile, or
   keep MVP account-free (local favorites)? Default: account-free.
2. **Recommendations router** — delete (no-AI policy) or keep rules-based feed?
3. **Mobile scope** — full bootable restore now, or defer mobile to a later session?
4. **Live Postgres** — can user provide a Postgres (Docker/remote) for the two
   migration phases? Otherwise I prove via `--sql` + SQLite coverage test.