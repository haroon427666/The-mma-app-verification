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
  Commits: `9e666a1` (Initial upload) → `ff74cd8` (Recovery checkpoint — current HEAD).
- **Current milestone**: V10 AI-module restoration **complete and verified**; mobile Phase 4
  bootability **complete** (TypeScript typecheck = 0 errors). Remaining: final verification docs
  update + final commit.
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
| Phase 7 verification + docs update | ⏳ Pending | `04-migration-plan.md` Phase 5 row superseded; `PROJECT_STATUS.md` update |
| Final commit | ⏳ Pending | ~80 files uncommitted; user must request the commit |

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

- **Git**: branch `main`; HEAD = `ff74cd8`. Working tree has **~80 uncommitted changes**
  (76 status entries + 3 new mobile files), including: backend fixes from earlier work,
  `platform/`→`data_platform/` renames (19 files, `git mv` — history preserved), intelligence fixes,
  prediction fixes, and all mobile Phase 4 fixes + `package.json`/`package-lock.json`.
- **Backend**: pytest **319 passed**; ruff **All checks passed**; mypy **Success: no issues found in 184 source files**
  (verified earlier in this session, before the mobile work; nothing backend-adjacent changed since).
- **Mobile TypeScript**: `tsc --noEmit` = **0 errors** (was 67 at session start).
- **AI packages**: prediction 10/10, recommendation 10/10, intelligence 6/6, data_platform 45/45 assertions;
  intelligence tests 31 passed.
- **Build status**: no full Metro/iOS/Android build has been run this session (typecheck-level only).
  `react-native-mmkv` is optional (try/catch import in QueryProvider).
- **Untracked files**: `mobile/app/networking/NetworkAnalytics.ts`, `mobile/globals.d.ts`,
  `recommendation/requirements.txt` (new, numpy>=1.24 — the only external dep the package imports),
  and a pre-existing stray `session-ses_0327.md` at root (not ours — do not commit without asking).

---

## 7. Remaining Work (execution order)

1. **[HIGH] Re-verify mobile typecheck**: `& ".\node_modules\.bin\tsc.cmd" --noEmit` from `mobile/` → expect 0.
2. **[HIGH] Phase 7 verification + docs**: update `04-migration-plan.md` (mark the Phase 5
   deletion row as superseded by the restoration directive; add Phase 5-restoration status),
   update `PROJECT_STATUS.md` (mobile tsc 0, restoration complete, data_platform rename),
   and `01-instruction-index.md` only if it still instructs deletions (it is superseded — annotate).
3. **[HIGH] Final commit** (ONLY when the user explicitly asks): stage the ~80 files; verify
   `git status` has no secrets/venv junk; write a message summarizing: restoration + validation,
   data_platform rename, mobile bootability (tsc 0), new deps. Decide with the user whether to
   include `recommendation/requirements.txt` (yes — package completeness) and `session-ses_0327.md`
   (no — stray).
4. **[MEDIUM, backlog] Feature-layer consolidation** in mobile `features/predictions` +
   `features/recommendations` (parallel hooks/repository/stores vs consolidated api) — do NOT do
   this without explicit user request.
5. **[LOW, backlog] Verify GPU fallback path** (onnxruntime) and Xcode Previews safety.

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
| backend pytest | `python -m pytest` (backend) | 319 passed |
| backend ruff | `ruff check` | All checks passed |
| backend mypy | `mypy` | Success: no issues in 184 source files |
| Python compile scan | `python -m compileall` on edited packages | passes |
| Backend import scan | grep for `from platform.` / `import platform` | zero references (post-rename) |
| Mobile tsc | `mobile> .\node_modules\.bin\tsc.cmd --noEmit` | **0 errors** (was 67 at session start) |
| npm install | `npm install @tanstack/query-async-storage-persister @tanstack/react-query-persist-client @hookform/resolvers` | 3 packages installed |
| V9↔V10 diff | CRLF-normalized, relative-path-keyed per AI area | File sets identical; 13 content diffs, V10 correct in all |

---

## 14. Next Session Plan

### Where to begin
1. Confirm state: `git status --short` (expect ~80 entries), `git log --oneline -3` (HEAD `ff74cd8`).
2. Confirm the goal with the user: Phase 7 docs update + final commit are the remaining plan items.
3. Read `docs/04-migration-plan.md` and `PROJECT_STATUS.md` before editing them.

### What NOT to repeat
- Do **not** re-run the restoration or V9 diff (complete, recorded in Section 5).
- Do **not** re-install npm deps (already in `package.json`/`node_modules`).
- Do **not** touch `data_platform/` internals, prediction/recommendation/intelligence modules, or the
  rename — all done and verified.
- Do **not** re-apply any deletion instructions found in `01-instruction-index.md` — superseded.
- Do **not** commit unless the user asks.

### What to verify first
- `mobile> .\node_modules\.bin\tsc.cmd --noEmit` → expect 0 errors.
- Backend gates if anything backend-adjacent changes: pytest, ruff, mypy (commands/venv in Section 1).
- `git status` for any accidental new files.

### What to implement next (in order)
1. **Docs update (Phase 7 verification)**:
   - `04-migration-plan.md`: supersede/annotate the Phase 5 deletion row; add restoration status
     (161 files restored from checkpoint, 11 fixed, 2 deleted as duplicates, rename done).
   - `PROJECT_STATUS.md`: mobile bootability (tsc 0), restoration complete, gates green.
   - `01-instruction-index.md`: only annotate the superseded deletion references — do not delete content.
2. **Final commit** (on request): `git add` everything except `session-ses_0327.md` (ask user);
   commit message style matches the repo (see `git log`); include summary of restoration +
   bootability + rename + new deps. Push only if requested.

### What to avoid changing
- `backend/` — the pre-existing uncommitted modifications are another thread of work (migration
  002/004/005); leave them, they're verified green.
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
