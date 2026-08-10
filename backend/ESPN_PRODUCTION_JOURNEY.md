# ESPN Production Journey — A to Z

**Status:** COMPLETE through Window 002 (verified) — see Decision Gate for next steps
**Date:** 2026-08-10
**Scope:** end-to-end record of the ESPN MMA production integration: research → code → acceptance → windowed production runs → coverage findings → decision gate

---

## 1. Context

This application's backend integrates the ESPN MMA API (`sports.core.api.espn.com/v2/sports/mma`) as its primary data provider. The journey below reconstructs everything that happened to date, so anyone (or any agent) can resume work without re-reading the entire research tree.

## 2. Frozen Research Phase (read-only, preserved)

Location: `C:\Users\-\Desktop\zip for xhatgpt\espn endpoint checks\` (frozen; do NOT modify)

- Start here: `espn_endpoint_discovery\START_HERE.md`
- Census: **38,014 unique athlete IDs** (38,006 flat listing verified + 8 hard-400s)
- Classification: 2,763 confirmed MMA, 33,352 MMA-likely, 1,845 uncertain, 45 combat-other, 8 invalid, 1 stub
- ~49 leagues; UFC roster ≈ 1,835–1,840 athletes; "other league" ≈ 27,286 IDs
- 96 endpoint families (75 confirmed live), 10 P0 surfaces
- Discovery sources ledger: flat listing 38,006 (2,347 new), league rosters 35,652 (31,076 new), hidden_profiles 3,802, reference_graph, search_api, events_competitors, rankings 109 (0 new at the time — the ONLY path to Demetrious Johnson in early phase)
- ONE Championship league slug is `ofc`
- Rate envelope: 2–5 rps; workers 4–8; page-based pagination 1-indexed, max page size 1000
- Historical data path: rankings → winningFight → events → competitions → competitors + eventlogs

## 3. Integration Code Phase (committed)

Commits (all in place, nothing further committed by this session):
- `cda302c` — "feat(espn): complete validated ESPN MMA integration" (client, provider, jobs, upserts, migration `006_statistics_career`, API surface)
- `56221cc` — "docs(espn): preserve integration acceptance evidence" (evidence package under `backend/docs/espn_validation/`)
- HEAD = `56221cc` on branch `main`, up to date with `origin/main`

### Key code mechanics (verified by reading + live probing)

| Component | Behavior |
|---|---|
| `ESPNProvider.fetch_athlete_ids()` | Union of global `/athletes` flat listing (limit 1000/page) + 6 league rosters (ufc, bellator, pfl, ksw, ifc, ofc) |
| `FighterSyncJob` | `ids = sorted(discovered)` (strings; all 7-digit → numeric order equivalent); window = `ids[start : start+limit]`, `start = state.last_offset` (always 0 on fresh CLI process) |
| `ESPN_FIGHTER_SYNC_LIMIT` | Default 1000 in production. The ONLY coverage knob available without code change |
| Sync state | `MemorySyncStateStore` only — per-process; `DatabaseSyncStateStore`/`RedisSyncStateStore` exist as scaffolding but are NOT wired to the CLI/scheduler |
| `sync_checkpoints` | Table exists (0 rows) + `CheckpointManager` implemented but not wired |
| `statistics` job | Samples up to `ESPN_STATS_MAX_FIGHTERS` (default 200) fighters from DB |
| `historical_event` | Does NOT inject ranked athlete IDs into fighter discovery; follows rankings → winningFight → events → competitions → competitors; skips fighters not synced |
| `ranking` job | Per-promotion fetch for ALL synced promotions; REPLACE strategy per (promotion, category): delete + insert in one transaction |
| Upserts | Idempotent via `(provider, external_id)` unique constraints; no duplicates/orphans ever observed |
| Pagination | `MAX_PAGINATION_PAGES=200` default; `limit=1000` honored → 38k listing ≈ 39 pages, no truncation |

## 4. Validation Phase (pre-production, evidence package)

`backend/docs/espn_validation/README.md`, `ACCEPTANCE_EVIDENCE.md`, `VERIFICATION.md`, `VALIDATION_RESULTS.json`, `PRODUCTION_DB_PREFLIGHT.md`, `CHECKSUM_MANIFEST.json`, `VALIDATION_FILE_MAP.md`, `VALIDATION_TIMELINE.md`
Plus: `backend/ESPN_INTEGRATION_PLAN.md`, `ESPN_ENDPOINT_CATALOG.md`, `ESPN_INTEGRATION_REPORT.md`, `ESPN_PRODUCTION_VALIDATION_REPORT.md`
Tests: `backend/tests/unit/test_espn_pagination.py`, `test_espn_discovery.py`, `backend/tests/integration/test_espn_records_and_stats.py`, `test_espn_live_probes.py`

## 5. Production Run History (DB `mma` @ localhost:5432)

| Run | Window | Mode | Result | Duration | Inserted | Updated | Skipped | Errors |
|---|---|---|---|---|---|---|---|---|
| accd73ad (23:58) | baseline 200 | auto | COMPLETED | 141,246 ms | 384 | 0 | 142 | 0 |
| 5e400b2a (00:00) | LIMIT=200 rerun | auto | COMPLETED | 5,253 ms | 4 | 100 | 422 | 0 |
| eb70f094 (15:58) | **Window 001** LIMIT=1000 | auto | COMPLETED | 820,613 ms | 2,369 | 90 | 729 | 0 |
| b86436ab (16:49) | **Window 002** LIMIT=2000 | auto | COMPLETED | 1,473,903 ms | 2,060 | 988 | 2,008 | 0 |
| 0c8c2567 (17:30) | **Window 002 rerun** LIMIT=2000 | auto | COMPLETED | 1,474,152 ms | 18 | 1,598 | 3,440 | 0 |

No HTTP 429s, no retries, no dead letters, no provider conflicts in any run.

### Window 001 (bounded first window, evidence: `PRODUCTION_WINDOW_001_*`)

- `ESPN_FIGHTER_SYNC_LIMIT=1000`, `ESPN_EVENTLOG_ENABLED=0`
- Synced external IDs 2,085,811 – 2,488,768 (sorted union positions 0–999)
- DB: fighters 0→1000, fighter_records 999, statistics 368, events 24, competitions 260, competitors 35, rankings 12, promotions 48, broadcasts 3, weight_classes 17, external_ids 1349
- Key discovery: representative IDs are NOT current champions — they are ESPN's stale (2022-era) P4P/ranked lists: Usman, Adesanya, Ngannou, Volkanovski, Blachowicz, Poirier, Figueiredo, Miocic, Oliveira, Jones, DJ, Rousey, Gracie, Shamrock, etc.

### Window 002 (this session)

- Design: `ESPN_FIGHTER_SYNC_LIMIT=2000` (only supported way to advance coverage), `ESPN_EVENTLOG_ENABLED=0`
- Live discovery probe (read-only): union = **38,011** ids (census 38,014; drift −3), min 2,085,811, max 5,395,233
- New band (positions 1000–1999) = external IDs **2,488,769 – 2,502,283** — all inactive/obscure athletes (sample verified live: Charlie West, Eduardo Maiorino, Norifumi Yamamoto, ...)
- Representative positions (0-indexed): Jones 85, Shamrock 99, GSP 105, Gracie 143, Frank Shamrock 754 (all already in W001); Oliveira 2167, Miocic 2296, Blachowicz 2345, Poirier 2363, Cormier 2380, **Demetrious Johnson 2480** (now in union via PFL roster), Nunes 2608, Rousey 4780, Khabib 5321, McGregor 7735, Cejudo 7760, Usman 10623, Ngannou 15820, Volkanovski 16094, Figueiredo 18846, Adesanya 20451
- Results: +1000 fighters (→2000), +999 fighter_records (→1998), +31 statistics (→399), +12 competitors (→47), +5 rankings (→17), +1 weight_class (→18, "Super Heavyweight" auto-created by fighter parser), +1001 external_ids (→2350), 0 errors
- Representative test: all 33 probed profiles live (HTTP 200), DB↔ESPN name match perfect for synced reps (Jones, GSP, Shamrock, Gracie, Frank Shamrock)

### Window 002 rerun (idempotency proof)

- `ESPN_FIGHTER_SYNC_LIMIT=2000` again → **0 fighter inserts**, 1,598 updates, 0 errors
- rankings stable at 17 rows (the `ranking inserted=18` counter is a pipeline nuance: one `add()` in the batch is deduplicated at flush; table unchanged, no duplicates, no accumulation)

## 6. Coverage Findings (the core problem)

1. **Every fresh CLI run restarts at the same sorted prefix** — no persisted offset, so repeated runs with the same LIMIT re-sync the same IDs (idempotent but wasteful).
2. **Coverage only advances by raising `ESPN_FIGHTER_SYNC_LIMIT`** — each step re-processes the whole prefix, so naive incremental windows cost O(n²) API calls (1000 + 2000 + ... + n·1000).
3. **The listing drifts between runs** (38,014 → 38,011) — window membership shifts slightly; upsert semantics absorb it safely.
4. **Ranked/current fighters cannot be prioritized without a code change**: the 150 ranking DTOs ESPN currently serves (ufc 133, bellator 7, ifc 10) resolve into the DB only for fighters already synced (17 rows / 13 fighters today). The ranking job cannot pull fighters into sync.
5. **Reaching top fighters costs**: Adesanya sits at sorted position 20,451 → `ESPN_FIGHTER_SYNC_LIMIT=21000` would need ≈ 21k profile fetches (≈ 35–45 min at production rate limits), after which most high-profile MMA fighters would be present. This is possible WITHOUT a code change but is far beyond "one next safe window".
6. **Full 38k census sync** requires DB-backed checkpoint wiring (code change) to be resumable/safe.

## 7. Decision Gate (Phase 10)

Classification of the production state after Window 002:

| Option | Description | Verdict |
|---|---|---|
| **A. Windowed expansion (status quo)** | Keep running bounded LIMIT increments (3000, 4000, ...) | SAFE but O(n²) API cost; each window ≈ 25 min; ~0 famous fighters until LIMIT ≈ 2200+ |
| **B. One long bounded run (no code change)** | `ESPN_FIGHTER_SYNC_LIMIT=21000` in a single run (~35–45 min, ~1.5× current run) | Reaches every representative fighter listed above; still bounded; needs approval (it is a bigger blast radius than "one window") |
| **C. Code change: DB-backed fighter checkpoint + offset** | Wire `sync_checkpoints` + `CheckpointManager` so runs resume from last offset | Required before any FULL census execution; unlocks efficient increments; requires code change + review/approval |
| **D. Code change: ranking→fighter discovery injection** | Inject ranked athlete IDs into the fighter window so champions/ranked fighters sync first | Most valuable for app UX (champions, top-15s); requires code change + approval |
| **E. Stop production sync** | Halt further ESPN syncing | No data-safety reason to stop; all runs are idempotent and verified |

**This session's gate result: Window 002 = COMPLETE + VERIFIED (0 errors, idempotency proven). Next step is a decision between A/B (continue without code change) or C/D (code change — requires explicit approval). No code was changed in this session; nothing was committed; frozen research untouched.**

## 8. Current DB State (after Window 002 + rerun)

fighters 2000 · fighter_records 1998 · statistics 399 · events 24 · competitions 260 · competitors 47 · rankings 17 · promotions 48 · venues 0 · broadcasts 3 · weight_classes 18 · sync_runs 5 · sync_jobs 50 · sync_checkpoints 0 · external_ids 2350 · users 0
alembic_version = 006 · 0 duplicates · 0 orphans · 0 null violations · fighter external_id range 2,085,811 – 2,502,283

## 9. Artifacts (this session, all under `backend/docs/espn_validation/` unless noted)

- `PRODUCTION_WINDOW_002_PREFLIGHT.json` (baseline, read-only)
- `PRODUCTION_WINDOW_002_DISCOVERY_PROBE.json` (live union census + target positions)
- `PRODUCTION_WINDOW_002_COVERAGE_ANALYSIS.md` (Q1–Q11 analysis)
- `PRODUCTION_WINDOW_002_REPRESENTATIVE_TEST.json` (33 live profile probes + DB↔ESPN match)
- `PRODUCTION_WINDOW_002_RANKING_VERIFY.json` (live ranking DTO census: 150 dtos)
- `PRODUCTION_WINDOW_002_AFTER.json` (post-run audit, read-only)
- `PRODUCTION_WINDOW_002_SYNC_LOG.txt` (window run log)
- `PRODUCTION_WINDOW_002_RERUN_SYNC_LOG.txt` (idempotency run log)
- `PRODUCTION_WINDOW_002_REPORT.md` (window report, next file)
- `ESPN_PRODUCTION_JOURNEY.md` (this file, at `backend/` root)

## 10. Environment Notes (for future sessions)

- Project root: `C:\Users\-\Downloads\mma-app-zaro-ai-repo\from-github\mma-app-zaro-ai-repo`
- Sync runs: run from `backend/` workdir: `python sync.py --full` (venv at `C:\Users\-\AppData\Local\Temp\opencode\mma-venv\Scripts\python.exe`)
- Env: `PYTHONIOENCODING=utf-8`, `ESPN_FIGHTER_SYNC_LIMIT=2000`, `ESPN_EVENTLOG_ENABLED=0`; tee logs to absolute paths; `Select-Object -Last 40` for tail
- DB: localhost:5432/mma (mma/mma); read-only sessions for audits (Python312 + psycopg2)
- PowerShell 5.1: avoid inline python with quotes/`*`; use temp scripts in `C:\Users\-\AppData\Local\Temp\opencode\`
- Production bounds exercised: fighters 2000, eventlog disabled, stats sample 200, everything else default
- Boundaries respected: no commits, no pushes, no mobile changes, no frozen-research edits, no unbounded 38k run, no code changes (any code change → stop and ask)

---

## 11. Session Record — 2026-08-10 (Reconstruction + C/D Diagnostic Review)

- **Date/time:** 2026-08-10 (evening); agent: reconstruction pass (read-only) + diagnostic review.
- **Objective:** (1) full project reconstruction per handoff brief (git / docs / frozen research / code / validation / DB / windows); (2) diagnose the uncommitted C/D work (discovery registry + resume + ranking injection) with **no DB changes, no migration, no sync, no commit, no rollback**.
- **Files inspected:** PROJECT_STATE / SESSION_STATE / EXECUTION_PLAN / PLAN_HISTORY; all `backend/ESPN_*` reports; `docs/espn_validation/*` (evidence package + all PRODUCTION_WINDOW_001/002 + preflight + design + implementation map); `src/providers/espn/{client,provider,config,discovery}.py` + `jobs/{fighter,ranking,historical_event}.py` + `parsers/eventlog.py`; `src/sync/{engine,pipeline,state,state_store,checkpoints,upserts/competition,upserts/id_resolver}.py`; `src/db/models/support.py`; `alembic/versions/007_discovery_registry.py`; `sync.py`; 3 new test files; frozen research (`START_HERE`, `FROZEN`, `RESEARCH_ARCHIVE`, `FINAL_NUMBERS`, `FINAL_RESEARCH_STATUS`, `MASTER_REPORT`, `KNOWN_LIMITATIONS`, `HIDDEN_DATA_GUIDE`, `RECONCILIATION.json`, `DISCOVERY_SOURCES_FINAL.json`, research `PROJECT_STATE`/`CONTINUATION_HANDOFF`/`NEXT_STEPS`).
- **Commands executed (all read-only):** `git status/branch/log/show/diff`; read-only asyncpg audits of `localhost:5432/mma` (counts, alembic, sync_runs, dupes, orphans); `pytest tests/` (full); `ruff` + `mypy` on modified/new files; SQLAlchemy render experiment for the SQLite `ON CONFLICT` behavior.
- **DB state before/after:** unchanged (read-only). alembic 006; counts per `ESPN_HANDOFF_STATE.md` §2; sync_checkpoints still 0 rows; registry tables still absent.
- **Git state before/after:** unchanged — HEAD `56221cc` on `main`; working tree untouched. Two docs added: `ESPN_HANDOFF_STATE.md` (new) + this entry.
- **Findings (evidence-backed):**
  1. Existing committed suite still green: **460 passed + 2 skipped** today.
  2. New C/D tests: **18 FAILED / 5 passed** → the C/D implementation is **unvalidated**.
  3. Failure class A — SQLite portability (not production bugs): (a) `sync_discovered_athletes.id` `BigInteger` PK has no autoincrement on SQLite (`NOT NULL constraint failed: sync_discovered_athletes.id`); (b) `on_conflict_do_update(constraint="<name>")` in `CheckpointManager.save` / `DiscoveryCheckpointManager.save` renders `ON CONFLICT ON CONSTRAINT` on Postgres but SQLite **silently drops the conflict target** (render-verified) → duplicate rows → `MultipleResultsFound`.
  4. Failure class B — **real production bugs**: missing `await` on `register_ids(...)` at `competition.py:134` and `historical_event.py:126` (mypy `unused-coroutine`; registration silently never executes); `_sync_limit()` default is `0` = **unbounded** (journey §3's "default 1000" is inaccurate).
  5. Failure class C — ruff: 6 import-organization errors in the 3 new test files (all `--fix`-able).
  6. Architecture: registry + resumable walks + unconsumed-filter window + consumed flags is **correct in principle** (matches design D1–D7); healthy-dead-end metric keys verified present; ranking injection correctly awaited in `ranking.py`; `DatabaseSyncStateStore` roundtrip correct.
  7. **Migration 007 is required if C/D is kept** (registry tables + `sync_checkpoints.data`); running `sync.py --full` with the current tree against the 006 DB would crash the fighter job. 007 backfills the 2,000 synced fighters as consumed.
- **Tests:** full suite run (480 total: 460 pass + 2 skip + 18 fail); targeted new-test runs; ruff/mypy on the C/D surface.
- **Decision (user directive):** diagnostic review only — no fixes, no migration 007, no production sync, no commit, no rollback. Next action requires approval.
- **Unresolved / open items:** (1) fix plan awaiting approval (A1/A2/B3 + ruff → tests green → 007 → bounded validation); (2) scheduler path still uses the in-memory state store; (3) `ESPN_HANDOFF_STATE.md` created to preserve this state.
- **Exact next step:** user decides between (recommended) finish C/D (fix + validate + 007 + bounded windows) or roll back C/D and continue windowed runs.

---

## 12. Session Record — 2026-08-10 (C/D Completion: fixes, migration 007, live validation)

- **Date/time:** 2026-08-10 (night); agent: continuation pass per the NEXT-PHASE brief (approved by user: "continue the previous prompt work like the phases").
- **Objective:** complete the C/D implementation (fix defects), apply migration 007, run the bounded live-validation plan (A/B/C + ranking injection), quality gates, DB safety, performance comparison, and phase documentation.
- **Approval:** user directed continuation of the phased brief; no commit/push allowed; frozen research untouched.
- **Code fixes applied (7 defects, all verified):**
  1. `competition.py` / `historical_event.py` — added missing `await` on `register_ids(...)` (relationship refs now actually register).
  2. `support.py` — `SyncDiscoveredAthlete.id` → `BigInteger().with_variant(Integer, "sqlite")` (autoincrement on SQLite).
  3. `checkpoints.py` — `on_conflict_do_update(constraint=...)` → `index_elements=[...]` in both managers (portable to SQLite).
  4. `discovery.py` — `register_ids` now actually invokes `ON CONFLICT DO NOTHING` (dialect-branched: `postgresql.insert(...).on_conflict_do_nothing(constraint=...)` vs SQLite target-less) — previously would have raised `IntegrityError` on Postgres re-registration.
  5. `support.py` — `run_id` (both new tables) + `ExternalId.entity_id` → `UUID(...).with_variant(String(36), "sqlite")` (SQLite NUMERIC-affinity corrupts all-digit UUID hex to REAL float → result-processor crash).
  6. `test_discovery_service.py` — missing `await` on `registry_ids(...)` helper (3 call sites, test bug).
  7. `test_espn_records_and_stats.py::TestDiscoveryFighterJob` — 2 tests rewritten to the registry-driven job contract (old `fetch_athlete_ids`/`state.checkpoint` assertions were obsolete).
- **Quality gates (pre-migration):** `pytest tests/` → **478 passed, 2 skipped** (env-gated live tests skip); `ruff` clean; `mypy` clean (9 files); `alembic heads` → single head `007`.
- **Migration 007 applied** (`alembic upgrade head`): added `sync_checkpoints.data` JSON; created `sync_discovered_athletes` (38k-capable, unique provider+external_id, window index) + `sync_discovery_checkpoints` (unique provider/source/league_slug); backfilled 2,000 existing fighter mappings as `consumed=true, source='backfill'`. Verified: 0 registry dupes, all indexes present, alembic current = 007.
- **Live validation (all bounded; `PYTHONIOENCODING=utf-8` required for the Unicode CLI banner):**
  - **Run A (LIMIT=30, kill mid-walk):** killed at 12s while walking global listing page 18 → checkpoint `global_listing page=18 IN_PROGRESS`; registry 18,000 (16k new + 2k backfill). **Resume walked from page 19** (log proof, no page-1 restart); walk COMPLETED: global 39 pages / 38,011 ids + 6 rosters; window 30 resolved; fighters 2000 → 2030.
  - **Run B (LIMIT=30, idempotent):** **0 discovery walk requests** (all 7 sources "already completed — skipped"); window advanced to next 30; fighters → 2060; 0 errors.
  - **Run C (LIMIT=200, kill mid-window):** killed at 30s mid-fetch (90/200 requests, 0 upserted — crash-safe, no partial consumption); resume: 200 resolved, inserted 400, 0 errors; fighters → 2285.
  - **Ranking injection (`--rankings`):** 25 unsynced ranked fighters of 109 referenced injected (upserted 50 fighter rows, 25 registry ids consumed `source='rankings'`); 59 ranking rows inserted; **ranking resolution 56/56** (was ~17). Deep-ID ranked fighters (Makhachev 2579938) need a larger `ESPN_RANKING_INJECTION_LIMIT` (e.g. 110) — expected bounded behavior.
  - **Representative inspection:** DJ (2512089) IS in the registry via global_listing (partially falsifies the "hidden" research claim for DJ); Rousey (245), Gracie (16594), Shamrock (16335), Ngannou (2579646), Makhachev (2579938) absent from the listing — true hidden profiles reachable only via injection (confirms the ordering problem being solved; window at ~ID 2.5M).
- **DB after (vs before):** fighters 2285 (was 2000) · fighter_records 2283 (1998) · external_ids 2635 (2350) · rankings 56 (17) · registry 38,011 (new) · discovery checkpoints 7 (new, all COMPLETED) · sync_runs 11 (5).
- **Integrity (post-validation):** 0 duplicate (provider, external_id) in fighters/external_ids/registry; 0 orphaned FKs (fighter_records, statistics, competitors, rankings); 0 NULL provider/external_id; **0 HTTP 429 / 5xx / breaker opens across all run logs** (only "429" hits are UUID substrings). Roster walk ids (4,201 across 6 leagues) converged into existing global rows — cross-source dedup proven.
- **Performance:** census enumeration cost ~45 discovery requests ONCE (Run A); Runs B/C/rankings = 0 discovery requests (vs OLD: full re-enumeration every run). Fighter windows advance by consumed flags — no prefix rescans.
- **Tests after:** 478 passed + 2 skipped (full suite); ruff/mypy clean; new phase doc `PRODUCTION_DISCOVERY_CHECKPOINT_PHASE.md` created; `ESPN_HANDOFF_STATE.md` still accurate (will refresh next session if needed).
- **Git:** no commits, no pushes; working tree contains the C/D implementation + this phase's fixes + docs (all uncommitted per standing rules).
- **Decision gate result: READY_FOR_PRODUCTION_WINDOW** — next step: bounded fighter window (e.g. LIMIT=1000) + one rankings run with `ESPN_RANKING_INJECTION_LIMIT=110`. No unbounded 38k sync. Awaiting approval before the next production window.
