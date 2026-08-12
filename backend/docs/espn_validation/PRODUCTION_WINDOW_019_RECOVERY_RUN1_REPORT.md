# PRODUCTION WINDOW 019 — RECOVERY RUN R1 (Census Completion) — **PARTIAL (breaker trip)**

**Date:** 2026-08-11 (UTC) · **Operation:** W019 recovery — census completion (Run R1 of 2)
**Command:** `ESPN_FIGHTER_SYNC_LIMIT=2000 python sync.py --full --entity fighter` (env: `PYTHONIOENCODING=utf-8 PYTHONUTF8=1`)
**DB context:** production = PostgreSQL 18 `localhost:5432/mma` (authoritative; `backend/mma_stats.db` is a 0-byte forensic placeholder — never production, untouched).

---

## 1. Verdict: **PASS-WITH-DEVIATION — PARTIAL RECOVERY (do NOT treat as census-complete)**

R1 was the first of two planned recovery runs (census completion, then records completion). It **consumed 904 of the 1,347 pending IDs** — including **ALL 324 deferred W019 IDs** (5310951+), which was the primary recovery objective. A burst of **40 connection-level ESPN errors** at 18:28:23 UTC (5 consecutive failures) tripped the circuit breaker `CLOSED → OPEN` at 18:28:47 UTC; the healthy-gate then **left 443 IDs queued/unconsumed** (`Fighter window: 443 ids unresolved during an unhealthy fetch (system signals detected) — left queued for retry, NOT consumed`). **The records phase never ran (0 /records requests).** Crash-safety held exactly as designed: 0 integrity violations, consumed↔fighter 100%. **Per protocol: STOP — no auto-retry, no auto-R2; continuation requires a new explicit decision gate.**

## 2. Preflight (completed before R1)

- **17/17 PASS** — live DB matched W019 AFTER exactly; no sync process running; `mma_stats.db` 0 bytes.
- **ESPN health probe (read-only, 18:22 UTC): ALL 200** — 3× consecutive rounds on next-pending 5310951 (profile + records), 10 deferred tail IDs, 4 records endpoints, control Makhachev 3332412, `/leagues`. 0×503.
- Implementation review (from source): window = ascending filter on unconsumed IDs → 324 deferred retried first; records attach in-run; records backlog via `--entity records` (registry-neutral); LIMIT=2000 self-bounds to the 1,347 remaining. Recovery plan captured in `PRODUCTION_WINDOW_019_RECOVERY_BASELINE.json`.

## 3. Execution (actual)

- **Window selected:** 1,347 IDs (ALL pending: 324 deferred + 1,023 beyond) — `next_window(2000)` returned the full remaining set.
- **904 profiles resolved** (band start 5310951 → …) · **443 IDs left queued** after breaker trip (first unconsumed now **5362434**).
- **0 records requests** — records phase never executed (breaker OPEN at attach time → all fetches rejected client-side).
- Registry: consumed 36,664 → **37,568 (+904)**; pending 1,347 → **443 (−904)**; total 38,011 unchanged.
- Sync run `7e0d0a87` COMPLETED (337,626 ms ≈ 5.6 min ≈ **2.68 req/s**); inserted=904 · updated 0 · skipped 0 · errors 0.
- Checkpoints fighter/ranking/records COMPLETED (unchanged); discovery 7/7 skipped (14 lines); alembic 008.

## 4. Breaker event — fully documented (connection-level, NOT HTTP 5xx)

Unlike W019 (44× HTTP 503) and W016–W018 (transient HTTP 503s recovered by retry), **R1's failures were connection-level**: 40× `ESPN connection error: .` (empty exception message — keep-alive/reset-class) at 18:28:23–18:28:47 UTC, with **0 HTTP 5xx/503/429/404 on the wire** (904/904 HTTP 200). The client's exception-retry path (connect errors → 1s/2s/4s backoff) exhausted 5 consecutive failures and the breaker opened:

- 18:28:47 — `Circuit breaker: CLOSED → OPEN (5 consecutive failures)`
- After OPEN: 1,336× `Circuit breaker is OPEN. Retry in 60s` · 443× `Athlete profile failed (<id>): Circuit breaker is OPEN`
- 18:28:50 — `Fighter window: 443 ids unresolved during an unhealthy fetch (system signals detected) — left queued for retry, NOT consumed` · `Fighter window: 904 resolved of 1347 ids`
- **0 records requests were ever made** — the job bailed at the profile stage.

First queued IDs (verified still unconsumed): 5362434 · 5362444 · 5362446 · 5362447 · 5362448 · 5362460–5362466.

## 5. Post-window audit — all ✓ (integrity intact)

| Check | Result |
|---|---|
| duplicate fighters / fighter_records / external_ids / registry | **0 / 0 / 0 / 0** |
| orphan fighter_records / rankings / statistics / competitors / external_ids | **0 / 0 / 0 / 0 / 0** |
| NULL provider/external_id | **0** |
| unresolved rankings | **0 (142/142 resolve)** |
| consumed registry IDs with a persisted fighter row | **37,568 / 37,568 (100%)** ✓ |
| registry total | 38,011 — unchanged |

## 6. Before → after / deltas (ACTUAL)

| Table | Before | After | Δ |
|---|---|---|---|
| fighters | 36,664 | **37,568** | **+904** (target was +1,347) |
| fighter_records | 34,183 | **34,183** | **0** (records phase never ran) |
| fighters missing records | 2,481 | **3,385** | +904 (all new fighters lack records) |
| statistics / rankings / competitors | 399 / 142 / 47 | 399 / 142 / 47 | 0 |
| external_ids | 37,021 | **37,925** | **+904** (0 weight classes) |
| events / competitions / promotions | 24 / 260 / 48 | 24 / 260 / 48 | 0 |
| weight_classes | 25 | 25 | 0 |
| registry total | 38,011 | 38,011 | 0 |
| registry consumed | 36,664 | **37,568** | **+904** |
| registry pending | 1,347 | **443** | **−904** |

## 7. Representative verification (all 6 PASS — untouched)

| Fighter | ext_id | record_summary |
|---|---|---|
| Islam Makhachev | 3332412 | 28-1-0 |
| Francis Ngannou | 3933168 | 19-3-0 |
| Demetrious Johnson | 2512089 | 25-4-1 |
| Ronda Rousey | 2563796 | 13-2-0 |
| Royce Gracie | 2335697 | 15-2-2 |
| Ken Shamrock | 2335653 | 29-17-2 |

## 8. Cohort quality (R1 partial cohort, verified live)

- Cohort size: **exactly 904 fighters** (all from the ascending window; 0 dead-ends in the resolved set).
- **All 324 deferred W019 IDs (5310951+) recovered and consumed** — objective 1 of the recovery is substantially met.
- All 904 new fighters lack `fighter_records` (records phase not executed — deferred work, NOT genuine absences).
- No fabricated rows; content consistent with the documented placeholder pattern at the tail.

## 9. Performance

| Metric | W019 | R1 (actual) |
|---|---|---|
| limit | 2,000 | 2,000 (self-bounded to 1,347 pending) |
| profiles fetched | 1,720 | 904 (resolved; 443 rejected by breaker) |
| records fetched | 0 | **0** |
| requests | 1,720 | **904** |
| failure mode | 44× HTTP 503 (persistent) | **40× connection-level errors (no HTTP 5xx)** |
| breaker | 1 trip (CLOSED → OPEN) | **1 trip (CLOSED → OPEN)** |
| 404 / 429 / other 5xx / tracebacks / errors | 0 | 0 / 0 / 0 / 0 / 0 |
| rate | ~2.96 req/s | ~2.68 req/s |
| elapsed | 9.7 min | 5.6 min |

The healthy-gate + breaker behaved exactly as designed (W005-run-1 / W019 precedent): partial consumption, 0 integrity violations, queued IDs preserved for a later run.

## 10. Files created / modified

Created: `PRODUCTION_WINDOW_019_RECOVERY_BASELINE.json` · `PRODUCTION_WINDOW_019_RECOVERY_RUN1_CENSUS_SYNC_LOG.txt` (2,339 lines) · `PRODUCTION_WINDOW_019_RECOVERY_RUN1_AFTER.json` · this report · `PRODUCTION_WINDOW_019_RECOVERY_RUN1_POST_AUDIT.md`.
Code: **none modified**. W019 artifacts untouched (historical, preserved).

## 11. Decision gate: **STOP — partial recovery; continuation requires a NEW explicit approval**

**R1 consumed 904/1,347.** Registry: **37,568 consumed / 443 pending** (next **5362434**). **All 324 deferred W019 IDs recovered.** Remaining census work: 443 IDs. **Records:** 1,676 W019 + 904 R1 = 2,580 fighters lack `fighter_records` (deferred, not genuine absences; genuine floor 805). **No auto-retry, no auto-R2 (records backfill), no further production operation, no commit/push** without a new explicit decision gate.

## 12. Git safety

No staged files · no commit · no push. No code drift beyond the documented W007 5-file set. DB writes exclusively the approved bounded census run (partial). `backend/mma_stats.db` verified untouched (0 bytes).
