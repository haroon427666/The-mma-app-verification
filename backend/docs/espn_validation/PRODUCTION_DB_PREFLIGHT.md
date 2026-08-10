# PRODUCTION DATABASE PREFLIGHT — ESPN Sync Target State

> **Date:** 2026-08-10 · **Type:** READ-ONLY preflight (no writes, no sync, no migrations)
> **Companion evidence:** `backend/docs/espn_validation/` (acceptance evidence, commit `56221cc`)
> **ESPN implementation:** commit `cda302c` · **This file is a new artifact — NOT covered by `CHECKSUM_MANIFEST.json`** (manifest intentionally unmodified).

---

## 1. Executive conclusion

The only database configured anywhere in the project is `localhost:5432/mma`
(user `mma`, dev credentials from repo defaults). The same database was used for
the bounded acceptance validation, and it still holds exactly that acceptance
dataset (100 fighters, 6 events, 2 sync runs — all COMPLETED). **There is no
separate production database.** The acceptance database IS the current
application/sync target database.

The database is healthy for a first production-windowed ESPN sync:
migration 006 applied, zero duplicates, zero orphans, idempotent upserts
(live-proven twice), and no non-ESPN/production user data present.

**STATUS: SAFE_TO_PROCEED** (with a bounded first window — see §12).

---

## 2. Database classification

**ACCEPTANCE_DB** — identical to the currently configured application DB.

| Evidence | Value |
|---|---|
| fighters | exactly 100, all created 2026-08-09 (acceptance run date) |
| events | exactly the acceptance set: UFC 200 (2016), Bellator 178 (2017), UFC 231 (2018), Bellator 214 (2019), UFC 235 (2019) + 1 upcoming (UFC Fight Night 2026-08-09) = 6 |
| sync_runs | exactly 2, both `COMPLETED`/`auto`/`espn`, timestamps 2026-08-09/10 = the acceptance dual-run |
| known hidden profiles | `espn:2335653` (Ken Shamrock) present in window; DJ/Rousey/Gracie/Ngannou absent — consistent with a bounded 100-ID window (IDs sorted, first window) |
| sync_checkpoints | 0 rows (in-memory checkpointing; nothing persisted) |
| users / devices / notifications / favorites / watchlist / preferences / sessions | all 0 (no production/user data) |
| fighter external_id range | 2085811 – 2335653 (sorted bounded window) |

No evidence of any T05-era state (the pre-integration "1,831 fighters / 110 rankings"
state) exists in this DB — that state was never this database's content.

---

## 3. Application DB configuration

| Source | Value (redacted) | Environment |
|---|---|---|
| `backend/src/config.py` (`Settings.database_url`) | `postgresql+asyncpg://mma:mma@localhost:5432/mma` | default (no `.env` file present — `env_file=".env"` not found in `backend/`) |
| `backend/.env.example` | same localhost URL | development template |
| `backend/docker-compose.yml` (app service) | `mma:mma@db:5432/mma` (host `db` = docker service) | docker/dev |

- **No `backend/.env` exists** → the running default is the localhost URL above.
- Shell env: no `DATABASE_URL` set in this session's environment.
- Consumers: FastAPI app (`src/db/session.py` engine), services, repositories.

## 4. ESPN sync DB configuration

| Source | Value | Notes |
|---|---|---|
| `backend/sync.py` (`setup_database`) | `settings.database_url` → `localhost:5432/mma` | CLI `--full/--resume/--weekly/--rankings` |
| `backend/src/sync/engine.py` | engine writes `sync_runs`/`sync_jobs` via `src.db.models.support` | same session as app |
| Live acceptance test `tests/integration/test_sync_live.py` | `create_async_engine(settings.database_url)` | **SAME database as app** |
| `verify_espn.py` | HTTP-only (no DB) | not DB-relevant |
| `scripts/espn_live_benchmark.py` | HTTP-only (no DB) | not DB-relevant |

## 5. Acceptance DB configuration

The acceptance run used the **same** `settings.database_url` (`localhost:5432/mma`).
`test_sync_live.py` truncates the sync tables at test start on that database
(documented in the test) — the acceptance dataset is the residue of that dual-run.

## 6. Same or different?

**SAME** — application DB, ESPN CLI DB, and acceptance DB are one database:
`localhost:5432/mma` (redacted). No other database URL exists in repo config,
tests, CLI, or alembic.

| URL found in | Database |
|---|---|
| `src/config.py` default | localhost:5432/mma |
| `.env.example` | localhost:5432/mma |
| `alembic.ini` | localhost:5432/mma |
| docker-compose app/db | mma@db:5432/mma (same DB, docker network alias) |

## 7. Current table counts (read-only, 2026-08-10)

| Table | Count | Table | Count |
|---|---|---|---|
| fighters | 100 | sync_runs | 2 |
| fighter_records | 100 | sync_jobs | 20 |
| statistics | 48 | sync_checkpoints | 0 |
| events | 6 | external_ids | 240 |
| competitions | 73 | provider_payloads | 0 |
| competitors | 4 | provider_conflicts | 0 |
| rankings | 4 | dead_letters | 0 |
| promotions | 48 | users | 0 |
| venues | 0 | devices / notifications / favorites / watchlist / preferences / sessions | 0 |
| broadcasts | 1 | alembic_version | 1 (row: `006`) |
| weight_classes | 13 | | |

Server: **PostgreSQL 18.4** · db `mma` · schema `public` · user `mma` (dev).

## 8. Sync history

| Run | id | Status | Start (UTC+05) | Duration | Ins | Upd | Skp | Err |
|---|---|---|---|---|---|---|---|---|
| 1 | `accd73ad-...` | COMPLETED | 2026-08-09 23:58:11 | 141,246 ms | 384 | 0 | 142 | 0 |
| 2 | `5e400b2a-...` | COMPLETED | 2026-08-10 00:00:45 | 5,253 ms | 4 | 100 | 422 | 0 |

- Both runs: `mode=auto`, `provider=espn`, 10 jobs each (promotion, venue, weight_class,
  fighter, event, competition, broadcast, statistic, ranking, historical_event), all COMPLETED.
- Run 2 is the idempotency run (100 fighters updated, 422 skipped, 4 ranking re-inserts).
- **Latest run = acceptance run.** **No production/full-census sync has ever occurred**
  (no run touches ~38k scale; checkpoint table empty).

## 9. Data-integrity results (read-only)

| Check | Result |
|---|---|
| Duplicate `(provider, external_id)` in external_ids | **0** |
| `uq_fighters_provider_external`, `uq_events_provider_external` unique constraints | present |
| Competitions without event / competitors without competition / fighter_records without fighter / statistics without fighter / sync_jobs without run | **0 / 0 / 0 / 0 / 0** |
| Statistics with `competitor_id` (per-fight rows) | 0 (all 48 are career rows) |
| Statistics NULL category/label/fighter_id | 0 / 0 / 0 |
| Events NULL status/name/promotion_id | 0 / 0 / 0 |
| fighters `full_name` NULL | **100** (first/last_name populated; `full_name` not populated by parser — pre-existing acceptance data characteristic, NOT a schema violation; NOT NULL on first/last only) |
| fighters `is_active` NULL | 0 |
| Known ESPN IDs present | `2335653` (Shamrock) = 1; DJ/Rousey/Gracie/Ngannou = 0 (outside bounded window, expected) |

## 10. Existing ESPN records / collision risk

- All 100 fighters, 6 events, 48 promotions, 13 weight classes, 73 competitions are `provider='espn'`.
- **No non-ESPN records exist** (TSDB/Octagon not wired).
- Collision boundary: `(provider, external_id)` unique per fighters/events; external_ids
  unique `(entity_type, entity_id, provider)`. The upcoming census upserts by
  `external_id` (IdResolver) → existing rows UPDATE, new rows INSERT. **No collision risk.**
- Rousey `2563797` cross-ID caveat (resolves to "Alexis") documented in acceptance evidence — informational.

## 11. Checkpoint / resume behavior (code audit — no changes)

- CLI `sync.py` and live tests construct the engine with **`MemorySyncStateStore`** (in-memory dict).
- `DatabaseSyncStateStore`/`RedisSyncStateStore` exist only as **docstring mentions — not implemented.**
- `sync_checkpoints` table exists (migration) but holds **0 rows**; `CheckpointManager`
  (`src/sync/checkpoints.py`) is **not wired** to the engine/pipeline.
- Consequence: checkpoint (discovered athlete-ID set + per-batch offset) lives only in
  the process. **Restarting the process loses resume progress** (re-enumerates listings,
  re-resolves from window start). Upserts remain idempotent, so no duplicates on re-run.
- Bounded production windows **are supported** in-process:
  `ESPN_FIGHTER_SYNC_LIMIT`, `ESPN_MAX_PAGES` (default 200),
  `ESPN_MAX_HISTORICAL_EVENTS` (default 200), `ESPN_STATS_MAX_FIGHTERS` (default 200),
  `ESPN_EVENTLOG_ENABLED` (default off) + `ESPN_EVENTLOG_MAX_FIGHTERS` (50).
- **A full 38k census is safe only as a single long process** (~3.5h at 3 rps) or
  windowed runs with manual offset tracking; cross-process resume = future DB-backed store.

## 12. Production-sync safety assessment

1. **Safe to run?** YES — with a **bounded first window** (`ESPN_FIGHTER_SYNC_LIMIT`).
   Rate envelope 3.0 rps/burst 6/6 concurrency (research 2–5 rps @ 4–8 workers) enforced
   by the fixed token bucket; breaker correct; idempotent upserts live-proven.
2. **Which DB receives data?** `localhost:5432/mma` (the only configured DB).
3. **Intended application DB?** YES — it is the application's configured DB (SAME).
4. **Empty or merge?** MERGE — 100 fighters / 6 events already present will be
   updated (same external_ids), new census IDs inserted. Not destructive.
5. **Existing data affected?** Only ESPN rows by external_id upsert. Zero user data
   exists (users=0) — nothing else to disturb. Historical-event competitors populate
   as fighters sync.
6. **Collisions?** None — 0 dupes, unique constraints in place.
7. **Schema prerequisites?** alembic head/current = `006` = applied (verified).
   `alembic check` unsupported (pre-existing env.py), not a blocker.
8. **Config suitable for first window?** YES with bounds; NOT suitable unbounded
   (default `ESPN_FIGHTER_SYNC_LIMIT=0` = full ~38k ≈ 3.5h single process).
9. **Recommended first window:** `ESPN_FIGHTER_SYNC_LIMIT=1000`
   (≈ few minutes at 3 rps), `ESPN_MAX_HISTORICAL_EVENTS` default 200,
   eventlog **off** for run 1; then scale 1,000 → 5,000 → full census in dedicated windows.
10. **Monitor:** `sync_runs`/`sync_jobs` status + counts + `api_calls`; rate limiter
    (expect no 429s/retries); breaker stays CLOSED; stats count variance (48 vs 88 —
    content-dependent, known); eventlog pagination (capped 5 pages); duplicate/orphan
    re-check after each window; duration trend vs 141 s acceptance baseline.

## 13. Exact next recommended operation (NOT executed)

```
cd backend
# windowed first production sync
$env:ESPN_FIGHTER_SYNC_LIMIT = "1000"        # bounded first window
python sync.py --full
# then: read-only re-verify counts/dupes/orphans; escalate window size
```
No migration, no schema change, no code change required.

---

## Final decision

**STATUS: SAFE_TO_PROCEED**

**DATABASE:** ACCEPTANCE_DB (== only configured DB)
**ESPN_SYNC_TARGET:** postgresql+asyncpg://***@localhost:5432/mma (redacted)
**ACCEPTANCE_DB:** postgresql+asyncpg://***@localhost:5432/mma (redacted — SAME)
**SAME_DATABASE:** YES
**CURRENT_FIGHTERS:** 100
**CURRENT_EVENTS:** 6
**CURRENT_SYNC_RUNS:** 2
**FULL_CENSUS_SYNC_ALREADY_RUN:** NO
**PRODUCTION_SYNC_EXECUTED:** NO
**DATABASE_MODIFIED_BY_THIS_TASK:** NO (all queries read-only, `readonly` transaction mode)
**RESEARCH_MODIFIED_BY_THIS_TASK:** NO
**CODE_MODIFIED_BY_THIS_TASK:** NO (one new report file created: this document)
