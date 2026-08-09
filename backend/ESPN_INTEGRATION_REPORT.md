# ESPN Production Integration — Final Report

> Date: 2026-08-09 · Workspace: production repo (backend/) — research archive untouched.
> Companion docs: `backend/ESPN_INTEGRATION_PLAN.md` (architecture/plan), `backend/ESPN_ENDPOINT_CATALOG.md` (reconciled catalog).

---

## 1. What the frozen research established

The frozen research (`research/espn_endpoint_discovery/`, 2026-08-09) established, with live-probe evidence:

- The flat athlete listing exposes ~**38,006 IDs**; the largest defensible census is **38,014** (38,006 verified + 8 hard-400 legacy). Classified: **2,763 confirmed MMA · 33,352 MMA-likely · 1,845 uncertain · 45 combat-other · 8 invalid · 1 stub**. 38,014 is NOT claimed to be the mathematical total.
- **49 promotions** (48 enumerated + CES verified separately); the "other" league (~27,286 IDs) is compositionally unresolved.
- **`/leagues/{slug}/events` is upcoming-only** (count=1 for every league) — never a historical archive. Historical discovery = **rankings → `ranks[].winningFight` → events/{id} → competitions → competitors** (47 hooks; verified live, UFC 235 2019, 12 competitions) + athlete **eventlogs** (~36k refs) + season types.
- **96 endpoint families**: 75 confirmed, 15 failed, 4 content-dependent, 1 current-only, 1 observed/unverified. **10 P0 surfaces**.
- Pagination is **page-based** (1-indexed, offset ignored, limit capped ~1000, default ~25).
- ONE Championship slug = **`ofc`**.
- Dead surfaces: core v3 MMA athlete (404), site v1 (403), sport dictionaries (404), teams (vestigial).
- **Performance envelope**: 4–8 workers at **2–5 req/sec sustained**; keep-alive; bounded concurrency; exponential backoff; retry 429/500/502/503/504 + DNS; **no retry on 400/404**; checkpoint/resume; dedup; cache reuse.

## 2. What production already had

- Provider-first architecture: `ESPN/TSDB/Octagon → providers → sync engine → DB → services → API → mobile` — **preserved in full**.
- Production-grade `ESPNClient`: keep-alive pool, token-bucket rate limiter, circuit breaker, backoff retries (correct 4xx no-retry), **page-based `paginate()`** with duplicate-page guards, `ESPN_MAX_PAGES` cap.
- Sync engine with plans → pipeline → 9 jobs, per-job commits, durable `sync_runs`/`sync_jobs`, `SyncState` checkpoint/resume, dead-letter + circuit-breaker reliability.
- Idempotent upserts (`BaseUpsert` FIELD_MAP, race-safe, FK resolution, lazy weight-class creation), `IdResolver` mapping, `FighterRecord` + `fighter_records` table, `StatisticsUpsert`, `CompetitionUpsert` with nested competitors.
- Verified parsers (fighters, events, competitions, rankings, records, statistics) and the ESPN endpoint catalog.
- T01–T18 milestone (data flow + contract integrity) complete: **419 tests green** at milestone close.

## 3. What was missing (reconciled gaps)

| # | Gap | Root cause |
|---|---|---|
| C1 | **No historical events** in the DB | Sync relied on upcoming-only league events listing |
| C2 | **Fighters persisted 0-0-0-0** | `fetch_fighter_records()` existed but no job called it; `FighterUpsert` never wrote the `fighter_records` table |
| C3 | **Eventlog unconsumed** | `athlete_eventlog` endpoint defined in config; no job/parser |
| C4 | **Statistics never populated** | `ESPN_StatisticSyncJob._fetch()` returned `[]`; `StatisticsUpsert` skipped career stats (competitor-scoped only, `competitor_id` NOT NULL) |
| C5 | **Discovery UFC-centric** | `fetch_fighters()` hard-defaulted `league_slug="ufc"` (~1,840 of 38,014) |
| C6 | **`is_active` not persisted** | Not in `FighterUpsert.FIELD_MAP`/`_to_model`; parser blindly defaulted |
| C7 | **Rate config exceeded safe envelope** | 10 rps / burst 15 vs research 2–5 rps |
| C8 | **Stale docs/config** | `one-championship` slug; offset-pagination claims; 48-league claims; "records resolved during sync" / "stats synced" claims that code never did |

## 4. What was changed (by phase)

### PHASE 1 — Athlete discovery architecture
- `config.py`: added `global_athletes` endpoint (`/athletes`); added `ESPN_SYNC_LEAGUES` env + `sync_league_slugs()`; `DEFAULT_SYNC_LEAGUES = (ufc, bellator, pfl, ksw, ifc, ofc)`.
- `provider.py`: `fetch_athlete_ids()` enumerates the global flat listing **plus** all configured league rosters, deduplicated by ESPN ID (cheap pass — no profile resolution).
- `provider.py`: `fetch_fighters_by_ids()` resolves profiles with **bounded concurrency** (`max_concurrency`, default 6) and chunked gather (1,000 IDs per batch — no unbounded task creation on the ~38k census); hidden-profile IDs from ranking/event refs resolve too.
- `client.py`: **response cache** (URL-canonicalized, TTL 300s, size-bounded) + **in-flight dedup** (concurrent identical requests share one HTTP call; cache write happens via a done-callback on the shared fetch, so a cancelled waiter never loses the result or triggers a duplicate fetch) + bounded-concurrency semaphore + **request metrics counters**.
- `jobs/fighter.py`: discovery-driven — ID set cached in `SyncState.checkpoint` (resumable), window resumes from `last_offset`, bounded by `ESPN_FIGHTER_SYNC_LIMIT` (0 = all).

### PHASE 2 — Athlete resolution / active status
- `parsers/fighter.py`: `is_active` is **presence-guarded** — only set when the payload explicitly provides `active` (bool); absent → `None`.
- `FighterDTO.is_active`: `bool | None = None` (unknown).
- `FighterUpsert`: `is_active` handled in `_special_fields`/`_apply_special_fields` — a real bool from ESPN updates the flag; `None` **never overwrites** stored status.

### PHASE 3 — Fighter records
- `FighterDTO`: added full record breakdown fields (`record_summary`, ko/sub/title breakdown, `total_fights`, `win_percentage`, `finish_rate`).
- `provider.py`: `fetch_fighter_record()` returns the full `FighterRecord` (records.py parser) or `None` when unavailable; backward-compatible `fetch_fighter_records()` kept.
- `jobs/fighter.py`: per-fighter records fetched with bounded concurrency and attached to the DTO.
- `FighterUpsert`: persists the breakdown into the **`fighter_records`** table (idempotent via unique fighter_id); **never resets stored records when data is unavailable** (None fields skipped).

### PHASE 4 — Historical events
- `parsers/ranking.py`: `parse_winning_fight_ref()` extracts (league, event_id, competition_id) from a winningFight competition ref; `extract_winning_fight_refs()` collects them.
- `provider.py`: `fetch_winning_fight_refs(league)` walks ranking categories.
- **New job `ESPN_HistoricalEventSyncJob`** (EntityType.HISTORICAL_EVENT): winningFight refs → deduplicated (league, event) hooks → fetch `events/{id}` + embedded competitions **under each hook's own league slug** → upsert via existing `EventUpsert` + `CompetitionUpsert`. Bounded (`ESPN_MAX_HISTORICAL_EVENTS`, default 200), env-gated (`ESPN_HISTORICAL_EVENTS`, default on).
- `types.py`/`plan.py`/`dependency.py`/`sync.py`: new EntityType, `FullSyncPlan` extended (after RANKING), `HistoricalEventsPlan`, dependency declaration, engine registry.

### PHASE 5 — Athlete eventlog
- **New parser `parsers/eventlog.py`** (probe-verified shape): `events.items[] → {event, competition, competitor}` refs; per-item **league slug** extracted (mvp/ufc/bellator/k1...). Parsed refs carry (league, event_id) only — no unused ID fields.
- `provider.py`: `fetch_eventlog_hooks()` — bounded (`ESPN_EVENTLOG_MAX_FIGHTERS`, default 50), content-dependent (empty logs skipped).
- `jobs/historical_event.py`: when `ESPN_EVENTLOG_ENABLED=1`, samples fighters from the DB and merges eventlog hooks into the historical discovery set (deduplicated).

### PHASE 6 — Statistics
- **Migration 006** `statistics_career`: `statistics.competitor_id` NOT NULL → NULL; partial unique index on `(fighter_id, category, label) WHERE competitor_id IS NULL`.
- `db/models/core.py`: `Statistic.competitor_id` nullable.
- `StatisticsUpsert`: career stats (empty `competition_external_id`) persist keyed by `(fighter_id, category, label)` with NULL competitor; per-fight stats unchanged (competitor-scoped).
- `jobs/statistics.py`: actually fetches career stats per fighter (bounded: `ESPN_STATS_MAX_FIGHTERS`, default 200) with bounded concurrency; **never fabricates** (absent stats → no rows).

### PHASE 7 — Performance / cache / retry
- Rate: **3.0 rps** (envelope 2–5), burst **6**, `max_concurrency` **6** (research 4–8).
- Client: response cache + in-flight dedup + canonicalization + metrics.
- Retry behavior verified unchanged-correct: 429/5xx/network retried with backoff; **400/404 not retried** (permanent failures).
- `ProviderCapabilities`: `rate_limit_rps=3.0`, cursor comment corrected to page-based.

### PHASE 8 — Tests
- `tests/unit/test_espn_discovery.py` (30 tests): rate envelope, ofc slug, env override, cache canonicalization/hit/miss/disabled, in-flight dedup, athlete-ID extraction, winningFight ref parsing (dedup + no-crash), eventlog parsing (probe shape, empty, dedup), full records parser, **plan wiring** (FullSyncPlan/HistoricalEventsPlan validate against DEPENDENCY_MAP; no cycles).
- `tests/integration/test_espn_records_and_stats.py` (12 tests): records → `fighter_records` table, idempotency, **no-reset-on-unavailable**, is_active update + None-no-overwrite, career stats persist (NULL competitor), career idempotency + update, discovery job resolves IDs + attaches records + window bounds.
- `tests/api/test_next_fight.py`: fixed time-drift (hardcoded 2026-08-08 dates → relative `_days_from_now`) — pre-existing flakiness, unrelated to ESPN integration.

### PHASE 9 — Documentation reconciliation
- `config.py`: ofc slug, rate envelope comments, sync-league scope, global listing.
- `ESPN_ENDPOINT_CATALOG.md`: offset→page pagination; 48→49 leagues; records/statistics now-wired; winningFight + eventlog discovery; upcoming-only events caveat; hidden-profile discovery; rate/request-efficiency section (13); matrix expanded (18 rows).
- `providers/registry.py`: one-championship → ofc comment.
- `sync/types.py`: capabilities corrected.

## 5. Why each change was necessary

Every change traces to a research fact (see §1/§3): the three historical discovery hooks (winningFight, eventlog, records) were defined-but-unwired, the write path silently zeroed records and skipped career stats, discovery was UFC-only while the research proved a 38k reachable census, and the rate config exceeded the measured safe envelope. Changes preserve the existing architecture — no provider/engine/upsert replaced, no new framework, no mobile changes, no research-workspace changes.

## 6. Research evidence → change map
| Change | Evidence |
|---|---|
| winningFight historical chain | ENDPOINT_GUIDE.md, HISTORICAL_COVERAGE_REPORT.md, FINAL_ENDPOINT_CATALOG.json (47 hooks) |
| eventlog | ENDPOINT_GUIDE.md (P0, CONTENT_DEPENDENT), live probes p19/p21 |
| records flow | FINAL_NUMBERS.md, parsers/records.py prior dead code, catalog claims vs code |
| global listing + rosters discovery | FINAL_NUMBERS.md (38,014 census), HIDDEN_SURFACES_REPORT.md |
| page pagination | probe-proven (already implemented T05; docs corrected) |
| ofc slug | FROZEN.md |
| rate 2–5 rps / 4–8 workers | PERFORMANCE_FINAL_REPORT.md |

## 7. Endpoint families implemented / deferred / ignored
- **Implemented (new/changed)**: global athlete listing, league rosters (multi), athlete profile (ID-driven), athlete records (full breakdown), athlete statistics (career), athlete eventlog, events detail (historical), competitions (historical), competitors (via competition upsert), status (historical FINAL), rankings (winningFight hooks).
- **Deferred**: `athletes/{id}/ranks` (content-dependent, ranked athletes only), season/types traversal (breadth expansion), linescores (non-essential), `competitors/{id}/statistics` per-fight wiring (content-dependent; career wired now), remaining P1 families.
- **Ignored / NOT APPLICABLE**: odds (product excludes betting), teams (vestigial), core v3 MMA (404), site v1 (403), sport dictionaries (404), other non-MMA-app endpoint families.

## 8. How athlete discovery works now
Global flat listing (`/athletes`) ∪ configured league rosters (`/leagues/{slug}/athletes`) → dedup by ESPN ID → cached in `SyncState.checkpoint` → resolved with bounded concurrency (6) → profiles → records per fighter. Hidden profiles (Rousey/DJ/Gracie/Ngannou...) reachable via ranking/event refs are resolved through the same ID path. Resumable across runs; never refetches cached responses within a run; never guesses IDs.

## 9. How historical events work now
`ESPN_HistoricalEventSyncJob` collects winningFight refs from each configured league's rankings, dedups `(league, event_id)` hooks (capped at 200), fetches each event + embedded competitions under the hook's own league slug, and upserts through the existing idempotent `EventUpsert`/`CompetitionUpsert` — no duplicates, no overwrite of newer data. Eventlogs (config-gated) add breadth.

## 10. How fighter records work now
Per fighter (bounded concurrency): `/athletes/{id}/records` → full breakdown → `fighter_records` row (unique per fighter). Empty/unavailable responses produce `None` fields that are skipped — **stored records are never reset**.

## 11. How statistics work now
Career: `/athletes/{id}/statistics` → `StatisticDTO` (career shape) → `statistics` rows keyed by fighter_id with NULL competitor_id (migration 006). Per-fight: competitor-scoped, unchanged path, still content-dependent. Absent stats → no rows (never fabricated).

## 12. Caching
Client response cache: canonicalized URL (path + sorted params) → TTL 300s, 10k entries, oldest-evicted. In-flight dedup: concurrent identical requests share one HTTP call (`deduped` metric). Per-run `RefResolver` cache (existing) for $refs. SyncState checkpoint holds the discovery ID set.

## 13. Retries
3 attempts × backoff 2.0 on 429 (honors Retry-After), 500/502/503/504, DNS/timeout/network errors. 400/404 treated as permanent (no retry, recorded, circuit-breaker counted). Circuit breaker: 5 consecutive failures → 60s cooldown → half-open probe.

## 14. Rate limiting
Token bucket: 3.0 rps sustained, burst 6, bounded concurrency 6 — inside the research's measured 2–5 rps / 4–8 workers envelope.

## 15. Test results
```
pytest tests/                        → 451 passed, 1 skipped (env-gated live)
  new: test_espn_discovery.py        → 30 passed
  new: test_espn_records_and_stats.py → 12 passed
ruff check src/ tests/ sync.py       → All checks passed
mypy src/ sync.py                    → Success: no issues found in 189 source files
migration 006                        → syntax valid; partial-unique-index semantics
```

Code-review pass (post-implementation): reviewer found no blockers; refinements applied — cancellation-safe cache write via done-callback, chunked profile resolution, dropped unused `competition_id` from eventlog refs, honest `params` semantics, and an explicit plan-validation test. All gates re-run green after the pass.

## 16. Live acceptance results
**Not run in this session.** The env-gated live acceptance (`MMA_LIVE_SYNC=1` + bounded `ESPN_MAX_PAGES`, `ESPN_FIGHTER_SYNC_LIMIT`, `ESPN_MAX_HISTORICAL_EVENTS`, `ESPN_STATS_MAX_FIGHTERS`) is ready in `tests/integration/test_sync_live.py`. Bounded live runs are recommended next (see NEXT PHASE) with the production-safe envelope.

## 17. Remaining known limitations
- 38,014 is the largest defensible census, not a mathematical total; "other" league (~27,286 IDs) compositionally unresolved — excluded from active discovery.
- The 33,352 "MMA-likely" cohort is not confirmed MMA; classification should gate any future UI surface.
- Career statistics + eventlogs are content-dependent; athletes without data produce no rows.
- Per-fight competitor statistics not yet wired into competition sync (career wired).
- CLI sync uses the in-memory state store (per-process resume); a DB-backed state store would make the discovery window resumable across processes (SyncState.checkpoint already carries the ID set).
- Season/types traversal deferred — breadth expansion beyond the winningFight/eventlog hooks.

## 18. Recommended future work
1. Bounded live acceptance runs (records, historical events, eventlog, career stats) with the safe envelope.
2. DB-backed `SyncStateStore` for cross-process resume of large discovery windows.
3. Classification gate (confirmed-Mma/MMA-likely) for any future roster UI.
4. Per-fight competitor statistics wiring during FINAL competition sync (content-dependent).
5. Season/types traversal for pre-2016 breadth where product value justifies the request budget.

---

## NEXT PHASE

**Bounded live acceptance + harden resume:**
1. `alembic upgrade head` (006) on the live Postgres; `alembic check` zero-drift.
2. Run `MMA_LIVE_SYNC=1 ESPN_FIGHTER_SYNC_LIMIT=50 ESPN_MAX_HISTORICAL_EVENTS=5 ESPN_STATS_MAX_FIGHTERS=20 pytest tests/integration/test_sync_live.py -v -s` and verify: records populate (`fighter_records` > 0), historical events populate, career stats populate, no duplicate fighters/events/competitions, upcoming events + rankings + profiles + search still work.
3. Verify client metrics (cache hits/dedup/retries) from a live run log.
4. Implement DB-backed state store so large census runs resume across processes.
5. Update `PROJECT_STATUS.md`/`CHANGELOG.md` with this integration (commit stays user-triggered).
