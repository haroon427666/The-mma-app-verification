# Production Window 001 — Controlled ESPN Sync Run Report

- **Run ID:** `eb70f094-8420-4741-b53d-b1d5ef4cc4bc`
- **Date (UTC+5):** 2026-08-10, 15:58:18 → 16:11:59
- **Duration:** 820,613 ms (~13.7 min)
- **Mode:** FULL (all 10 jobs), provider `espn`, via existing CLI `backend/sync.py --full`
- **Status:** COMPLETED — 2,369 inserted / 90 updated / 729 skipped / **0 errors**
- **Evidence artifacts (this folder):** `PRODUCTION_WINDOW_001_BASELINE.json` (pre-run), `PRODUCTION_WINDOW_001_AFTER.json` (post-run), `PRODUCTION_WINDOW_001_SYNC_LOG.txt` (preserved console log)

## 1. Run parameters

| Parameter | Value | Source / default |
|---|---|---|
| `ESPN_FIGHTER_SYNC_LIMIT` | `1000` | Explicit env override |
| `ESPN_EVENTLOG_ENABLED` | `0` (disabled) | Default — no `eventlog` job row created, 0 eventlog payloads |
| `ESPN_MAX_PAGES` | 200 (default) | Unchanged — discovery pagination safety cap |
| `ESPN_MAX_HISTORICAL_EVENTS` | 200 (default) | Unchanged |
| `ESPN_STATS_MAX_FIGHTERS` | 200 (default) | Unchanged |
| No `MMA_LIVE_SYNC` | never set | Live sync never invoked |

No code changes were made during the run. The database was not touched outside `sync.py`'s own writes; baseline/after captures used read-only connections.

## 2. Before / After row counts

| Table | BEFORE | AFTER | Delta | Notes |
|---|---|---|---|---|
| fighters | 100 | 1000 | **+900** | Exactly the 1000-window (900 new) |
| fighter_records | 100 | 999 | +899 | 1 fighter has no record row (no-fight/debut athlete) |
| statistics | 48 | 368 | +320 | 200 sampled × ~1.8 records |
| events | 6 | 24 | +18 | 1 (event job) + 17 (historical) |
| competitions | 73 | 260 | +187 | 5 (competition job) + 182 (historical) |
| competitors | 4 | 35 | +31 | All from historical-event upserts |
| rankings | 4 | 12 | +8 | Ranking job reports inserted=12 → table rebuilt per category (delete+insert pattern) |
| weight_classes | 13 | 17 | +4 | **weight_class job is a no-op (0ms)** — new classes created implicitly by fighter upserts |
| broadcasts | 1 | 3 | +2 | |
| promotions | 48 | 48 | 0 | All skipped (already synced) |
| venues | 0 | 0 | 0 | ESPN supplies no venue data (payload missing — known mock-warning) |
| external_ids | 240 | 1349 | +1109 | fighter provider-ID mappings |
| sync_runs / sync_jobs | 2 / 20 | 3 / 30 | +1 / +10 | One COMPLETED run, all 10 jobs COMPLETED |
| sync_checkpoints | 0 | 0 | 0 | No mid-run resumption |

All deltas reconcile exactly with per-job upsert tallies (e.g., historical_event inserted=230 = 17 events + 182 competitions + 31 competitors).

## 3. Data integrity

- **Duplicate provider external IDs:** fighters 0, events 0, competitions 0
- **Orphans:** 0 across competitions→events, competitors→competitions, fighter_records→fighters, statistics→fighters, sync_jobs→runs, external_ids→fighters
- **NULL checks:** 0 on fighters (is_active, first/last name), events (status/name/promotion), statistics (fighter/category/label), competitions (event_id), competitors (competition_id)
- **Provider purity:** 100% ESPN — 0 non-ESPN fighters/events/competitions

## 4. Performance

| Job | Duration | Inserted | Notes |
|---|---|---|---|
| fighter (incl. records) | 696,907 ms (85%) | 1,799 | 1,000 profiles + 999 records + discovery pagination ≈ 2,000+ requests |
| statistic | 65,453 ms | 320 | |
| ranking | 32,344 ms | 12 | |
| promotion | 15,890 ms | 0 | |
| historical_event | 6,281 ms | 230 | |
| broadcast / event / competition | 2,625 / 703 / 297 ms | 2 / 1 / 5 | |
| venue / weight_class | 0 ms | 0 | no-op jobs |

Total ≈ 2,500 ESPN requests over 820s ≈ **3 req/s sustained** (within the client's rate limit).

## 5. Monitoring observations (from preserved log)

- **0 errors, 0 retries, 0 HTTP 429s, 0 network-retry warnings** across ~2,500 requests — the rate limiter worked with zero throttling events.
- 461 `Competitor skipped: fighter <id> not yet synced` warnings — expected: upcoming-event/historical competitors whose fighter rows are outside the window. These 461 IDs **include every current P4P-ranked athlete** (see §6).
- Cache invalidation ran for 6 API prefixes (`mma:api:*`) after the run; Redis was reachable (client initialized); 1 cache-miss fallback logged at startup.
- Log lines reference the failed-capture artifacts? No — one log preamble line captures the PowerShell `[ERROR]`-style wrapper text from the pipe (Unicode console workaround); the sync itself logged 0 errors (`[ERROR]` count = 0 in the preserved log body).

## 6. Research reconciliation (live ESPN cross-check)

Verified against the live ESPN API (`sports.core.api.espn.com`) **after** the run:

- **DB ↔ ESPN name match (in-window representatives):** `2335653` = Ken Shamrock ✓ (DB "Ken Shamrock" = ESPN "Ken Shamrock"); `2335697` = Royce Gracie ✓. Sync fidelity confirmed.
- **Correction to earlier acceptance-phase research:** the representative ID set is *not* the current-champion set. Live lookup shows `2512089` = Demetrious Johnson, `2563796` = Ronda Rousey, `3933168` = Francis Ngannou, `3949584` = Alexander Volkanovski — these are real athletes but **not** 2026 champions. The IDs are valid; the earlier champion attribution was erroneous and is retracted here.
- **Ranked-fighter coverage:** the 9 P4P-ranked athletes returned by ESPN's own UFC rankings endpoint (Usman `3088812`, Adesanya `4285679`, Ngannou `3933168`, Volkanovski `3949584`, Blachowicz `2506250`, Poirier `2506549`, Figueiredo `4189320`, Miocic `2504951`, Oliveira `2504169`) are **all OUTSIDE the window** — the exact IDs that produced "not yet synced" skips.
- **Window coverage:** in-window band = external IDs `2,085,811`–`2,488,768` (lowest-ID slice of the ~38k athlete listing). This covers mostly older-generation athletes (e.g., Cain Velasquez `2335654`, Cheick Kongo `2335655`) and early-edition ESPN IDs. **Current-era and ranked fighters (ID range ~2.5M–5.1M) are not covered by a 1,000-fighter window.**
- **Upstream staleness (documented, not a defect):** ESPN's MMA rankings still show a 2022-era champion set (Usman/Adesanya/Ngannou era). The `rankings` table (12 rows) faithfully mirrors this stale upstream data.

## 7. Risks / follow-ups

1. **Coverage gap is structural:** `ESPN_FIGHTER_SYNC_LIMIT` sorts by ID and takes the lowest N, so increasing it helps only slightly (current champs are 5M-range IDs; full listing ≈ 38k). Recommend: (a) priority fetch of ranked-fighter IDs (`rankings → ranks[].athlete`), and/or (b) dedicated "by external_id list" sync for the active roster, before a full un-windowed run.
2. **`api_calls` column is 0/untracked** in `sync_runs`/`sync_jobs` — request counts must be estimated from logs. Cheap observability win.
3. **weight_class job is a no-op (0 ms)** — classes are only materialized implicitly through fighter upserts; document or fold into the fighter job.
4. **ranking table rebuilds each run** (delete+insert semantics visible in counts) — confirm this is intended idempotency behavior for the ranking upsert.
5. **1,000 fighters ↔ 999 records:** one athlete (debut/no-fights) legitimately has no record row; treat as expected, verify per-athlete on demand.
6. **Eventlog path remains untested in production** (disabled by default, per design). When enabled in a future window, its volume is the primary scale risk and should be validated with a small window first.

## 8. Conclusion

The production window completed cleanly: window honored (exactly 1,000 fighters), zero errors, zero rate-limit events, zero integrity violations, perfect row-count reconciliation, faithful name-level fidelity vs live ESPN for in-window representatives, and a precisely quantified coverage gap (ranked/current-era fighters outside the low-ID window) with a concrete remediation plan.
