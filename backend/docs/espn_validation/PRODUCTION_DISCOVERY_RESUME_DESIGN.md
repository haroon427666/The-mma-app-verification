# Production Discovery + Resume — Design (Phases 2–4)

Status: DESIGN COMPLETE — implementation per this document + implementation map.
Baseline: HEAD `56221cc`. Scope: fighter discovery ordering + durable resume + ranking
injection. Backward compatibility: existing jobs, plans, CLI flags, env vars unchanged.

---

## Phase 2 — Minimum safe architecture

### Problem (from research)
`SyncEngine` already has a complete checkpoint abstraction (`SyncStateStore`,
`CheckpointManager`, `sync_checkpoints` table), but the CLI wires the in-memory store:
- `sync.py build_engine()` → `MemorySyncStateStore` → NO resume across runs; a killed run
  re-enumerates the full 38k-id census and re-scans the synced prefix on every run.
- `CheckpointManager` + `sync_checkpoints` are implemented but **unwired** (zero callers).

### Design: reuse the existing abstraction, don't build a parallel system
1. **`DatabaseSyncStateStore`** — new class in `src/sync/state_store.py` implementing the
   existing `SyncStateStore` protocol (same `load`/`save` shape as `MemorySyncStateStore`).
2. Persistence: the EXISTING `sync_checkpoints` table + `CheckpointManager`. A single new
   `data JSONB` column (migration 007) carries the `SyncState` fields that have no column
   today (`checkpoint` dict, timestamps, cursors). Scalar columns stay in sync with the
   existing ones (`last_offset`, `last_page`, `total_records`, `status`, `last_error`,
   `completed`) so the table remains meaningful to humans and to the existing scheduler
   cleanup.
3. `CheckpointManager.save` gains an optional `data: dict | None` parameter (None = do not
   touch the column — backward compatible with all existing callers, of which there are
   currently none outside tests).
4. CLI wiring: `build_engine(session)` creates the DB-backed store. Engine default remains
   in-memory so every existing test keeps working unchanged.

### Why this is safe
- No new state system; the engine's `_get_state`/`_save_state` flow is untouched.
- Idempotent: `save` is an upsert on the existing unique constraint
  `uq_sync_checkpoints_entity_provider`.
- `mark_completed` resetting pagination offsets is harmless for the fighter job because
  progress is owned by the discovery registry (D3), which is NOT affected by the 7-day
  cleanup of `sync_checkpoints`.

---

## Phase 3 — Fix discovery ordering

### Problem (from research)
`fetch_athlete_ids()` re-enumerates the flat listing (39 pages) + rosters on EVERY fighter
run. A kill/restart loses `state.last_offset` (memory store) → next run re-scans pages 1..N
and re-fetches the synced prefix ("repeated prefix scanning"). Also: competitor refs found
during historical events are dropped (`skipped`) when the fighter isn't synced yet — no
path back into the pipeline.

### Design
**A. Deduplicated registry table** `sync_discovered_athletes`
- Unique `(provider, external_id)`; `consumed` flag; `source` (provenance); `run_id`.
- ALL surfaces converge here (listing walk, roster walks, ranking injection, competition
  refs, eventlog refs when enabled). Unique constraint ⇒ one row per athlete, first source
  wins, idempotent inserts via `ON CONFLICT DO NOTHING`.

**B. Resumable per-source walk checkpoints** `sync_discovery_checkpoints`
- One row per (provider, source, league_slug) — `''` for the global listing.
- `page` = last page processed; walk resumes at `page + 1`; `completed` sources are skipped
  (re-walk only with `ESPN_DISCOVERY_FORCE=1`); FAILED sources retry from last page.
- Managed by `DiscoveryCheckpointManager` in `src/sync/checkpoints.py` — same module,
  same shape as `CheckpointManager` (one abstraction, two tables).
- Every page commit: registry inserts + checkpoint row are committed per page so a hard
  kill cannot lose walk progress.
- `client.paginate(..., start_page=N)` — new optional param, default 1 (fully backward
  compatible; the existing `fetch_athlete_ids` keeps its current behavior and is still
  tested by `test_espn_discovery.py`).

**C. Fighter window = next N unconsumed ids (ascending)**
- `SELECT ... WHERE provider='espn' AND NOT consumed ORDER BY external_id LIMIT N`.
- Same ascending order as today ⇒ window 001/002 semantics preserved (first window after
  migration = ids above 2,502,283, thanks to the backfill marking the 2,000 synced
  fighters consumed).
- Consumed transitions (crash-safe, per-batch):
  - batch upsert success → `_upsert` marks those ids consumed (only successfully upserted ids);
  - content-dependent 404 / parse failure → consumed in `_fetch` (never retried — matches the
    records "never reset" rule);
  - transient network error → NOT consumed (retried on next run; bounded by window size).
- `state.checkpoint["athlete_ids"]` caching is removed (registry replaces it; stale keys
  from old runs are ignored).

**D. Relationship refs enter the pipeline**
- `CompetitionUpsert._upsert_competitors`: unresolvable fighter → registry insert
  (`source='competition'`, unconsumed) → next fighter window syncs it → competitor rows
  resolve on a later run. No speculative creation: only real refs from real payloads.
- Eventlog (gated by existing `ESPN_EVENTLOG_ENABLED`): competitor athlete ids from
  eventlog payloads → registry (`source='eventlog'`).

### Compatibility guarantees
- `fetch_athlete_ids()` untouched (still used by tests); new walk lives in
  `DiscoveryService` (`src/providers/espn/discovery.py`) with the same two sources.
- Fighter job behavior for existing DB rows: migration backfill inserts external_ids rows
  (entity_type='fighter') as `consumed=true, source='backfill'` → first post-deploy window
  advances to never-synced ids (NO repeated prefix scanning of the existing 2,000).
- Bounded windows unchanged: `ESPN_FIGHTER_SYNC_LIMIT` (0 = all), rate envelope 3 rps.

---

## Phase 4 — Ranking → athlete injection

### Problem (from research)
`RankingUpsert` skips any ranking entry whose fighter has no `external_ids` mapping
(research: only 18 of 150 rank-referenced fighters were synced). The `rankings` table is
therefore incomplete relative to ESPN's published rankings, and the gap compounds because
the skipped fighters are exactly the ones fans search for (champions).

### Design
In `ESPN_RankingSyncJob._fetch` (before returning dtos to the pipeline):

1. Collect the real `fighter_external_id` set from the fetched RankingDTOs.
2. `IdResolver.resolve_bulk("espn", "fighter", ids)` → missing = not yet synced.
3. Bound the injection: `ESPN_RANKING_INJECTION_LIMIT` (default 25, `0` disables) — the
   ranking job must stay cheap; deep backfills happen via the fighter window.
4. Fetch missing profiles (`fetch_fighters_by_ids`) + attach records (shared helper with
   the fighter job) → real athlete resources only — **no fake IDs, no speculative athlete
   creation**; content-dependent 404s are skipped.
5. `FighterUpsert` on the job's session → external_ids registered → the SAME run's
   `RankingUpsert` resolves them.
6. Registry bookkeeping: `register_ids(ids, source='rankings', consumed=True)` — injected
   fighters are fully synced (profile + records) and must not be re-fetched by the window.

### Safety
- Idempotent: FighterUpsert keyed by `(provider, external_id)`; resolve_bulk skips synced
  fighters; ON CONFLICT DO NOTHING on the registry.
- Bounded: hard cap per run (25 default) — full listing coverage remains the fighter
  window's job.
- No behavior change when `ESPN_RANKING_INJECTION_LIMIT=0` or when all referenced fighters
  are already synced (the 18 today → 0 extra requests).
- Identity stays external-ID-only (Rousey collision documented in research; no name
  matching anywhere in this design).

---

## Open items / deferred (documented, not implemented)
- Freshness re-walk: COMPLETED sources are not re-walked automatically; `ESPN_DISCOVERY_FORCE=1`
  triggers a full re-walk (idempotent). Automatic drift detection is future work.
- Scheduler path (`src/sync/scheduler.py`) does not pass a db session to the engine →
  no state persistence there (pre-existing; CLI path gets it in this phase).
- Kill during a hard crash leaves `sync_runs.status='RUNNING'` (pre-existing behavior;
  no heartbeat/finalizer exists — noted in validation).
