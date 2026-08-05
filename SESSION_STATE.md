# SESSION_STATE.md — Handoff for Next OpenCode Session

> Read this file completely before touching anything. It contains everything needed to
> resume work accurately. Zero-memory-friendly: the next session should start from
> Section 14 (Next Session Plan) and work backward into the details as needed.

---

## 1. Project Overview

- **Project**: MMA Intelligence (mma-app-zaro-ai-repo) — a full-stack MMA analytics app:
  AI fight predictions, fighter rankings, personalized recommendations, event/fighter search.
- **Monorepo layout (repo root)**:
  - `backend/` — FastAPI + SQLAlchemy + Alembic backend (Python)
  - `prediction/`, `recommendation/`, `intelligence/` — AI Python packages (self-contained, own verify.py)
  - `data_platform/` — data engineering platform (identity, trust, resolution, scheduler, normalization, mappers, connectors, hardening, integration) — **renamed from `platform/`**
  - `mobile/` — React Native + TypeScript client (Expo-style structure, tsc-based typecheck)
  - `docs/` (or root markdown) — planning docs: `01-instruction-index.md`, `04-migration-plan.md`, `PROJECT_STATUS.md` etc.
- **Git**: repo at `C:\Users\-\Downloads\mma-app-zaro-ai-repo\from-github\mma-app-zaro-ai-repo`, branch `main`.
  Commits: `9e666a1` (Initial upload) → `ff74cd8` (Recovery checkpoint) → `af731e1` (restoration +
  Phase 4 fixes committed — current HEAD).
- **Current milestone**: V10 AI-module restoration **complete and verified**; mobile Phase 4
  bootability **complete** — `tsc --noEmit` = 0 errors AND `npx expo export` bundles
  web/android/iOS (both committed in `af731e1`). Phase 7 item 5 contract re-diff **executed
  in two rounds**: round 1 implemented 7 endpoints (rankings/fighters) and removed not-feasible
  phantoms; round 2 ran a full scripted audit (100 backend routes × mobile literals, 39 phantom
  paths → 0), implemented 3 event sub-routes, rewired 4 wrong paths, deleted the
  predictions/recommendations mobile modules + dead query layers. All gates green:
  pytest **339 passed**, ruff clean, mypy clean, tsc 0, expo export green. Everything
  uncommitted — ONE final commit pending user review of the report.
  Remaining after commit: live-Postgres apply, optional consolidation.
- **Environment**: Windows 10/11, PowerShell 5.1. All commands run from repo root or `mobile/`
  via the `workdir` parameter (never `cd` in commands).
  - Backend/AI Python: venv at `C:\Users\-\AppData\Local\Temp\opencode\mma-venv\Scripts\python.exe`
  - AI self-checks must run with `$env:PYTHONPATH = repo root` and `$env:PYTHONIOENCODING="utf-8"` set,
    from the repo root.
  - Mobile typecheck: `& ".\node_modules\.bin\tsc.cmd" --noEmit` run from `mobile/` (workdir=mobile).

---

## 2. Session Summary

This session (the "restoration + Phase 4" session) did two large bodies of work.

### Part A — V10 AI-module restoration (completed in this session)

The repo had suffered **uncommitted deletions** of the AI feature areas (prediction/,
recommendation/, intelligence/, platform/, and the mobile predictions/recommendations/intelligence
feature folders) — triggered by an instruction doc (`01-instruction-index.md` section F6/P1 and
"Delete table" L176–182, plus `04-migration-plan.md` Phase 5 row) that was later superseded by the
user's directive to restore everything. Details in Section 4/5.

The user's 7-point restoration report was produced and delivered (structure: restored list,
V9↔V10 comparison, validated+fixed list, deleted-as-duplicates, architectural adjustments,
not-restored, gates). See Section 5.

### Part B — Mobile Phase 4 bootability (completed in this session)

Brought `mobile/` from **67 TypeScript errors to 0** (tsc `--noEmit`, strict mode). Work clusters:

1. **Missing npm dependencies (6 errors)** — installed:
   - `@tanstack/query-async-storage-persister@^5.101.4`
   - `@tanstack/react-query-persist-client@^5.101.4`
   - `@hookform/resolvers@^5.7.1`
   (fixes `providers/QueryProvider.tsx` persister imports and
   `components/auth/LoginScreen.tsx` + `RegisterScreen.tsx` zod resolver imports; `package.json` +
   `package-lock.json` updated)
2. **Missing modules (6 errors)**:
   - Created `mobile/app/networking/NetworkAnalytics.ts` re-exporting `NetworkAnalytics`/`networkAnalytics`
     from `NetworkLogger.ts` (the class already lived there; two files imported `./NetworkAnalytics`)
   - Created `mobile/app/bootstrap/README.md` + ambient `declare module '*.md'` in new `mobile/globals.d.ts`
   - `design-system/tokens/extended.ts`: wrong relative import `'../colors'` → `'./colors'`
   - `design-system/animations/animationLib.ts`: wrong relative import `'../../tokens'` → `'../tokens'`
3. **Missing/wrong exports and imports (~25 errors)**:
   - `app/deeplinks/DeeplinkManager.ts`: `class RouteRegistry` → `export class RouteRegistry`
   - `app/networking/OfflineQueue.ts`: removed dead `NetworkError` import (not exported by NetworkUtils)
   - `app/offline/OfflineConfig.ts`: added `MAX_QUEUE_SIZE: 500` to `OFFLINE_CONSTANTS`
   - `app/storage/StorageManager.ts`: added `export { storageLogger } from './StorageConfig'` re-export
   - `app/session/SessionDevice.ts`: added `sessionManager` to the `./SessionManager` import
   - `design-system/theme/ThemeTypes.ts`: added `ThemeContextValue` interface
   - `design-system/images/index.tsx`: added `AvatarImage` (=FighterAvatar) and `PosterImage` (=EventPoster) aliases
   - `design-system/hooks/index.ts`: `Dimensions` imported from `'react'` (wrong) → from `'react-native'`
   - Fighter hooks wiring: `features/fighters/index.ts` now also re-exports legacy
     `useFighterList`/`useFighterDetail` from `./hooks/useFighters`; `features/fighters/screens/index.tsx`
     imports `useFightersStore` from `'../store'` instead of `'../hooks'`
   - `hooks/index.ts` (global barrel): replaced stale names with real ones —
     `useFighters, useFighter, useFavoriteFighter, useStats, useHistory, useSimilarFighters` (fighters),
     `useEloRankings` (rankings) — previously `useFighterList/useFighterDetail/useFavoriteFighters/useFighterStats/useFightHistory/useRankings`
   - `features/rankings/screens/index.tsx`: added `useTitleDefenses` to the `../hooks` import (hook exists, wasn't imported)
   - `features/rankings/types.ts`: added optional `isChampion?: boolean` to `RankingFighter`
   - `features/rankings/navigation/RankingsStack.tsx`: replaced all 9 `Promise.resolve({ default: () => null })`
     placeholder screens with the real screens from `'../screens'` via `getComponent={() => require('../screens').X}`
4. **Type bugs (~25 errors)**:
   - `features/events/types.ts`: `FightCardEntry extends BaseFight` failed (narrower re-declarations of
     `result/status/cardSegment`) → `extends Omit<BaseFight, 'result' | 'status' | 'cardSegment'>`
   - `features/events/hooks/useWatchlist.ts`: mutation variable was `string` but `onMutate`/`onError`
     destructured `{ id }` → refactored to `(id: string)` end-to-end
   - `features/events/screens/EventDetailScreen.tsx`: `onFightPress={(fightId) => ...}` → `(fightId: string)`
   - `features/events/stories/EventCard.stories.tsx`: mockEvent typed `as any` (missing ~12 ExtendedEvent fields)
   - `features/search/SearchModule.tsx` + `features/search/types-and-api.ts`:
     `useInfiniteQuery` overload failures → dropped explicit generic, `initialPageParam: ''`,
     `cursor: pageParam as string | undefined`, `getNextPageParam: (last) => last.nextCursor`
     (string|null is accepted because getNextPageParam returns `TPageParam | undefined | null`)
   - `features/search/SearchModule.tsx`: `autoData.slice(...)` → `(autoData ?? []).slice(...)`
   - `design-system/theme/ThemeTypes.ts`: palette `surface`/`text` typed as `typeof surface.light`
     (light-only) → union `(typeof surface)['light'|'dark'|'amoled']` (ThemeBuilder builds dark/amoled too)
   - `theme/motion.ts`: removed dead `themeIndex` export (referenced non-existent `colors/typography/spacing/radius/shadows`
     shorthand names; no consumers existed)
5. **React-UMD / isolatedModules / top-level await (~10 errors)**:
   - `app/auth/Authorization.ts`: added `import * as React from 'react'`; PERMISSIONS cast via
     `as unknown as Record<string, UserRole[]>`; `withAuth` renders via
     `React.createElement(Component as React.ComponentType<any>, props as any)` (file is `.ts`, no JSX)
   - `app/analytics/AnalyticsHooks.ts`: `useFunnel` cleanup `() => funnelTracker.end(...)` →
     `() => { funnelTracker.end(...); }` (void return)
   - `app/bootstrap/BootstrapState.ts`: removed top-level dynamic `await import('./BootstrapTypes')` → static `BootstrapError` import
   - `app/networking/Interceptors.ts`: replaced all `new (await import('./NetworkTypes')).X(...)`
     (one was top-level await → TS1308) with static imports `RateLimitError, APIError`
   - `hooks/usePerformance.ts`: added `import * as React from 'react'` (React.lazy used at line ~152)
   - `release/ReleaseStores.ts`: `releaseLogger.error(msg, error)` → 1-arg call (logger's `error(m: string)`)
   - `release/index.ts`: `ReleaseConfig` (a type) split out of the value re-export → `export type { ReleaseConfig }`
   - `security/SecurityHooks.ts`: `SecurityConfig`/`SecurityLevel` split into `export type` re-export

Result: **`mobile/node_modules/.bin/tsc.cmd --noEmit` = 0 errors** (was 67).

---

## 3. Deliverables Progress

| Deliverable | Status | Notes |
|---|---|---|
| Restoration report (7-point structure) | ✅ Completed | Delivered to user; full inventory in Section 5 |
| AI module restoration (7 areas, 161 files) | ✅ Completed | Restored from V10 git checkpoint, validated, bugs fixed |
| Backend gates green | ✅ Completed | pytest 319 passed; ruff clean; mypy clean (184 files) |
| Mobile Phase 4 bootability | ✅ Completed | tsc 0 errors; 3 npm deps installed; 3 new files; ~40 files fixed |
| Phase 7 verification + docs update | ✅ Completed | `04-migration-plan.md` Phase 7 items 5/6 + `backend/PROJECT_STATUS.md` + this file updated through round 2 |
| Final commit | ⏳ Pending | One commit (exclude `session-ses_0327.md`, `mobile/dist/`) after user reviews the final report |

---

## 4. Recovery History

### The incident
- The repo had uncommitted **working-tree deletions** of all AI areas (the `prediction/`,
  `recommendation/`, `intelligence/`, `platform/` packages and the mobile
  `features/predictions`, `features/recommendations`, `intelligence` folders).
- These deletions were caused by following "deletion" instructions in
  `01-instruction-index.md` (F6/P1/ZV3–5, Delete table L176–182) and `04-migration-plan.md`
  (Phase 5 row). The user later **superseded** those instructions: everything was to be restored.
- A prior crash of the agent session happened earlier; the checkpoint commit `ff74cd8`
  ("Recovery checkpoint: backend migration fixes (002/004/005), sync CLI on real engine, champions
  endpoints, mobile bootability work-in-progress") was the recovery anchor.

### Recovery process
1. Verified with `git status` that the deletions were **uncommitted** (working-tree only) — the
   files still existed in commit `ff74cd8`.
2. Recovered with `git restore .` (i.e., restored the V10 working tree from the V10 checkpoint).
   **No files were manually copied from the V9 repo.**
3. Cross-checked against the historical V9 reference repo at
   `C:\Users\-\Downloads\from-github (1)\from-github\mma-app-zaro-ai-repo` (CRLF-normalized,
   relative-path-keyed diff per AI area) to confirm nothing was lost vs the previous generation.

### Important recovery decisions
- **Restore-in-place (V10 authoritative)**: since the deletions were uncommitted, restoration = `git restore .`.
- **V10 wins on all 13 real content diffs vs V9** (see Section 5) — V9 was not imported from.
- Renamed `platform/` → `data_platform/` (Section 9) as the only architectural adjustment.

---

## 5. AI Module Restoration

### What was restored and where it came from
All 161 files across 7 areas were restored **from the V10 checkpoint commit `ff74cd8`** via
`git restore .` (they existed in history; deletion was working-tree only):

- `prediction/` (20 files) — fight predictor, models, finish predictor, verify.py
- `recommendation/` (28 files) — recommender pipeline, verify.py
- `intelligence/` (58 files) — analytics (age curves, momentum), embeddings (matchup embedder),
  tests (test_all.py), verify.py
- `platform/` (19 files) → renamed to `data_platform/` — identity, trust, resolution, scheduler,
  scheduler_jobs, normalization, mappers, connectors, hardening, integration, verify.py
- `mobile/features/predictions/` (18 files), `mobile/features/recommendations/` (9 files),
  `mobile/intelligence/` (9 files)

### Validation performed
- **V9↔V10 comparison**: file sets identical in all 7 areas. Initial 100% diff was CRLF noise;
  after line-ending normalization only **13 real content diffs**, all resolved in V10's favor:
  - 10 × `recommendation/*.py` — V9 files were garbage placeholders ("This file could not be retrieved…");
    V10 holds the real implementations
  - 3 × mobile files — V10 versions are the consolidated modern barrels; V9 had a broken `../models` import
- **Per-package self-checks** (run with `PYTHONPATH`=root + utf-8): prediction 10/10, recommendation 10/10,
  intelligence 6/6, data_platform "ALL 45 ASSERTIONS PASS — Phase 19.1-19.12 Complete"
- **intelligence pytest suite**: `intelligence/tests/test_all.py` = 31 passed
- **Backend gates**: pytest 319 passed; ruff all checks passed; mypy no issues in 184 source files

### Bugs found and fixed in restored modules (11 files)
| File | Bug | Fix |
|---|---|---|
| `prediction/__init__.py` | imported nonexistent `train_models` — blocked the whole package | `train_fight_predictor, cross_validate` |
| `prediction/models/finish_predictor.py` | string `most_likely` key broke the probability-dict contract | removed key (no consumers) |
| `intelligence/analytics/age_curves.py` | `career_stage(22)` wrongly returned "Young Prospect" (0.50 boundary bug) | restructured boundary |
| `intelligence/embeddings/matchup_embedder.py` | champion-vs-weak matchup scored 0.58 (sigmoid ×3.0 too flat) | sharpened to ×6.0 (0.66) |
| `intelligence/analytics/momentum.py` | `trajectory_slope` returned 0 on flat recent windows | widen-on-flat fallback |
| `intelligence/tests/test_all.py` | stale `>0.9` champion-slot assert contradicted unit-normalized embedder | relative-dominance assert |
| `data_platform/trust/__init__.py` | unrecorded conflict/latency scored as *perfect* (1.0) | neutral 0.5; sherdog trust now 0.68 |
| `data_platform/hardening.py` | imported `name_similarity` from wrong module | from `identity` |
| `data_platform/identity/__init__.py` | present-field weight renormalization in compare_fighters/compare_events | fixed renormalization |
| `data_platform/verify.py` + `integration.py` | stale docstrings referencing `platform/` | updated to `data_platform/` |
| `mobile/features/predictions/types.ts` | missing `PredictionDashboard` export (TS1205 re-export issue) | added `export interface PredictionDashboard` |

Plus: `mobile/features/predictions/api/index.ts` (AccuracyStats→PredictionAccuracyStats),
`components/PredictionsComponents.tsx` (dropped stale ConfidenceBadgeProps import),
`screens/PredictionsScreen.tsx` (single source of truth).

### Deleted as dead/orphaned duplicates (2 files)
- `mobile/features/predictions/screens/PredictionScreen.tsx` (third-generation dead copy)
- `mobile/features/predictions/screens/index.tsx` (orphaned, broken, held all 13 AI tsc errors;
  `PredictionsScreen.tsx` is the wired, compiling one)

### Compatibility checks
- Backend has **zero references** to root `platform` package; no bare `import platform` anywhere.
- All `data_platform` internal imports rewritten `from platform.` → `from data_platform.` (35 imports, 19 files).
- Mobile AI feature paths: 0 tsc errors (all errors were in non-AI areas).

### Remaining concerns
- Parallel layers inside `features/predictions` and `features/recommendations` (`hooks/`+`repository/`+`stores/`
  vs consolidated `api/`) both compile and are exported — flagged for a future consolidation, not this restoration.
- Fallback GPU availability (onnxruntime) not verified in-order.
- Xcode Previews safety not verified.

---

## 6. Current Repository Status

- **Git**: branch `main`; HEAD = `af731e1` ("restoration + Phase 4 completion"). Working tree has
  **many uncommitted changes** (Phase 7 item 5, both rounds): backend (3 event endpoints +
  20 tests), mobile rewiring + deletions, and the 4 files from the previous session.
  Commit ONLY on explicit user request — one final commit, excluding the stray
  `session-ses_0327.md` and regenerated `mobile/dist/` (expo output; not tracked).
- **Backend**: pytest **339 passed** (332 + 7 new event-extras tests in
  `tests/api/test_event_extras.py`); ruff clean; mypy clean (184 files). Endpoints: 100 total —
  round 1 added `/v1/rankings/movement|goat|prospects|streaks`, `/v1/title-defenses`,
  `/v1/fighters/{id}/similar`, `is_title` filter; round 2 added
  `GET /v1/events/{id}/fights|results|statistics` (+ `EventStatisticsResponse`).
- **Contract audit**: scripted cross-ref of 100 routes vs mobile literal URLs — was 39 phantom
  mobile paths, now **PHANTOM_COUNT 0** (script at `C:\Users\-\AppData\Local\Temp\opencode\api_audit.py`).
- **Mobile TypeScript**: `tsc --noEmit` = **0 errors** (re-verified after round-2 cleanup;
  one leftover `Reminder` import in `events/offline/queue.ts` fixed).
- **AI packages**: prediction 10/10, recommendation 10/10, intelligence 6/6, data_platform 45/45 assertions;
  intelligence tests 31 passed (unchanged by rounds 1–2).
- **Build status**: `npx expo export` **PASSED** (2026-08-05, re-verified after round 2) —
  web 4741ms / Android 10197ms / iOS 15059ms, 47 assets → `dist/`. Live Postgres still
  unavailable — no runtime boot against a real DB.
- **Untracked files**: `backend/tests/api/test_event_extras.py` (new, 7 tests),
  `backend/tests/api/test_rankings_extras.py` (new, 13 tests), a pre-existing stray
  `session-ses_0327.md` at root (not ours — do not commit without asking).

---

## 7. Remaining Work (execution order)

1. **[DONE] Phase 7 item 5 — contract re-diff (mobile vs backend), phantom keep/delete decisions**:
   Completed this session (see "Phase 7 item 5 — executed" below). All phantom calls resolved:
   - **Implemented on backend** (real data, tested): `/v1/rankings/movement` (two-snapshot rank
     delta), `/v1/rankings/goat` (champions by title_defenses + finish rate score), `/v1/rankings/prospects`
     (active unranked by finish rate), `/v1/rankings/streaks` (consecutive WIN outcomes),
     `/v1/title-defenses` (champion rows with defenses > 0), `/v1/fighters/{id}/similar`
     (physical/record feature distance), `fights` list gained `is_title` filter.
   - **Removed as not-feasible** (explained in final report): rank/champion `history` screens +
     hooks (no snapshot/lineage data — rankings have only the latest sync; champions have no
     won-date/reign model), `/v1/predictions/*` (no backend router, no model artifacts wired to DB),
     `/v1/fighters/trending`, style-analysis, fighter timeline/achievements, rank-history,
     `elo`/`composite` ranking lists, watchlist reminders, follows, `/status` membership checks.
   - **Fixed wrong paths**: home live events → `/v1/events/live`; fighter stats → `/statistics`,
     history → `/history`; watchlist list → `/v1/watchlist/events` (was `/v1/me/watchlist/events`),
     favorites list → `/v1/me/favorites`; watchlist fighters tab → `/v1/watchlist/fighters`.
   - **Membership checks now list-derived**: `useIsFavorite` reads `/v1/me/favorites`; events
     `useWatchlist` was already list-based (store `watchedIds`).
    - **Dead code deleted**: `app/networking/` tree, `features/rankings/screens/RankingsScreen.tsx`,
      `features/rankings/api/queries.ts`, `features/watchlist/WatchlistModule.tsx`,
      `components/screens/HomeScreen.tsx`, dead home-endpoint constants, phantom fighter APIs
      (trending/champions/predictions/timeline/achievements/style-analysis/follows/compare),
      rankings history/champion-history screens + stack routes.
    **Round 2 (2026-08-05) — full scripted audit + second cleanup** (details §7b): re-ran the
    cross-reference (100 routes × mobile literals), found 39 phantom paths, resolved ALL:
    implemented `GET /v1/events/{id}/fights|results|statistics`; rewired fighters history →
    `/v1/fighters/{id}/history`, watchlist list → `/v1/watchlist/events`, favorites list →
    `/v1/me/favorites` (ID→detail mapping), push-token → `/v1/notifications/push-token`;
    removed profile `/v1/me/stats|export`; deleted `features/predictions/` +
    `features/recommendations/` modules (no backend predictions router; recs module never
    rendered), events reminder/prediction layers, dead `watchlist/api/queries.ts`,
    `search/types-and-api.ts`, parallel `profile/` layer. Re-audit: **PHANTOM_COUNT 0**.
2. **[MEDIUM] Live-Postgres verification** (only when a Postgres is available): `alembic upgrade head`,
   sync run, endpoint smoke tests. Phase 2 note: `--sql` chain 001→005 coherent; full sync run never executed.
3. **[LOW, backlog] Mobile navigation polish**: `features/predictions/` + `features/recommendations/`
   were removed (round 2) — the Predictions/Recommendations tabs are gone; the backend
   recommendations feed API remains real (home uses `/v1/recommendations/fighters`). A future
   session could re-surface recommendations in the UI on request.
4. **[LOW, backlog] Verify GPU fallback path** (onnxruntime) and Xcode Previews safety.

---

## 7b. Phase 7 item 5 — executed (this session)

Backend additions in `backend/src/api/v1/other.py` (movement/goat/prospects/streaks +
`title_router`), `backend/src/api/v1/fighters.py` (`/{fighter_id}/similar`),
`backend/src/api/v1/fights.py` (`is_title`), schemas in `src/schemas/misc.py` +
`src/schemas/fighter.py`, router registered in `src/api/v1/__init__.py`, tests in
`backend/tests/api/test_rankings_extras.py` (13 tests). Gates: pytest **332 passed**,
ruff clean, mypy clean (184 files). Mobile: home/fighters/rankings/watchlist features
rewired (see Section 7), tsc **0 errors**, `npx expo export` bundles web/android/iOS.
Not-feasible removals documented in the final report to the user.

### Round 2 — full contract audit (2026-08-05)

- **Audit tool**: `C:\Users\-\AppData\Local\Temp\opencode\api_audit.py` (venv python; arg = repo
  root). Cross-references every backend route (grep `@router` decorators, prefix-aware) against
  mobile string literals (grep `api.get/post/...('...')`); prints METHOD/PATH/FILE:LINE/
  MOBILE_USED/TESTED + `MOBILE_PHANTOM_PATHS` list. Two fixes were needed during development:
  router-prefix regex must be `([A-Za-z_]*_?router)` (bare `router` names), and phantom matching
  must be anchored (`"^" + route_regex(path) + r"(?:\?[^\"'`]*)?$"`) or literal prefixes
  (`/v1/rankings`) false-positive.
- **Backend additions** (`backend/src/api/v1/events.py` + `backend/src/schemas/event.py`):
  `GET /v1/events/{event_id}/fights` (fight card), `GET /v1/events/{event_id}/results`
  (only fights with `result_method` set), `GET /v1/events/{event_id}/statistics`
  (total/title/decisions/finishes/ko_tko/subs/countries/weight-classes →
  `EventStatisticsResponse`). Refactored `_build_fight_items()` out of `_event_to_detail`
  (winner derived from competitor `outcome == "WIN"`; fighter country column is `nationality`).
  All cached via `cached_json_response(ttl=120)`.
- **Tests**: `backend/tests/api/test_event_extras.py` — 7 tests (fights 2, results 2,
  statistics 3), direct `asyncio.run` calls. **7 passed** (23.57s, 5 pre-existing warnings).
- **Mobile path fixes** (4): FightersScreen HistoryTab `/v1/fighters/{id}/fights` →
  `/v1/fighters/{id}/history` (renders `outcome === 'WIN'`, `opponentName`, `method`, `round`);
  WatchlistScreen list paths → `/v1/watchlist/events` + `/v1/me/favorites` (favorites returns
  string IDs only → repo maps ID→`/v1/fighters/{id}` detail); notifications `register()` →
  `POST /v1/notifications/push-token` body `{token, platform}` (backend has no DELETE route →
  `unregister()` is now local-only).
- **Profile cleanup** (`features/profile/ProfileModule.tsx`): removed phantom
  `/v1/me/stats` + `/v1/me/export` (api/repo/hooks/screen sections + `useUserStats`/
  `useExportData` exports in `features/index.ts`).
- **Mobile deletions (round 2, 19 paths)**: `features/predictions/` (no backend predictions
  router), `features/recommendations/` (never rendered — imported by MainNavigator but no tab),
  `events/api/queries.ts` + `predictions.api.ts` + `reminders.api.ts`, `events/hooks/usePredictions.ts`
  + `useReminder.ts`, `events/mutations/useReminders.ts`, `events/store/reminder.store.ts`,
  `events/components/FightPredictionCard.tsx` + `OddsCard.tsx` + `ReminderButton.tsx`,
  `events/utils/reminder.ts`, `watchlist/api/queries.ts`, `search/types-and-api.ts`,
  `profile/index.ts` + `profile/screens/ProfileScreen.tsx` + `profile/api/queries.ts` +
  `profile/README.md`.
- **Barrels/consumers updated**: `navigation/MainNavigator.tsx` (Predictions tab + both stack
  imports removed; now 8 tabs), `hooks/index.ts`, `features/index.ts`, all `features/events/*`
  barrels + types + repository + `FightCard`/`FightRow` + `EventDetailScreen`/`FightCardScreen`
  rewrites, `events/offline/queue.ts` (dropped `Reminder` type + reminder actions).
- **Gates (round 2)**: pytest **339 passed**, ruff clean, mypy clean (184 files),
  tsc 0 errors, `npx expo export` green, audit **PHANTOM_COUNT 0**.

---

## 8. Known Issues

- **Technical debt**: legacy vs modern dual trees in `features/fighters` (`hooks/useFighters.ts` +
  `api/queries.ts` legacy generation, kept alive only via the two barrel re-exports) and
  `features/rankings/api/queries.ts` (legacy `useRankings`, unused).
- **Technical debt**: `design-system/theme/ThemeTypes.ts` declares its own `ThemeContextValue`
  structurally identical to the one in `ThemeContext.ts` (two types, same name — safe because
  structural typing, but a future refactor could unify them via re-export).
- **Casts/`any` left in place** (deliberate, minimal): `Authorization.ts` createElement casts,
  search `pageParam as string | undefined`, `EventCard.stories.tsx` mockEvent `as any`,
  `RankingsStack.tsx` uses `require('../screens')` (matches existing pattern),
  `usePerformance.ts` `React.lazy` generic.
- **`storageLogger`**: re-exported from `StorageManager.ts` via a second export statement
  (duplicate symbol in one file — valid TS, slightly unusual).
- **SecurityHooks.ts** still imports `securityConfig` (unused after the export split); harmless
  (no `noUnusedLocals`), could be cleaned.
- **CRLF**: repo has mixed line endings; git warns "LF will be replaced by CRLF". Do not fight it.
- **Uncommitted everything**: ~80 files pending. Commit only on explicit user request.
- **Runtime not exercised**: no Metro/iOS/Android boot or Jest run this session; `react-native-mmkv`
  absent (persistence degrades gracefully to in-memory QueryClientProvider path).
- **`session-ses_0327.md`** at repo root is a stray untracked file from an earlier session — not part of this work.
- **Assumption**: deletion instructions in `01-instruction-index.md`/`04-migration-plan.md` are
  superseded — this is the user's explicit directive; do not re-apply deletions.

---

## 9. Important Decisions (and why)

1. **Restore in place from the V10 checkpoint (`git restore .`) instead of copying V9 files.**
   The deletions were uncommitted; the authoritative V10 content existed in `ff74cd8`. Copying V9
   would have imported stale/broken code (10 recommendation files were V9 garbage placeholders).
2. **V10 wins on all 13 content diffs vs V9.** CRLF-normalized comparison showed file sets identical;
   the 13 real diffs were V9 defects (placeholders, broken imports) or V10 improvements (modern barrels).
3. **Rename `platform/` → `data_platform/`.** The top-level `platform` package shadowed the Python
   stdlib `platform` module; numpy/scipy import chains (`platform.machine()`) crashed inside the
   package's own verify scripts. Done via `git mv` (history preserved); zero backend coupling existed.
4. **Delete the two orphan prediction screen files.** `PredictionScreen.tsx` and `screens/index.tsx`
   were dead third-generation duplicates; the broken one held all 13 AI tsc errors. The wired screen
   (`PredictionsScreen.tsx`) is the single source of truth.
5. **Create `NetworkAnalytics.ts` as a re-export shim** rather than editing the two importers —
   preserves the intended module layout (the implementation lives in `NetworkLogger.ts`).
6. **Wire real ranking screens in `RankingsStack`** instead of `() => null` placeholders — the
   screens already existed and compiled; placeholders made the stack non-bootable.
7. **Keep both fighter hook generations**; wire the legacy `useFighterList/useFighterDetail` into
   the barrel minimally rather than rewriting screens — smallest correct delta.
8. **Search infinite queries use `initialPageParam: ''` (string sentinel).** TanStack v5 infers
   TPageParam from `initialPageParam`; `undefined` sentinels caused overload/cast errors. `''`
   gives TPageParam=string; `getNextPageParam` returning `string|null` is legal (type allows
   `TPageParam | undefined | null`); `pageParam as string | undefined` keeps the API call type-safe.
9. **Theme palette typed as light|dark|amoled union** in `ThemeTypes` — ThemeBuilder legitimately
   builds all three modes; the old `typeof surface.light` typing was wrong, not the builder.
10. **`isChampion?: boolean` added (optional)** to `RankingFighter` — the component uses it; optional
    to avoid breaking existing construction sites.
11. **Removed dead `themeIndex` export** in `theme/motion.ts` — referenced non-existent names,
    had zero consumers.
12. **All new mobile files are minimal shims** (`NetworkAnalytics.ts`, `globals.d.ts`,
    `bootstrap/README.md`) — matching existing codebase conventions, no comments added.

---

## 10. Files Created (this session)

| File | Purpose |
|---|---|
| `mobile/app/networking/NetworkAnalytics.ts` | Re-exports `NetworkAnalytics`/`networkAnalytics` from `NetworkLogger.ts` (fixes 2 TS2307) |
| `mobile/globals.d.ts` | `declare module '*.md'` — enables `export { default as BootstrapDocs } from './README.md'` |
| `mobile/app/bootstrap/README.md` | Bootstrap platform docs (imported by `bootstrap/index.ts`) |
| `recommendation/requirements.txt` | `numpy>=1.24` — the only external dep the package imports (created earlier in session) |

(`mobile/package-lock.json` regenerated by npm install; `mobile/node_modules` updated.)

---

## 11. Files Modified (this session — mobile Phase 4)

All under `mobile/` unless noted:

- `app/auth/Authorization.ts` — React import, PERMISSIONS cast, createElement cast
- `app/analytics/AnalyticsHooks.ts` — funnel cleanup void return
- `app/bootstrap/BootstrapState.ts` — static BootstrapError import (removed top-level await)
- `app/deeplinks/DeeplinkManager.ts` — `export class RouteRegistry`
- `app/networking/Interceptors.ts` — static RateLimitError/APIError imports
- `app/networking/OfflineQueue.ts` — removed dead NetworkError import
- `app/offline/OfflineConfig.ts` — `MAX_QUEUE_SIZE: 500`
- `app/session/SessionDevice.ts` — import sessionManager
- `app/storage/StorageManager.ts` — re-export storageLogger
- `design-system/animations/animationLib.ts` — `../tokens` import path
- `design-system/hooks/index.ts` — Dimensions from react-native
- `design-system/images/index.tsx` — AvatarImage/PosterImage aliases
- `design-system/theme/ThemeBuilder.ts` — `: Theme['palette']` return annotation
- `design-system/theme/ThemeTypes.ts` — ThemeContextValue; surface/text union
- `design-system/tokens/extended.ts` — `./colors` import path
- `features/events/hooks/useWatchlist.ts` — mutation variable typing (string)
- `features/events/screens/EventDetailScreen.tsx` — `(fightId: string)`
- `features/events/stories/EventCard.stories.tsx` — mockEvent `as any`
- `features/events/types.ts` — `FightCardEntry extends Omit<BaseFight, 'result'|'status'|'cardSegment'>`
- `features/fighters/index.ts` — legacy hook re-exports
- `features/fighters/screens/index.tsx` — useFightersStore from '../store'
- `features/rankings/navigation/RankingsStack.tsx` — real screens wired
- `features/rankings/screens/index.tsx` — import useTitleDefenses
- `features/rankings/types.ts` — `isChampion?: boolean`
- `features/search/SearchModule.tsx` — infinite query + `(autoData ?? [])`
- `features/search/types-and-api.ts` — infinite query
- `hooks/index.ts` — correct feature hook names
- `hooks/usePerformance.ts` — React import
- `package.json` + `package-lock.json` — 3 new deps
- `release/ReleaseStores.ts` — 1-arg logger call
- `release/index.ts` — `export type { ReleaseConfig }` split
- `security/SecurityHooks.ts` — type/value export split
- `theme/motion.ts` — removed dead themeIndex

Earlier in the session (restoration fixes, root-level): `prediction/__init__.py`,
`prediction/models/finish_predictor.py`, `intelligence/analytics/age_curves.py`,
`intelligence/analytics/momentum.py`, `intelligence/embeddings/matchup_embedder.py`,
`intelligence/tests/test_all.py`, `data_platform/identity/__init__.py`, `data_platform/trust/__init__.py`,
`data_platform/hardening.py`, `data_platform/verify.py`, `data_platform/integration.py`,
`mobile/features/predictions/types.ts`, `mobile/features/predictions/api/index.ts`,
`mobile/features/predictions/components/PredictionsComponents.tsx`,
`mobile/features/predictions/screens/PredictionsScreen.tsx`.
Pre-existing uncommitted backend modifications (NOT this session's work, do not revert):
`backend/pyproject.toml`, `backend/src/api/cache.py`, `backend/src/api/v1/events.py`,
`backend/src/api/v1/fighters.py`, `backend/src/api/v1/fights.py`, `backend/src/api/v1/other.py`,
`backend/tests/unit/test_etag.py`.

---

## 12. Files Restored

- **161 files in 7 AI areas**, restored from `ff74cd8` via `git restore .`:
  `prediction/` (20), `recommendation/` (28), `intelligence/` (58),
  `platform/` (19 — subsequently renamed to `data_platform/`), `mobile/features/predictions/` (18),
  `mobile/features/recommendations/` (9), `mobile/intelligence/` (9).
- **Why**: the user's directive superseded the deletion instructions in `01-instruction-index.md`
  (F6/P1/ZV3–5, Delete table L176–182) and `04-migration-plan.md` (Phase 5 row). Every file exists
  in V10 history; the "restoration" was a working-tree recovery, validated against V9 as the
  historical reference.
- **Renamed (19 files, `git mv`, history preserved)**: `platform/*` → `data_platform/*`, with all
  35 internal `from platform.` imports rewritten to `from data_platform.`.
- **Intentionally NOT restored**: the two orphan/dead prediction screen duplicates (Section 5) —
  verified dead: no imports, broken content, superseded by `PredictionsScreen.tsx`.

---

## 13. Validation Record

| Gate | Command / context | Result |
|---|---|---|
| prediction self-check | `$env:PYTHONPATH=root; python prediction/verify.py` | 10/10 assertions pass |
| recommendation self-check | `python recommendation/verify.py` | 10/10 assertions pass |
| intelligence self-check | `python intelligence/verify.py` | 6/6 assertions pass |
| intelligence tests | `python -m pytest intelligence/tests/test_all.py` | 31 passed |
| data_platform self-check | `python data_platform/verify.py` | ALL 45 ASSERTIONS PASS (Phase 19.1–19.12 Complete) |
| backend pytest | `python -m pytest` (backend) | **339 passed** (332 + 7 event-extras; baseline 319) |
| backend ruff | `ruff check` | All checks passed |
| backend mypy | `mypy` | Success: no issues in 184 source files |
| contract audit | `api_audit.py <repo>` (venv python) | **100 endpoints / PHANTOM_COUNT 0** (was 39) |
| Python compile scan | `python -m compileall` on edited packages | passes |
| Backend import scan | grep for `from platform.` / `import platform` | zero references (post-rename) |
| Mobile tsc | `mobile> .\node_modules\.bin\tsc.cmd --noEmit` | **0 errors** (re-run after round-2 cleanup) |
| expo export | `mobile> npx expo export` | PASSED — web/android/iOS bundles (re-run after round 2) |
| npm install | `npm install @tanstack/query-async-storage-persister @tanstack/react-query-persist-client @hookform/resolvers` | 3 packages installed |
| V9↔V10 diff | CRLF-normalized, relative-path-keyed per AI area | File sets identical; 13 content diffs, V10 correct in all |

---

## 14. Next Session Plan

### Where to begin
1. Confirm state: `git status --short` (expect many modified + deleted files from the
   contract-diff cleanup, rounds 1–2), `git log --oneline -3` (HEAD `af731e1`).
2. The Phase 7 item 5 audit is COMPLETE (both rounds) and the final report was presented.
   The user's next action: review the report and approve the ONE final commit
   (exclude `session-ses_0327.md` and `mobile/dist/`).
3. Read `migration-2026-08-03/04-migration-plan.md` (Phase 7 section) and
   `backend/PROJECT_STATUS.md` (already updated through round 2) before editing them.

### What NOT to repeat
- Do **not** re-run the restoration or V9 diff (complete, recorded in Section 5).
- Do **not** re-install npm deps (already in `package.json`/`node_modules`).
- Do **not** touch `data_platform/` internals, prediction/recommendation/intelligence modules, or the
  rename — all done and verified.
- Do **not** re-apply any deletion instructions found in `01-instruction-index.md` — superseded.
- Do **not** re-run the API audit or expo export just to verify (both green; `expo export`
  regenerates `dist/`).
- Do **not** commit unless the user asks.

### What to verify first
- `mobile> .\node_modules\.bin\tsc.cmd --noEmit` → expect 0 errors (last run post-round-2: 0).
- Backend gates if anything backend-adjacent changes: pytest (339), ruff, mypy (Section 1 commands).
- `git status` for any accidental new files.

### What to implement next (in order)
1. **Await user review of the final Phase 7 item 5 report**, then create the ONE final commit
   (all Phase 7 item 5 rounds 1–2 work; exclude `session-ses_0327.md` + `mobile/dist/`; message
   matching repo style, e.g. "Phase 7 item 5: contract cleanup + event endpoints + phantom removal").
2. **Live-Postgres verification** when a DB is available (alembic upgrade head, sync, smoke tests).
3. Optional backlog: recommendations re-surface in UI, GPU fallback, Xcode Previews.

### What to avoid changing
- `backend/` — pre-existing committed state is green (319 tests); no pending backend work except
  phantom-path decisions that require backend changes (with user sign-off).
- The `as any`/cast sites in mobile — deliberate minimal fixes; refactor only on request.
- `mobile/node_modules` and `package-lock.json` — keep as installed.

---

## 15. Final Notes

- **User interaction style**: concise, direct; no emojis; don't over-explain. Only commit/push when
  explicitly asked. The user works through a long-running "plan" (Phase 4 → Phase 7 → final commit)
  with an instruction-index doc (`01-instruction-index.md`) as the source of task lists — but user
  directives always supersede the docs.
- **Engineering standards in this repo** (enforced by the user): strict layering, dependency
  injection, no scope-betting, backend gates (pytest/ruff/mypy/alembic) must stay green.
- **Commands that work** (PowerShell 5.1; use `workdir` param, never `cd`):
  - Mobile typecheck: workdir `mobile`, `& ".\node_modules\.bin\tsc.cmd" --noEmit`
  - AI self-check: workdir repo root, with
    `$env:PYTHONPATH = (Get-Location).Path; $env:PYTHONIOENCODING='utf-8'`,
    then `& "C:\Users\-\AppData\Local\Temp\opencode\mma-venv\Scripts\python.exe" <pkg>\verify.py`
  - Backend tests: `& "<venv python>" -m pytest` from `backend/`
- **Historical V9 reference** (read-only, for comparison only): `C:\Users\-\Downloads\from-github (1)\from-github\mma-app-zaro-ai-repo`.
- **Venv python**: `C:\Users\-\AppData\Local\Temp\opencode\mma-venv\Scripts\python.exe`
  (temp dir `C:\Users\-\AppData\Local\Temp\opencode` is pre-approved for scratch work).
- **Do not add code comments unless asked** (repo convention).
- If the user says "continue" with no other context, proceed down Section 7's remaining work
  (docs update → ask about commit).
