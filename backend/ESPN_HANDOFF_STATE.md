# ESPN HANDOFF STATE — Current State for the Next Agent

> **Generated:** 2026-08-10 (reconstruction + C/D diagnostic review session)
> **Read first:** this file, then `backend/ESPN_PRODUCTION_JOURNEY.md` (A-to-Z), then frozen research `START_HERE.md`.
> **Status of this handoff:** reconstruction COMPLETE; C/D diagnostic review COMPLETE; **no fixes implemented yet (awaiting approval)**.

---

## 1. Git state

| Item | Value |
|---|---|
| HEAD | `56221cc4c53cc568fb4fbbf95df9d1b1c46450b7` `docs(espn): preserve integration acceptance evidence` |
| Branch | `main` — up to date with `origin/main` |
| Accepted integration commit | `cda302c` `feat(espn): complete validated ESPN MMA integration` (HEAD tree == cda302c tree) |
| Staged / pushed | Nothing staged; nothing pushed by any session |
| Uncommitted (backend, C/D work) | `src/providers/espn/discovery.py` (untracked), `jobs/fighter.py`, `jobs/ranking.py`, `jobs/historical_event.py`, `parsers/eventlog.py`, `client.py`, `sync/checkpoints.py`, `sync/state_store.py`, `sync/upserts/competition.py`, `db/models/support.py`, `sync.py` |
| Uncommitted (new files) | `alembic/versions/007_discovery_registry.py`, `tests/unit/test_discovery_service.py`, `tests/unit/test_ranking_injection.py`, `tests/unit/test_state_store_db.py`, all `docs/espn_validation/PRODUCTION_*` artifacts, `PRODUCTION_DISCOVERY_RESUME_DESIGN.md`, `PRODUCTION_DISCOVERY_RESUME_IMPLEMENTATION_MAP.md`, `ESPN_PRODUCTION_JOURNEY.md` |
| Uncommitted (mobile) | ~47 files — **pre-existing T17-era changes, unrelated to ESPN work; do NOT touch without user instruction** |
| Never commit | `session-ses_0327.md` (stray root log); root state docs (`PROJECT_STATE.md` etc.) remain untracked by design |

## 2. Database state (live `localhost:5432/mma`, PostgreSQL 18.4, role `mma`)

**Alembic: `006` — migration `007` NOT applied** (C/D registry tables do NOT exist).

| Table | Count | Table | Count |
|---|---|---|---|
| fighters | 2000 | sync_runs | 5 (all COMPLETED) |
| fighter_records | 1998 | sync_jobs | 50 (all COMPLETED) |
| statistics | 399 | sync_checkpoints | 0 (empty) |
| events | 24 | external_ids | 2350 |
| competitions | 260 | users / payloads / conflicts / dead_letters | 0 |
| competitors | 47 | **sync_discovered_athletes** | **missing (007 unapplied)** |
| rankings | 17 | **sync_discovery_checkpoints** | **missing (007 unapplied)** |
| promotions | 48 | venues | 0 |
| broadcasts | 3 | weight_classes | 18 |

Integrity: **0 duplicates, 0 orphans, 0 NULL violations**. Fighter external_id range: 2,085,811 – 2,502,283.

## 3. Latest sync runs

| Run | When (+05) | Window | Result | Inserted | Updated | Skipped | Errors |
|---|---|---|---|---|---|---|---|
| `accd73ad` | 08-09 23:58 | acceptance 200 | COMPLETED | 384 | 0 | 142 | 0 |
| `5e400b2a` | 08-10 00:00 | acceptance rerun | COMPLETED | 4 | 100 | 422 | 0 |
| `eb70f094` | 08-10 15:58 | **W001** LIMIT=1000 | COMPLETED | 2,369 | 90 | 729 | 0 |
| `b86436ab` | 08-10 16:49 | **W002** LIMIT=2000 | COMPLETED | 2,060 | 988 | 2,008 | 0 |
| `0c8c2567` | 08-10 17:29 | **W002 rerun** | COMPLETED | 18 | 1,598 | 3,440 | 0 |

W002 rerun proved idempotency (0 fighter inserts). 0 HTTP 429s / 0 retries in every run.

## 4. Validation status (today, read-only re-checks)

| Check | Result |
|---|---|
| Existing committed suite | **460 passed + 2 skipped** (was 455+2 at validation close — all existing tests still green) |
| New C/D tests (3 files, 23 tests) | **18 FAILED / 5 passed — the C/D work is UNVALIDATED** |
| ruff (modified + new files) | 6 errors (import-organization in the 3 new test files, all `--fix`-able) |
| mypy (modified + new files) | **2 real errors: missing `await` on `register_ids`** in `competition.py:134` + `historical_event.py:126` |

## 5. C/D diagnostic findings (see journey §11 for the full record)

**A. Test-harness / SQLite portability (16–18 of the failures — NOT production bugs on Postgres):**
1. `sync_discovered_athletes.id` is `BigInteger` PK — no autoincrement on SQLite (`NOT NULL constraint failed: sync_discovered_athletes.id`). Works on Postgres (BIGSERIAL). Fix: `BigInteger().with_variant(Integer, "sqlite")` in `db/models/support.py`.
2. `CheckpointManager.save` / `DiscoveryCheckpointManager.save` use `on_conflict_do_update(constraint="<name>")` — renders `ON CONFLICT ON CONSTRAINT ...` on Postgres (correct), but **SQLite silently drops the conflict target** (verified by render experiment: `ON CONFLICT  DO UPDATE`) → second save inserts a duplicate row → `MultipleResultsFound` on load. Fix: use `index_elements=["entity_type","provider"]` / `["provider","source","league_slug"]` (or dialect branch like `discovery.py._insert`).

**B. Real production-code bugs:**
3. **Missing `await` on `DiscoveryService.register_ids(...)`** at `competition.py:134` and `historical_event.py:126` — the coroutine is created and discarded; relationship-ref registration (source='competition'/'eventlog') **silently never executes** on any dialect. mypy-confirmed (`unused-coroutine`). Ranking injection (`ranking.py:115`) is correctly awaited.
4. `_sync_limit()` default is **0 = unbounded** (`python sync.py --full` with no `ESPN_FIGHTER_SYNC_LIMIT` attempts the full ~38k census ≈ 3.5 h). **`ESPN_PRODUCTION_JOURNEY.md` §3 claims "default 1000" — that is inaccurate**; always pass the env var explicitly for windowed runs.

**C. Architecture assessment (correct in principle):**
- Registry + per-source resumable walks + unconsumed-filter window + consumed flags: sound, matches `PRODUCTION_DISCOVERY_RESUME_DESIGN.md` D1–D7. Ascending order preserved; late relationship-ref arrivals always selected; crash-safe consumption.
- Healthy-dead-end detection in `fighter.py` (breaker CLOSED + zero deltas on `network_errors`/`server_errors_5xx`/`rate_limited_429`) is correct — all three metric keys verified to exist in `client.metrics`.
- Ranking injection: bounded (`ESPN_RANKING_INJECTION_LIMIT` 25), idempotent, real-refs-only — correct.
- `DatabaseSyncStateStore` roundtrip correct; **requires 007** (`sync_checkpoints.data` column).
- Scheduler path still uses the in-memory store (documented open item) — no session passed.

**D. Is migration 007 required?** **YES, if C/D is kept** — the fighter job's registry queries and `DatabaseSyncStateStore` both fail without it (tables / `data` column absent). Running `sync.py --full` with today's working tree against the 006 DB **would crash the fighter job**. 007 also backfills the 2,000 synced fighters as `consumed` so the first post-deploy window advances to new IDs.

## 6. Decision gate (currently OPEN)

- Previous gate (journey §7, options A–E) is superseded: C+D were implemented but left unvalidated.
- **Recommended:** fix items A1/A2/B3 + ruff, get all 480 tests green, THEN (with approval) apply 007 + run the bounded validation plan (kill-resume, idempotency, mid-window kill, ranking injection).
- Alternatives: roll back the C/D working-tree changes (10 files) and continue windowed runs; or review further.
- **NO production sync / migration has been approved yet.**

## 7. Approved next action

**NONE.** Diagnostic review delivered; implementation fixes await explicit user approval.

## 8. Forbidden actions (standing rules)

- No production sync, no unbounded 38k run, no migration apply, no commits/pushes, no rollback without approval.
- No modifications to the frozen research workspace (`C:\Users\-\Desktop\zip for xhatgpt\espn endpoint checks`).
- No changes to mobile files or planning docs.
- No code edits until the fix plan is approved.

## 9. Exact commands for the next agent

```bash
# venv python
PY="/c/Users/-/AppData/Local/Temp/opencode/mma-venv/Scripts/python.exe"
cd "C:/Users/-/Downloads/mma-app-zaro-ai-repo/from-github/mma-app-zaro-ai-repo/backend"

# Gates
"$PY" -m pytest tests/ -q                       # expect 480 total (455+2 existing, 23 new)
"$PY" -m ruff check src tests sync.py           # expect clean
"$PY" -m mypy src sync.py                       # expect 0 errors

# Read-only DB audit (asyncpg in venv)
"$PY" -c "import asyncpg,asyncio; \
async def m():\
 c=await asyncpg.connect('postgresql://mma:mma@localhost:5432/mma');\
 print(await c.fetchval('select version_num from alembic_version'));\
 await c.close()\
;asyncio.run(m())"

# Approved bounded sync (only after approval + migration)
ESPN_FIGHTER_SYNC_LIMIT=1000 ESPN_EVENTLOG_ENABLED=0 PYTHONIOENCODING=utf-8 "$PY" sync.py --full
```

## 10. Known risks

1. **Rousey ID collision** (2563797 = "Alexis"; research-documented Fedor 2335301 → Frank Mir) — identity is external-ID-only, never name-matched.
2. **`ESPN_FIGHTER_SYNC_LIMIT` default 0 = unbounded** — always set it explicitly (journey doc's "default 1000" is wrong).
3. Migration 007 unapplied — C/D code cannot run against the current DB.
4. Cross-promotion historical attribution = first-ref-scope (deterministic, e.g. Bellator 214 → ufc).
5. 38,014 census ≠ 38,014 fighters (`other` league ~27,286 unresolved; 2,763 confirmed MMA).
6. Census not proven exhaustive; listing drifts between runs (38,014 → 38,011 observed).
7. Rankings are current-only and 2022-era stale upstream; ranking job cannot pull fighters into sync without injection (which C/D adds).
8. Naive LIMIT windows are O(n²) API cost; eventlog capped at 5 pages/fighter; `alembic check` unsupported; venues 0 (pre-existing).
