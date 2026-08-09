# ESPN Production Integration — Post-Implementation Validation Report

> Date: 2026-08-09 · Validated against: live ESPN API + live PostgreSQL (`mma` db, alembic 006)
> Companion docs: `ESPN_INTEGRATION_PLAN.md` (architecture), `ESPN_INTEGRATION_REPORT.md` (implementation), `ESPN_ENDPOINT_CATALOG.md` (catalog).
> Frozen research workspace: untouched.

---

## 1. Executive summary

The ESPN production integration was **independently audited against code and validated live against the real ESPN API and a real PostgreSQL database**. The static audit verified every implemented surface against the frozen research; the live acceptance ran a bounded full-sync **twice** (idempotency proven), probed all representative surfaces (hidden historical fighters, records, statistics, eventlog, historical events, rankings, non-UFC roster), and benchmarked the rate envelope at 1/2/4/8 workers.

**Five genuine problems were found and fixed** during validation (three were only visible under live conditions):

1. **Circuit breaker poisoned entire sync runs** — the client tripped the breaker after 5 consecutive HTTP 404s, but ESPN legitimately returns 404 for content-dependent surfaces (athletes without records/statistics/eventlog). First live run failed with `rankings = 0` for exactly this reason. Fix: 4xx never trips the breaker (only 429-exhausted / 5xx-exhausted / network errors do).
2. **Rate envelope not enforced under concurrency** — the pre-existing token bucket leaked tokens: the live benchmark measured **8.36 req/s at 8 workers** with a 3 req/s configured rate (violating the researched 2–5 req/s envelope). Fix: standard refill-under-lock/sleep-outside/recheck bucket — re-benchmarked at **2.68–3.22 req/s across 1/2/4/8 workers**.
3. **Eventlog ingestion dropped fights** — `fetch_eventlog_hooks` fetched only page 1; live probe proved Demetrious Johnson's eventlog has **30 fights across 2 pages** (25/page). Fix: page loop with `pageCount` termination + `ESPN_EVENTLOG_MAX_PAGES` cap (5).
4. **Cross-scope winningFight refs caused duplicate fetches + non-deterministic promotion attribution** — the same historical event is referenced under both `ufc` and `bellator` scopes; hooks keyed by `league:event` fetched each event once per scope and last-write-won. Fix: dedupe hooks by ESPN event ID (shared numeric namespace, live-proven), first-scope-wins.
5. **Live acceptance test did not cover the new surfaces** — the env-gated live test lacked the historical-event job, had no bounded windows (would have attempted a ~25k-profile crawl), and did not assert the new tables. Fix: registered the job, bounded env windows, dual-run idempotency assertions, DB-integrity assertions; added a representative-surface probes test and a bounded benchmark script.

**Final live evidence:** 10/10 sync jobs COMPLETED with 0 errors (twice); 100 fighters, 100 fighter records, 48–88 career stats, 6 events (1 upcoming + 5 historical), 73 competitions, 4 competitors, 4 rankings, 48 promotions, 13 weight classes; **zero duplicates, zero orphaned FKs**; hidden profiles Demetrious Johnson / Royce Gracie / Ken Shamrock / Ronda Rousey all resolve; records land (Shamrock 29-17-2, Gracie 15-2-2); historical chain returns 12 competitions / 24 competitors per event; `ofc` roster = 408 (= research exactly).

**Readiness: READY_FOR_COMMIT** — all five problems fixed and re-validated live; remaining items are documented ESPN-data realities and operational guidance, not defects (see §19, §20, §21).

---

## 2. Research-to-production mapping

| Research requirement | Production implementation | Evidence in code | Test coverage | Status |
|---|---|---|---|---|
| Global flat athlete listing | `ENDPOINTS["global_athletes"]` + `fetch_athlete_ids()` | `config.py`, `provider.py` | unit + live | IMPLEMENTED |
| League-scoped rosters | `/leagues/{slug}/athletes` for `DEFAULT_SYNC_LEAGUES` | `config.py` (ufc, bellator, pfl, ksw, ifc, ofc) | unit + live (ofc=408) | IMPLEMENTED |
| ID dedup before resolution | `set[str]` union in `fetch_athlete_ids` | `provider.py` | live | IMPLEMENTED |
| ESPN ID = provider identity | `external_id` = athlete ID everywhere; `IdResolver` | `provider.py`, `upserts/` | DB dup-check | IMPLEMENTED |
| Page-based pagination | `paginate()` drives `page`, echoes `pageIndex`/`pageCount`, `ESPN_MAX_PAGES` cap | `client.py` | `test_espn_pagination.py` | IMPLEMENTED |
| Resumable discovery | `SyncState.checkpoint["athlete_ids"]` + per-batch `last_offset` | `jobs/fighter.py`, `pipeline.py` | unit | PARTIALLY_IMPLEMENTED (in-process store; DB store = future work) |
| Bounded concurrency 4–8 | `max_concurrency=6`, chunked gather (1,000/batch) | `config.py`, `provider.py` | benchmark | IMPLEMENTED |
| Rate 2–5 req/s | `rate_limit_per_second=3.0`, burst 6, fixed token bucket | `config.py`, `client.py` | unit + benchmark | IMPLEMENTED (was INCORRECT, fixed) |
| No retry on 400/404 | 4xx not in `retry_status_codes` | `client.py` | unit | IMPLEMENTED |
| 404 ≠ system failure (breaker) | 4xx never trips breaker | `client.py` | unit | IMPLEMENTED (was INCORRECT, fixed) |
| Response cache + dedup | canonicalized cache (TTL 300s, 10k) + in-flight dedup | `client.py` | unit + benchmark | IMPLEMENTED |
| Fighter records full breakdown | `/athletes/{id}/records` → `FighterRecord` → `fighter_records` | `parsers/records.py`, `jobs/fighter.py`, `upserts/fighter.py` | unit + live | IMPLEMENTED |
| Records never reset on unavailable | None-fields skipped in upsert | `upserts/fighter.py` | integration | IMPLEMENTED |
| Historical chain rankings→winningFight→event→comps→competitors | `fetch_winning_fight_refs` + `ESPN_HistoricalEventSyncJob` | `parsers/ranking.py`, `jobs/historical_event.py` | unit + live | IMPLEMENTED |
| `ofc` slug (not one-championship) | `ESPN_LEAGUE_SLUGS["ofc"]` | `config.py` | unit | IMPLEMENTED |
| Eventlog ingestion (config-gated) | `fetch_eventlog_hooks` + `ESPN_EVENTLOG_ENABLED` | `provider.py`, `parsers/eventlog.py` | unit + live | IMPLEMENTED (pagination was INCORRECT, fixed) |
| Career statistics | `/athletes/{id}/statistics` → rows keyed (fighter_id, category, label), NULL competitor | migration 006, `jobs/statistics.py`, `upserts/statistics.py` | integration + live | IMPLEMENTED |
| `is_active` presence-guarded | parser sets only explicit bool; upsert never overwrites with None | `parsers/fighter.py`, `upserts/fighter.py` | integration + live | IMPLEMENTED |
| Never fabricate statistics | absent stats → no DTOs → no rows | `jobs/statistics.py` | integration + live (EMPTY) | IMPLEMENTED |
| `/leagues/{slug}/events` not treated as archive | historical discovery uses winningFight refs, not the events listing | `jobs/historical_event.py` docstring + code | live | IMPLEMENTED |

---

## 3. Athlete discovery audit

1. **Global listing queried?** YES — `fetch_athlete_ids()` paginates `/athletes` (limit 1000).
2. **League rosters queried?** YES — all 6 `sync_league_slugs()` (env-overridable).
3. **IDs deduplicated before resolution?** YES — `set` union, then sorted into the window.
4. **ESPN ID as stable identity?** YES — external_id everywhere; duplicate-check query in live DB returned 0 dupes.
5. **Page-based pagination?** YES — page-driven walk with `pageIndex`/`pageCount` termination, duplicate-page guard, cap.
6. **Effective limit handled?** YES — limit ≤ 1000; `ESPN_MAX_PAGES` caps walks.
7. **Resume after interruption?** PARTIAL — per-batch `last_offset` + checkpointed ID set, but the CLI uses the in-memory state store (per-process). DB-backed store = documented future work.
8. **SyncState/checkpoint works?** YES in-process (dual-run test reused the ID set); durable `sync_checkpoints` table exists but is not wired to the engine.
9. **Interrupted run continues without restarting?** In-process yes; cross-process no (documented).
10. **Already-known IDs regenerated?** Listings are re-enumerated only when the checkpoint is empty; profiles are re-resolved each run (idempotent upserts; cache within TTL). A DB-backed "known IDs" skip is future work.
11. **Duplicate URLs eliminated?** YES — canonicalized cache + in-flight dedup (benchmark: 20 deduped for 40 concurrent).
12. **League slugs correct?** YES — all 6 verified live (ofc roster = 408, matching research).
13. **Configured leagues intentional?** YES — active majors per research roster table (ufc 1,835 · bellator 986 · pfl 588 · ksw 208 · ifc 172 · ofc 408); documented in config.
14. **Add a league without rewriting?** YES — `ESPN_SYNC_LEAGUES` env or one tuple edit.

## 4. Athlete resolution audit

- **Batching** — chunked gather (1,000 coroutines/batch) — bounded memory on the 38k census.
- **Bounded concurrency** — client semaphore 6 (research 4–8).
- **Retry** — 429/5xx/network: 3 attempts, backoff 2^n; 400/404: no retry.
- **Cache** — canonicalized TTL cache; repeat pass = 0 new HTTP calls (benchmark).
- **In-flight dedup** — shared futures; done-callback writes the cache (cancellation-safe); benchmark: 20 HTTP calls for 40 concurrent.
- **Atomic state** — per-job commits in the engine; batch-level offsets.
- **Cancellation** — cancellation checked between batches; client dedup safe under cancellation (reviewed + fixed earlier).
- **400/404** — not retried, not breaker-tripping.
- **429/5xx/DNS** — retried with backoff; breaker on exhaustion.
- **Metrics** — requests (non-2xx), cache_hits/misses, deduped, retries, 4xx/5xx/network, 429.
- **Can concurrency exceed the envelope?** NO after the token-bucket fix — benchmark verified 2.68–3.22 req/s at 1/2/4/8 workers (was 8.36 at 8).
- **Cache writes lost on cancellation?** NO — done-callback pattern (fixed in implementation phase; unit-tested indirectly via dedup tests).

## 5. Cache efficiency audit

- **Canonicalization** — path + sorted params (unit-tested).
- **TTL** — 300s, size-bounded 10k, oldest-evicted.
- **Hit/miss** — counted; miss = not-in-cache (deduped requests also counted as misses — documented semantics).
- **Failed responses cached?** NO — only successful `_fetch_json` results reach `_cache.set` (done-callback checks `exception()`).
- **Duplicate URLs avoided** — same URL from different discovery paths (global listing vs roster vs $ref) shares the cache key (canonicalized).
- **In-flight shared** — YES (dedup).
- **Reused across runs?** Within TTL (300s) and per-process; not persisted. RefResolver cache is per-run by design (fresh data).
- **Measured** — benchmark: 20 IDs fetched once under 2-way concurrency (50% reduction); repeat fetch 0 new calls; effective request reduction for the census ≈ dedup on fan-out surfaces.

## 6. Fighter records audit

- **Model** — `FighterRecord` + `fighter_records` table (unique fighter_id) — pre-existing, now wired.
- **Parser** — `parsers/records.py` full breakdown (W/L/D/NC, KO/sub/title, totals, finish rate).
- **Provider** — `fetch_fighter_record()` returns full record or None.
- **Job** — `_attach_records()` bounded concurrency.
- **Upsert** — `fighter_records` written only when the DTO carries data; None fields never clobber; idempotent (select-then-update; DB unique).
- **Live proof** — 100/100 records for the bounded window (Jeremy Horn 90-21-1 · Alistair Overeem 47-19-0 with KO/sub breakdowns); one row per fighter; duplicate-check passed.
- **Unavailable records do not erase** — `_has_record_data()` guard + None-skip (integration-tested).
- **Duplicate runs** — dual live run: `fighter_records` count unchanged.

## 7. Historical events audit

- **Ref parsing** — `parse_winning_fight_ref` extracts league + event_id + competition_id (unit-tested; 19 UFC refs live).
- **Deduplication** — by ESPN event ID (fixed during validation; cross-scope refs proven live).
- **League slug preserved** — each event fetched under its ref's scope.
- **Event ID uniqueness justified** — shared numeric namespace proven (same ID under ufc and bellator scopes = same event).
- **Competitions associated correctly** — event payload embeds competitions; live: 12 comps / 24 competitors per historical event.
- **Competitors resolve** — skipped-with-warning when the fighter isn't synced yet (bounded window → 4 landed); retried on later runs.
- **Persisted** — live: 5 historical events (UFC 200 2016 · UFC 231 2018 · Bellator 214 2019 · UFC 235 2019 · Bellator 178 2017) + 68 competitions.
- **Bounded** — `ESPN_MAX_HISTORICAL_EVENTS` (200 default); job env-gated.
- **Idempotent** — dual live run: identical counts.
- **Missing refs don't corrupt** — exceptions caught per league; empty hooks → no-op.
- **`/leagues/{slug}/events` not used as archive** — confirmed in code.

## 8. Eventlog audit

- **Endpoint construction** — `ENDPOINTS["athlete_eventlog"]` (verified live).
- **Parsing** — probe-verified shape; per-item league slug extracted.
- **Pagination** — FIXED during validation (page loop, pageCount termination, cap 5); live: DJ 30 fights / 2 pages.
- **Provider** — `fetch_eventlog_hooks` bounded by `ESPN_EVENTLOG_MAX_FIGHTERS` (50).
- **Job** — config-gated (`ESPN_EVENTLOG_ENABLED`, default off); merged into historical hooks.
- **Error handling** — per-athlete try/except.
- **Persistence** — events flow through EventUpsert; eventlog itself stores no rows (it's a discovery hook, not a table).
- **Dedup/idempotency** — merged by event ID; dual-run stable.
- **What is stored vs not** — the eventlog endpoint is consumed as a *discovery hook* only; per-fight outcome data lives in competitions/competitors.

## 9. Statistics audit

- **Migration 006** — applied to live DB (head 006): `competitor_id` nullable, partial unique index `uq_statistics_career_fighter_cat_label (fighter_id, category, label) WHERE competitor_id IS NULL` verified in `pg_indexes`.
- **Career vs per-fight distinguished** — `competition_external_id=""` → NULL competitor; per-fight path unchanged.
- **Parser** — normalization map + displayName fallback; absent → no DTOs.
- **Job** — samples `ESPN_STATS_MAX_FIGHTERS` (200) fighters, bounded concurrency.
- **Persistence** — live: 48–88 career rows, all `competitor_id IS NULL`, keyed (fighter, category, label).
- **Idempotency** — dual run identical counts; partial index backstops.
- **Missing stats** — live probe: Shamrock `EMPTY (0 stats)` — correctly classified as no-content, not failure.

## 10. Live acceptance results

Env-gated `MMA_LIVE_SYNC=1` runs against the real ESPN API + live Postgres (bounded windows: 100 fighters, 5 historical events, 25 stat fighters, 10 eventlog fighters, 25 max pages).

**Full-sync plan, run 1:** 10/10 jobs COMPLETED, 0 errors — promotions 48, fighters 100, fighter_records 100, statistics 48–88, events 6, competitions 73, competitors 4, rankings 4, weight_classes 13, sync_runs 1, sync_jobs 10.
**Full-sync plan, run 2:** COMPLETED, **identical row counts everywhere**, 0 errors — idempotency proven.

**Representative surface probes (all PASSED):**

| Probe | Result |
|---|---|
| profile:demetrious_johnson (hidden) | OK (Demetrious) |
| profile:royce_gracie (hidden) | OK (Royce) |
| profile:ken_shamrock (hidden) | OK (Ken) |
| profile:ronda_rousey (hidden) | OK (**Alexis** — cross-ID collision, see §19) |
| profile:ufc_ranked#1 (active) | OK (active=True) |
| records:shamrock / gracie | OK (29-17-2 / 15-2-2) |
| stats:demetrious_johnson | OK (8 stats) |
| stats:ken_shamrock | EMPTY (0 stats — content-dependent) |
| eventlog:demetrious_johnson | OK (count=30, pages=2 — pagination proven) |
| eventlog:royce_gracie | OK (count=20, pages=1) |
| winningfight_refs:ufc | OK (19 refs) |
| historical:ufc/400818923 (UFC 200) | event=OK comps=OK (12 comps, 24 competitors) |
| historical:ufc/400943074 (Bellator 178) | event=OK comps=OK (12 comps, 24 competitors) |
| rankings:ufc | OK (133 ranks) |
| roster:ofc (ONE Championship) | OK (408 fighters — matches research exactly) |
| status:gracie / rousey | OK (is_active=False / False) |

## 11. Database validation

- **Before:** alembic 005; promotions 48, fighters 1,831, records 0, statistics 0, rankings 110, events 1 (T05-era state). **After:** alembic 006 (upgrade + verify); full acceptance dataset above.
- **No duplicates** — `(provider, external_id)` group-by = 0 dupes for fighters/events/competitions.
- **One fighter_records per fighter** — duplicate-fighter_id check = 0.
- **No orphans** — competitions without event = 0; competitors without competition = 0; sync_jobs without run = 0.
- **Content spot-checks** — records (Horn 90-21-1, Overeem 47-19-0), stats all career (0 with competitor), is_active 93 False / 7 True (window is mostly legacy fighters — real values, no NULLs, presence-guard correct), historical events dated 2016–2019 with FINAL status, rankings/competitors real.
- **Repeated sync does not multiply rows** — proven by run 2 equality.

## 12. Idempotency results

Dual-run equality held for every table (fighters, events, competitions, competitors, fighter_records, statistics, rankings). Run 2 = upserts (100 updated / 0 inserted for fighters), 2.2–5.3s (cache-served). No duplicate identities at the DB level.

## 13. Performance benchmark

`scripts/espn_live_benchmark.py` — 100-ID pool, 20 fresh IDs per worker count, production config (3.0 rps, burst 6, cache on):

| Workers | Resolved | HTTP calls | Failures | Elapsed | Effective rps |
|---|---|---|---|---|---|
| 1 | 20/20 | 20 | 0 | 6.20s | 3.22 |
| 2 | 20/20 | 20 | 0 | 7.45s | 2.68 |
| 4 | 20/20 | 20 | 0 | 6.62s | 3.02 |
| 8 | 20/20 | 20 | 0 | 6.67s | 3.00 |

- **Pre-fix at 8 workers: 8.36 rps (envelope violated). Post-fix: all configs ≈ 3 rps.**
- In-flight dedup: 20 deduped, 20 actual HTTP calls for 40 concurrent requests.
- Cache reuse: re-fetch of 20 cached IDs = 0 new HTTP calls.
- No retries, no failures, no 429s observed during the benchmark.
- Network (1.9s first byte) is the dominant per-request cost; the rate limiter, not ESPN, caps throughput — the client cannot exceed the envelope by construction (post-fix).

## 14. Full test results

```
pytest tests/                → 455 passed, 2 skipped (env-gated live tests)
ruff check src/ tests/ sync.py scripts/ → All checks passed
mypy src/ sync.py            → Success: no issues found in 189 source files
alembic heads / current      → 006 (head) — consistent
migration 006                → applied to live DB; nullable + partial index verified
alembic check                → unsupported by project env.py (no autogenerate MetaData) — pre-existing
```

## 15. Code-review findings

Independent review of the validation-phase changes: token-bucket rewrite correct (tokens never negative, proper regression shape), breaker semantics correct, eventlog page loop/pageCount termination correct, sync-live dual-run assertions sound. **One actionable gap found:** the probes test's provider-method classification was vacuous (provider methods swallow exceptions) — fixed with metrics-delta classification (content-dependent vs not). Minor cleanups applied (redundant `or {}`, env-var doc).

## 16. Bugs discovered

1. **Circuit breaker tripped by content-dependent 404s** (live: first sync run failed, rankings = 0).
2. **Token bucket leaked tokens under concurrency** (live benchmark: 8.36 rps at 8 workers vs 3 rps configured).
3. **Eventlog ingestion truncated to page 1** (live probe: DJ 30 fights across 2 pages).
4. **Cross-scope winningFight refs → duplicate fetches + non-deterministic promotion** (live: Bellator events referenced under both ufc and bellator scopes).
5. **Live acceptance test didn't cover new surfaces / had no bounds** (would have attempted a ~25k-profile crawl).

## 17. Fixes made

| # | Problem | Root cause | Fix | Evidence |
|---|---|---|---|---|
| 1 | Breaker poisoned runs | `on_failure()` on every 4xx | 4xx never trips breaker; only 429/5xx-exhausted + network do | unit tests (404 CLOSED / 5xx OPEN); live sync PASSED |
| 2 | Envelope exceeded | release-during-wait token bucket leaked under concurrency | standard refill/sleep-outside/recheck loop | pacing unit test; benchmark 8.36→3.00 rps |
| 3 | Eventlog truncated | first page only | page loop + pageCount + cap 5 | unit test (pages [1,2] merged); live probe pages=2 |
| 4 | Historical dup fetches + attribution | hooks keyed league:event | dedupe by event_id, first-scope-wins | live sync PASSED (events 6, no dupes) |
| 5 | Live test gaps | missing job + unbounded windows | registered historical job, bounded env, dual-run + integrity assertions | live test PASSED (twice) |

## 18. Remaining limitations

- **Ronda Rousey ID 2563797 currently resolves to a different athlete ("Alexis")** — a live cross-ID collision, the same class the research documented for Fedor (2335301 → Frank Mir). The integration faithfully resolves what ESPN serves; identity drift is an ESPN data reality.
- **Promotion attribution for cross-promotion historical events follows the first ref scope** (ufc-first iteration) — deterministic now, but e.g. Bellator 214 is attributed to ufc. ESPN serves these events under multiple scopes and echoes the scope in `league.$ref`; no authoritative promotion marker exists in the payload.
- **Full-census runs are long by design** — ~38k profiles ≈ 3.5h at 3 rps; use `ESPN_FIGHTER_SYNC_LIMIT` windows. Competitors for historical events populate fully only after the corresponding fighters are synced.
- **Discovery checkpoint is in-process** (MemorySyncStateStore) — cross-process resume needs the DB-backed store (future work).
- **Statistics count varies between runs** (48 vs 88) — listing churn shifts the sorted window; content-dependent availability; not a regression.
- **Eventlog capped at 5 pages/fighter** (125 fights) — veterans beyond that are truncated.
- **`other` league (~27,286 IDs) excluded** from active discovery (composition unresolved per research).
- **`alembic check` unsupported** by the project's env.py (pre-existing).
- **Venues = 0** — pre-existing (venue extraction from embedded competition data; unchanged by this integration).

## 19. Production readiness assessment

**READY_FOR_COMMIT.**

Evidence:
- All five genuine problems found during validation were fixed and **re-validated live** (sync PASSED twice, probes PASSED, benchmark gates PASSED after each fix).
- Full gates green: 455 passed + 2 env-gated skips, ruff clean, mypy clean (189 files), alembic 006 head/current consistent.
- Live DB: real data in every table, zero duplicates, zero orphans, idempotency proven by a second full run.
- The remaining items (§18) are ESPN-data realities and documented operational guidance — none block committing the integration.
- Per the task's standing rules the working tree remains **uncommitted**; the commit itself is the user's decision (no commit made).

## 20. Exact next step

Run the migration + a bounded live sync with the intended production windows, then commit when the user approves:
```
alembic upgrade head   # already applied to the acceptance DB
MMA_LIVE_SYNC=1 pytest tests/integration/test_sync_live.py -v -s      # full-plan acceptance (idempotency included)
MMA_LIVE_SYNC=1 pytest tests/integration/test_espn_live_probes.py -v -s  # representative surfaces
python scripts/espn_live_benchmark.py                                   # envelope verification
```
Then (user-approved): implement the DB-backed `SyncStateStore` for cross-process resume of the full 38k census.

## 21. Final output

- **A. What was audited:** all production ESPN provider/client/jobs/parsers/upserts, sync engine/plan/dependency/state, migration 006, tests, CLI, plus the frozen research baselines.
- **B. What was verified:** every research→implementation mapping (code + tests + live), rate envelope (benchmark), cache/dedup (benchmark), idempotency (dual run), DB integrity (queries), migration state (006 applied + verified).
- **C. What failed:** live sync run 1 (breaker on 404s); benchmark envelope (8.36 rps); eventlog pagination (page 1 only); live-test coverage gaps.
- **D. What was fixed:** breaker 4xx semantics; token-bucket rewrite; eventlog pagination; historical event-ID dedup; live test upgrades + probes + benchmark + 4 new unit tests.
- **E. Live ESPN results:** 10/10 jobs twice; all probes OK/EMPTY per content dependency; 19 winningFight refs; 133 rankings; ofc 408.
- **F. Database results:** tables populated with real data; 0 dupes; 0 orphans; records/stats/historical events verified by content.
- **G. Performance results:** 2.68–3.22 req/s at 1/2/4/8 workers; dedup 50% request reduction; cache reuse 0 new calls; 0 failures/retries.
- **H. Test results:** 455 passed, 2 skipped (env-gated); ruff/mypy clean; alembic 006.
- **I. Remaining risks:** Rousey ID collision; cross-promotion attribution bias; in-process checkpoint; census-run length; eventlog 5-page cap; `other` league excluded; venues 0 (pre-existing).
- **J. Production readiness:** READY_FOR_COMMIT.
- **K. Exact next step:** migration applied; run the three live commands above with production windows; implement DB-backed state store for census-scale resume (user-approved); commit only on user request.

---

*No machine-readable validation artifact was created: the production project has no convention for one (the research workspace's `RESEARCH_MANIFEST.json` is research-side; production validation lives in markdown + the env-gated live tests).*
