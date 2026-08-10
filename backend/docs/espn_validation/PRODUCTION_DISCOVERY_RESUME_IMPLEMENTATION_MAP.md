# Production Discovery + Resume — Implementation Map

Working reference for the production-window phases. Baseline: HEAD `56221cc`
(accepted after PRODUCTION_WINDOW_002). All paths relative to `backend/`.

## Current state (Phase 1 reconstruction — verified by reading code)

| Area | File | Facts |
|---|---|---|
| ESPN client | `src/providers/espn/client.py` | Only HTTP module. Cache + in-flight dedup + token bucket (3 rps, burst 6) + circuit breaker. `paginate()` ALWAYS starts at page 1 (`params.setdefault("page", 1)`), walks via echoed `pageIndex`/`pageCount`. |
| Athlete discovery | `src/providers/espn/provider.py:124` | `fetch_athlete_ids()` — global listing (`/athletes`, ~38k ids) + rosters (`/leagues/{slug}/athletes`), dedup set. NO resume: full re-enumeration on every call. |
| Fighter job | `src/providers/espn/jobs/fighter.py` | Discovery-driven: IDs cached in `state.checkpoint["athlete_ids"]` (memory only — wiped by `mark_completed` on COMPLETED state? No — checkpoint dict survives, but MemorySyncStateStore loses it between CLI runs). Window = `ids[start : start+limit]` ascending; `last_offset` resume in-memory only. |
| Pipeline | `src/sync/pipeline.py` | Fetch → transform → batch upsert with `state.update_progress(page, offset)` after each batch; `mark_completed()` resets offsets. Crash-resume works ONLY if state persisted (it is not, in CLI). |
| Engine | `src/sync/engine.py` | Loads state from `SyncStateStore` per job, saves after each job. CLI passes `MemorySyncStateStore` → zero durability. |
| State store | `src/sync/state_store.py` | Protocol `SyncStateStore` + `MemorySyncStateStore` only. `DatabaseSyncStateStore` referenced in docstrings, NEVER implemented. |
| Checkpoints | `src/sync/checkpoints.py` | `CheckpointManager` (DB `sync_checkpoints`, uq `uq_sync_checkpoints_entity_provider`) — complete, but UNWIRED (grep: no callers outside definition). |
| CLI | `sync.py` | `build_engine()` → `SyncEngine(jobs, statestore=MemorySyncStateStore())`. `run_sync` passes `db_session` to `engine.execute` for run/job records. |
| Ranking job | `src/providers/espn/jobs/ranking.py` | Fetches per-promotion rankings; RankingUpsert SKIPS fighters with no `external_ids` mapping (18/150 resolve today). No injection. |
| Historical events | `src/providers/espn/jobs/historical_event.py` | winningFight → events → competitions → competitors. |
| Competition upsert | `src/sync/upserts/competition.py:127-133` | Competitor with unresolvable fighter → `skipped` (log "Competitor skipped: fighter X not yet synced"). NO registration of the ID for later sync. |
| IdResolver | `src/sync/upserts/id_resolver.py` | `resolve` / `resolve_bulk` / `register` — keyed (provider, external_id, entity_type). Bulk resolve ideal for injection. |
| Models | `src/db/models/support.py` | `SyncCheckpoint` (no data column). `SyncRun`, `SyncJob`, `ExternalId`. |
| Migrations | `alembic/versions/001..006` | 006 latest. Style: `sa.Uuid()` PKs + `server_default=sa.text("gen_random_uuid()")`, named unique constraints, `JSONType` = `JSON().with_variant(JSONB(), "postgresql")`. |
| Tests | `tests/unit|integration` | SQLite `sqlite+aiosqlite://` in-memory fixtures with `Base.metadata.create_all` (works — models are portable). Tests must run WITHOUT a live DB. |
| Scheduler cleanup | `src/scheduler/cleanup.py:76` | Deletes COMPLETED `sync_checkpoints` older than 7 days. NOTE: applies only to `sync_checkpoints`, not the new discovery tables. |

## Known facts / constraints (research)
- Union census 38,014 ids; listing 38,006; rosters add ~1,200 unique (hidden profiles).
- Ranking-referenced fighters 150; ~18 resolved today (window 001 band 2,085,811–2,502,283).
- Hidden profiles (DJ 2512089, Rousey, Gracie, Shamrock, Ngannou 2579646) absent from listings.
- Rousey ID collision (shared athlete ID) — identity is EXTERNAL-ID ONLY, no name matching anywhere.
- Content-dependent 404s are normal (records/statistics/eventlog); must not trip breaker (already fixed) and must not be retried forever.

## Design decisions (Phases 2–4)

### D1 — Registry = single deduplicated athlete-ID source of truth (DB)
New table `sync_discovered_athletes(provider, external_id, source, run_id, consumed, timestamps)`,
unique `(provider, external_id)`. ALL discovery surfaces converge here:
- global listing walk, roster walks (per source, resumably)
- ranking injection (immediately synced → `consumed=true`)
- competition/eventlog competitor refs (queued for the fighter window)

### D2 — Per-source resumable walk checkpoints (new table, same abstraction)
New table `sync_discovery_checkpoints(provider, source, league_slug, page, offset,
discovered_count, last_athlete_id, status, last_error, completed, run_id, last_processed_at)`,
unique `(provider, source, league_slug)`, `league_slug NOT NULL DEFAULT ''` ('' = global).
Managed by `DiscoveryCheckpointManager` in `src/sync/checkpoints.py` (same module/pattern as
`CheckpointManager` — NOT a competing system). Walk resumes at `checkpoint.page + 1`;
COMPLETED sources are skipped unless `ESPN_DISCOVERY_FORCE=1`.

### D3 — Fighter window = next N unconsumed registry ids (ascending)
`SELECT external_id FROM sync_discovered_athletes WHERE provider='espn' AND consumed=false
ORDER BY external_id LIMIT N` — preserves prior ascending-order behavior; consumed flags make
progress crash-proof (offset in SyncState is NOT the source of truth; survived even if
`sync_checkpoints` rows are cleaned after 7 days).

Consumed semantics:
- Resolved + upserted → consumed (in `_upsert`, per batch — crash-safe: only upserted ids consumed).
- Content-dependent 404 / parse-fail → consumed (never retried, "missing records never reset" rule).
- Transient network failure → NOT consumed (retried next run).

### D4 — SyncState persisted to `sync_checkpoints` (+ `data JSONB` column)
`DatabaseSyncStateStore` (new, in `src/sync/state_store.py`) implements the EXISTING
`SyncStateStore` protocol via the EXISTING `CheckpointManager` + `sync_checkpoints` table.
`CheckpointManager.save` gains optional `data` dict → `sync_checkpoints.data`.
CLI `build_engine(session)` wires it in. Engine default stays memory-only (tests).

### D5 — Ranking→athlete injection (bounded, idempotent, no fake IDs)
In `ESPN_RankingSyncJob._fetch`, after collecting RankingDTOs:
1. Collect `fighter_external_id` from dtos (real refs only).
2. `resolver.resolve_bulk` → missing = not synced.
3. Bounded by `ESPN_RANKING_INJECTION_LIMIT` (default 25, `0` disables).
4. `provider.fetch_fighters_by_ids(missing)` + attach records (same as fighter job).
5. `FighterUpsert` via ctx.db → registers external_ids → ranking rows resolve same run.
6. Registry rows added `source='rankings', consumed=true`.

### D6 — Relationship refs → registry
- `CompetitionUpsert._upsert_competitors`: unresolvable fighter → `register_ids(..., source='competition')` (before `skipped`).
- Eventlog (only when enabled): register competitor athlete ids from eventlog payloads (`source='eventlog'`).

### D7 — Migration 007 backfill
Backfill existing synced fighters (external_ids rows, entity_type='fighter') into the
registry as `consumed=true, source='backfill'` → post-deploy windows start on NEW ids,
no re-fetch of the already-synced 2,000.

## Implementation files (Phase 5)
1. `alembic/versions/007_discovery_registry.py` — add `sync_checkpoints.data`, 2 new tables, backfill, indexes.
2. `src/db/models/support.py` — `SyncCheckpoint.data`, `SyncDiscoveredAthlete`, `SyncDiscoveryCheckpoint`.
3. `src/sync/checkpoints.py` — `Checkpoint.data`, `DiscoveryCheckpointManager` (+ `save`/`load`).
4. `src/sync/state_store.py` — `DatabaseSyncStateStore` (+ serialize helpers).
5. `src/providers/espn/discovery.py` — `DiscoveryService` (walk, register, window, consume).
6. `src/providers/espn/client.py` — `paginate(..., start_page=1)`.
7. `src/providers/espn/jobs/fighter.py` — registry-driven window.
8. `src/providers/espn/jobs/ranking.py` — injection hook.
9. `src/sync/upserts/competition.py` — register missing competitor fighters.
10. `sync.py` — `build_engine(session)` with `DatabaseSyncStateStore`.

## Validation plan (Phase 7) — bounded, no full re-scan
- Run A: `ESPN_FIGHTER_SYNC_LIMIT=30`, kill mid-walk (~10s) → resume → walk completes from page N (log proof).
- Run B: complete small window; re-run same LIMIT → fighter job api_calls ≈ 0, inserts = 0 (no repeated prefix scanning).
- Run C: kill mid-window (LIMIT=200, kill ~75s) → resume → remaining only, no dupes (fighters count by external_id).
- Ranking run with injection: at least one current ranked fighter (e.g. Makhachev 2579938) enters fighters + rankings resolve.
- Representative inspection: DJ / Rousey / Gracie / Shamrock / Ngannou present in registry (from listing walk) — note positions.

## Quality gates (Phase 10)
`pytest`, `ruff`, `mypy`, `alembic upgrade head` + `alembic current`/`heads` (single head), DB migration applied.
