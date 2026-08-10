# PRODUCTION DISCOVERY + CHECKPOINT PHASE — Implementation & Validation Record

Phase artifact for the durable-discovery/checkpoint phase. Companion to
`PRODUCTION_DISCOVERY_RESUME_DESIGN.md` (design) and
`PRODUCTION_DISCOVERY_RESUME_IMPLEMENTATION_MAP.md` (map). Chronological record
of what was implemented, what was fixed, and what was live-validated.
Append-only history is in `ESPN_PRODUCTION_JOURNEY.md`.

---

## 1. Objective

Make ESPN production sync durable and discovery-complete:

1. **Resumable discovery** — the ~38k athlete-ID census must never restart from
   page 1 after a process kill.
2. **No repeated prefix scanning** — completed discovery sources are never
   re-walked; the fighter window advances by unconsumed registry IDs.
3. **Relationship-discovered athletes enter the fighter pipeline** — ranking
   refs, competition competitor refs, and eventlog refs feed the same
   deduplicated registry that the fighter window consumes.
4. **DB-backed checkpoints** — SyncState persisted to the existing
   `sync_checkpoints` table (no competing checkpoint system).

All live validation was **bounded** (windows of 30/30/200 + ranking injection);
no full-census fighter sync, no `LIMIT=21000`, no unbounded crawl.

## 2. Starting state (verified before this phase)

- HEAD `56221cc` (accepted post `PRODUCTION_WINDOW_002`), branch `main`.
- DB `mma` @ localhost:5432, alembic at **006**; migration 007 existed in the
  working tree but was **unapplied**.
- fighters 2000 · fighter_records 1998 · external_ids 2350 · rankings 17 ·
  sync_runs 5 · sync_checkpoints 0.
- Discovery was in-memory only: `fetch_athlete_ids()` re-enumerated the full
  listing every run; fighter window lived in `SyncState.checkpoint["athlete_ids"]`
  under `MemorySyncStateStore` (lost between CLI processes).
- 23 new C/D tests existed; **18/23 failed** (SQLite portability + real bugs).
- `CheckpointManager` was complete but unwired; `DatabaseSyncStateStore` absent.

## 3. Research evidence used (frozen, read-only)

- Census ≈ 38,014 ids; global listing ≈ 38,006; rosters add hidden profiles.
- Rate envelope 2–5 req/s; page-based pagination, limit ≤ 1000.
- Ranked athletes (~150 refs, ~18 resolved at window 002); hidden profiles
  (DJ/Rousey/Gracie/Shamrock/Ngannou) absent from listings.
- Rousey ID-collision documented — identity is external-ID-only, no name
  matching anywhere (untouched by this phase).

## 4. Implementation summary (what was already in the tree + what was fixed)

The candidate C/D implementation (uncommitted working tree) was reviewed,
debugged, completed, and validated. Files (all under `backend/`):

| File | Role |
|---|---|
| `alembic/versions/007_discovery_registry.py` | `sync_checkpoints.data` JSON + 2 new tables + consumed backfill; **applied this phase** |
| `src/db/models/support.py` | `SyncCheckpoint.data`, `SyncDiscoveredAthlete`, `SyncDiscoveryCheckpoint`; SQLite-portable PK/UUID types |
| `src/sync/checkpoints.py` | `DiscoveryCheckpointManager`; portable `index_elements` upserts |
| `src/sync/state_store.py` | `DatabaseSyncStateStore` (protocol-compatible, via CheckpointManager) |
| `src/providers/espn/discovery.py` | `DiscoveryService` — resumable per-source walks, registry, window, consumed flags |
| `src/providers/espn/client.py` | `paginate(..., start_page=)` for resumable walks |
| `src/providers/espn/jobs/fighter.py` | Registry-driven window; healthy-fetch dead-end consumption |
| `src/providers/espn/jobs/ranking.py` | Bounded ranking→athlete injection (default 25, `0` disables) |
| `src/providers/espn/jobs/historical_event.py` | Eventlog competitor refs → registry (awaited) |
| `src/sync/upserts/competition.py` | Unresolvable competitor fighters → registry (`source='competition'`, awaited) |
| `sync.py` | `build_engine(session)` wires `DatabaseSyncStateStore` |
| tests | 23 new unit tests + 2 updated integration tests |

### Defects found and fixed this phase (diagnosis in journey §11)

1. **Missing `await` on `register_ids(...)`** in `competition.py:134` and
   `historical_event.py:126` — coroutine created and discarded; relationship
   registration silently never ran (any dialect). Fixed.
2. **SQLite `BigInteger` PK doesn't autoincrement** — `sync_discovered_athletes.id`
   now `BigInteger().with_variant(Integer, "sqlite")`.
3. **`on_conflict_do_update(constraint="<name>")` drops the conflict target on
   SQLite** (verified by SQLAlchemy render experiment) → duplicate rows →
   `MultipleResultsFound`. Both managers now use `index_elements=[...]`.
4. **`register_ids` claimed "ON CONFLICT DO NOTHING" but never invoked it** —
   would `IntegrityError` on re-registration on Postgres. Now dialect-portable
   (`postgresql.insert().on_conflict_do_nothing(constraint=...)` vs SQLite
   target-less `on_conflict_do_nothing()`).
5. **UUID NUMERIC-affinity corruption on SQLite** — all-digit hex UUIDs stored
   as REAL floats crash the result processor (`'float' object has no attribute
   'replace'`). `run_id` on both new tables and `ExternalId.entity_id` now use
   `UUID(...).with_variant(String(36), "sqlite")` (Postgres unchanged).
6. **`_sync_limit()` default is `0` = UNBOUNDED** (not "1000" as the journey
   §3 claimed) — all live runs explicitly set `ESPN_FIGHTER_SYNC_LIMIT`.
7. **2 integration tests** asserted the pre-rewrite contract
   (`fetch_athlete_ids` + `state.checkpoint["athlete_ids"]`) → updated to the
   registry-driven contract (same intent: bounded window + records attach).
8. Test-file bugs (missing `await` on `registry_ids(...)` helper) — fixed.

## 5. Migration 007 — what it changes, why applied

- `sync_checkpoints.data` (JSON) — carries SyncState payload fields without a
  dedicated column (`DatabaseSyncStateStore`).
- `sync_discovered_athletes` — deduplicated athlete-ID registry, unique
  `(provider, external_id)`, `consumed` flag, window index
  `(provider, consumed)`.
- `sync_discovery_checkpoints` — per-source walk state (page/offset/count/last
  id/status/completed/run_id), unique `(provider, source, league_slug)`.
- **Backfill**: existing synced fighters (external_ids, entity_type='fighter')
  seeded as `consumed=true, source='backfill'` → post-deploy windows start on
  NEW ids, no re-fetch of the 2,000.
- Reversible (`downgrade` drops both tables + the column). Single head (007).
- **Applied this phase** (`alembic upgrade head`): verified 2000 backfill rows,
  0 registry dupes, all indexes present, alembic current = 007.
- **Migration 008** (added after review): migration 007 created
  `sync_checkpoints.data` as plain JSON, but the model maps it through
  `JSONType` → JSONB on Postgres (permanent autogenerate diff). 008 alters the
  column to native JSONB (lossless `USING data::jsonb`, portable, reversible).
  Applied: `data_type=jsonb`, alembic current = 008, single head.
- **DB-backed SyncState verified live**: `sync_checkpoints` now holds 2 rows
  (fighter + ranking, COMPLETED, JSONB payloads) written by
  `DatabaseSyncStateStore` during the validation runs.

## 6. Quality gates (before migration/live runs)

- `pytest tests/` → **478 passed, 2 skipped** (env-gated live tests skip).
- `ruff check` → clean (all touched files).
- `mypy` → clean (9 source files).
- `alembic heads` → single head `007`; `alembic current` → `007` after apply.

## 7. Live validation (bounded — Phase 7 of the plan)

All runs `--full --entity fighter` unless noted; `PYTHONIOENCODING=utf-8`
(CLI banner is Unicode; cp1252 redirect otherwise crashes).

### Run A — kill mid-walk → resume from checkpoint (LIMIT=30)
- Started; **killed at 12s while walking the global listing (page 18)**.
- Checkpoint persisted: `global_listing page=18, IN_PROGRESS, 18000 ids`.
- Registry after kill: 18,000 rows (16,000 new from walk pages 1–18 +
  2,000 backfill; page 18 partially registered pre-kill).
- **Resume run**: `global_listing` walked starting at **page 19** (log proof),
  no page-1 restart. Walk completed: global 39 pages/38,011 ids + all 6
  rosters COMPLETED. Window: **30 resolved of 30**.
- fighters 2000 → **2030**.

### Run B — idempotent re-run, no repeated prefix (LIMIT=30)
- Discovery walk requests: **0** (all sources "already completed — skipped").
- Window advanced to the next 30: fighters 2030 → **2060**; 0 errors.

### Run C — kill mid-window → resume (LIMIT=200)
- Started; killed at 30s mid-fetch (90 of 200 athlete requests, 0 upserted —
  crash-safe: no partial consumption).
- Resume: **200 resolved of 200**, inserted=400 (profiles + records), 0 errors.
- fighters 2060 → **2285**.

### Ranking → athlete injection (live)
- `--rankings`: fetched per-promotion rankings (133 UFC etc.); **25 unsynced
  ranked fighters of 109 referenced** injected (limit default 25), upserted 50
  fighter rows, 25 registry ids consumed (`source='rankings'`); ranking rows
  inserted 59.
- Resolution improved: **all ranking rows now resolve to fighters** (56/56 vs
  ~17 before).
- Note: injection is ascending-by-ID and bounded; deep-ID ranked fighters
  (e.g. Makhachev 2579938) require a larger `ESPN_RANKING_INJECTION_LIMIT`
  (e.g. 110) in a future run — expected bounded behavior, not a bug.

### Representative athlete inspection
- **DJ (2512089)** present in registry (`global_listing`) — the research's
  "hidden" claim is partially falsified for DJ (present in the listing).
- **Rousey (245), Gracie (16594), Shamrock (16335), Ngannou (2579646),
  Makhachev (2579938)** absent from the listing walk — true hidden profiles,
  reachable only via ranking/competition injection. Confirms the ordering
  problem the phase solves (window at ID ~2.5M; famous fighters deeper).

## 8. Database before/after

| Table | Before | After |
|---|---|---|
| fighters | 2000 | **2285** |
| fighter_records | 1998 | **2283** |
| external_ids | 2350 | **2635** |
| rankings | 17 | **56** |
| statistics | 399 | 399 |
| events / competitions / competitors | 24 / 260 / 47 | unchanged |
| sync_discovered_athletes | — | **38,011** (36,011 global + 2,000 backfill; roster ids deduped) |
| sync_discovery_checkpoints | — | **7** (all COMPLETED) |
| sync_checkpoints | 0 | 0 (fighter windows consumed via registry; per-entity SyncState rows created only when entities run with progress) |
| sync_runs | 5 | **11** |

### Integrity (post-validation)
- Duplicate (provider, external_id): fighters **0** · external_ids **0** ·
  registry **0**.
- Orphaned FKs: fighter_records **0** · statistics **0** · competitors **0** ·
  rankings **0**.
- NULL provider/external_id in fighters: **0**.
- HTTP 429 / 5xx / breaker opens across all run logs: **0** (rate envelope 3 rps
  held; the only "429" log hits are UUID substrings).
- Registry dedup across sources proven: roster walks (ufc 1840 + bellator 986 +
  pfl 587 + ksw 208 + ifc 172 + ofc 408 = 4,201) converged into the existing
  global rows — no new rows from rosters beyond the global walk.

## 9. Performance (old vs new)

| Metric | OLD (windows 001/002) | NEW |
|---|---|---|
| Census enumeration | re-walked **every** run (~44+ requests) | **once** (Run A: 45 requests); Run B/C/rankings: **0** discovery requests |
| Fighter prefix | rescan from offset (O(n²)-style) | consumed flags — window always advances |
| Resume | in-memory only (lost on kill) | durable checkpoints — mid-walk kill resumes at page 19 |

## 10. Remaining risks / notes

1. Census (38,011 registered) is NOT proof of MMA-completeness — ~35.7k ids
   remain pending; most are the research's MMA-likely/uncertain population.
2. `sync_checkpoints` rows are cleaned after 7 days by scheduler cleanup — the
   fighter window does NOT depend on them (registry consumed flags are the
   source of truth); per-entity SyncState still benefits from them while fresh.
3. Ranking injection is bounded per run (25) — a full ranked-fighter backfill
   needs one run with a larger limit (~110).
4. Rousey ID collision documented; identity remains external-ID-only.
5. Venues table still 0 rows (known ESPN venues gap, out of scope here).
6. Migration applied only to the localhost acceptance DB; production would
   require the same `alembic upgrade head` (reversible).
7. Reviewer notes (accepted as documented tradeoffs, no code change):
   (a) `_sync_limit()` default `0` = unbounded — always pass the env var;
   (b) ranking injection consumes all fetched ids without the fighter job's
   healthy-fetch guard (0 errors observed; mirror the guard if ever needed);
   (c) per-id transient failures can be dead-ended inside an otherwise healthy
   window; (d) window selection has no row-locking (idempotent upserts make
   concurrent runs safe but duplicative); (e) window ordering is lexicographic
   (correct for 7-digit numeric ids).

## 11. Decision

Architecture validated end to end with bounded runs. Durable discovery,
no-repeated-prefix, relationship injection, and DB-backed checkpoints all
proven live.

## 12. Next step

**READY_FOR_PRODUCTION_WINDOW** — the next production step is a bounded
fighter window (e.g. `ESPN_FIGHTER_SYNC_LIMIT=1000`) plus one rankings run with
`ESPN_RANKING_INJECTION_LIMIT=110` (full ranked-fighter backfill). No
unbounded 38k sync; the census is enumerated once and the window advances
incrementally. No commit/push performed in this phase (per standing rules).
