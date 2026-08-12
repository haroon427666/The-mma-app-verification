# PRODUCTION WINDOW 019 — Census Expansion Report (Window 12) — **PARTIAL (breaker trip)**

**Date:** 2026-08-11 (UTC) · **Type:** bounded fighter census window (registry-consuming)
**Command:** `ESPN_FIGHTER_SYNC_LIMIT=2000 python sync.py --full --entity fighter` (env: `PYTHONIOENCODING=utf-8 PYTHONUTF8=1` for console capture)
**DB context:** production = PostgreSQL 18 `localhost:5432/mma` (authoritative; `backend/mma_stats.db` is a 0-byte placeholder from the earlier forensic probe — never production, untouched).

---

## 1. Verdict: **PASS-WITH-DEVIATION — PARTIAL WINDOW (do NOT treat as a full 2,000-ID window)**

The run completed with **exit 0 / COMPLETED / 0 errors**, but **consumed only 1,676 of the 2,000 target IDs**: a persistent upstream ESPN 503 episode (NOT the transient type seen in W016–W018) triggered the **circuit breaker (CLOSED → OPEN, 5 consecutive failures)** and the job's healthy-gate **left 324 IDs queued/unconsumed** (`Fighter window: 324 ids unresolved during an unhealthy fetch (system signals detected) — left queued for retry, NOT consumed`). **The records phase never ran** (0 `/records` requests; all 1,676 new fighters lack records). The crash-safety mechanism worked exactly as designed (only resolved IDs consumed, 0 integrity violations, consumed↔fighter 100%) — **this is the documented W005-run-1 precedent**, not a data-quality failure. **Per protocol: STOP — no automatic re-run; completing the remaining 1,347 pending IDs requires a new explicit decision gate.**

## 2. Target

Twelfth bounded census window: next 2,000 **unconsumed** registry IDs in ascending `external_id` order. Prior state: 38,011 discovered IDs, 34,988 consumed, 3,023 pending (window 11 completed `7caf5f7b`).

## 3. Baseline (window 12)

`PRODUCTION_WINDOW_019_CENSUS_BASELINE.json` (2026-08-11T17:57:53Z) — fighters 34,988 · fighter_records 34,183 · missing 805 · registry 38,011 (34,988 consumed / 3,023 pending) · external_ids 35,345 · weight_classes 25 · alembic 008 · HEAD `19a87c7`. All integrity checks 0. Preflight 17/17: live counts matched W018 AFTER exactly · next 5238639 · discovery 7/7 · checkpoints 3/3 · reps 6/6 · no sync process · mma_stats.db 0 bytes.

## 4. Execution (actual)

- **Window selected:** 2,000 IDs (`5238639…` ascending, deterministic `next_window` filter)
- **1,720 profile requests; 0 records requests**
- **1,676 fighters inserted** (band 5238639 → 5311038) · **0 fighter_records inserted** (records phase never executed)
- **324 IDs left queued/unconsumed** (`unhealthy fetch (system signals detected)`) — 44 persistent-503 failures + ~280 never attempted after breaker OPEN
- Registry: consumed 34,988 → **36,664 (+1,676)**; pending 3,023 → **1,347 (−1,676)**
- Sync run `09d84b8d` COMPLETED (580,809 ms ≈ 9.7 min ≈ **2.96 req/s**)
- Checkpoints: fighter/ranking/records COMPLETED (unchanged); discovery 7/7 skipped (14 lines); alembic 008

## 5. Breaker event — fully documented (upstream 503 episode, persistent)

At 23:07:25–23:07:50 local (18:07 UTC) the window tail (IDs 5310951+) hit **persistent "Backend fetch failed" 503s** on **profile** GETs — unlike the W016/W017/W018 transient episodes, **retries did NOT recover them** (44 retry attempts, 0 recoveries):

- 23:07:42 — `Circuit breaker: CLOSED → OPEN (5 consecutive failures)`
- After OPEN: `Athlete profile failed (<id>): Circuit breaker is OPEN. Retry in 60s` for the remaining IDs
- 23:07:50 — `Fighter window: 324 ids unresolved during an unhealthy fetch (system signals detected) — left queued for retry, NOT consumed` · `Fighter window: 1676 resolved of 2000 ids`
- **0 records requests were ever made** — the job bailed at the profile stage
- Run still completed with 0 errors (the engine records the partial resolution as COMPLETED; unresolved IDs are NOT consumed)

Affected IDs (examples, verified still unconsumed): 5310951 · 5310982 · 5310983 · 5310990 · 5311036–5311043 · 5311046–5311052 · 5311063 · 5311270 · 5311360.

## 6. Post-window audit — all ✓ (integrity intact)

| Check | Result |
|---|---|
| duplicate fighters / fighter_records / external_ids / registry | **0 / 0 / 0 / 0** |
| orphan fighter_records / rankings / statistics / competitors / external_ids | **0 / 0 / 0 / 0 / 0** |
| NULL provider/external_id | **0** |
| unresolved rankings | **0 (142/142 resolve)** |
| consumed registry IDs with a persisted fighter row | **36,664 / 36,664 (100%)** ✓ |
| registry total | 38,011 — unchanged |
| discovery checkpoints | 7/7 COMPLETED — unchanged |
| checkpoints (fighter/ranking/records) | 3/3 COMPLETED — unchanged |

## 7. Before → after / deltas (ACTUAL)

| Table | Before | After | Δ |
|---|---|---|---|
| fighters | 34,988 | **36,664** | **+1,676** (target was +2,000) |
| fighter_records | 34,183 | **34,183** | **0** (records phase never ran) |
| fighters missing records | 805 | **2,481** | +1,676 (all new fighters lack records) |
| statistics | 399 | 399 | 0 |
| rankings | 142 | 142 | 0 |
| competitors | 47 | 47 | 0 |
| external_ids | 35,345 | **37,021** | **+1,676** (2,000 fighters, 0 weight classes) |
| events / competitions / promotions | 24 / 260 / 48 | 24 / 260 / 48 | 0 |
| weight_classes | 25 | 25 | 0 |
| registry total | 38,011 | 38,011 | 0 |
| registry consumed | 34,988 | **36,664** | **+1,676** |
| registry pending | 3,023 | **1,347** | **−1,676** |

## 8. Representative verification (all 6 PASS — untouched)

| Fighter | ext_id | record_summary |
|---|---|---|
| Islam Makhachev | 3332412 | 28-1-0 |
| Francis Ngannou | 3933168 | 19-3-0 |
| Demetrious Johnson | 2512089 | 25-4-1 |
| Ronda Rousey | 2563796 | 13-2-0 |
| Royce Gracie | 2335697 | 15-2-2 |
| Ken Shamrock | 2335653 | 29-17-2 |

## 9. Cohort quality (window-12 partial cohort, verified live)

- Cohort size: **exactly 1,676 fighters** (created 18:07:50 UTC bulk-stamp) — **all 1,676 WITHOUT fighter_records** (records phase not executed — not genuine absences; the records backfill/completion is deferred and requires approval).
- Window band (consumed): 5238639 → 5311038. First IDs continue the W018 placeholder cluster ("Mongi Zitouni"/"Ludovic Dandine" roster entries, 5238639+) — content consistent with the documented placeholder pattern.
- Sample profiles resolved correctly (Mongi Zitouni 5238639 · Ludovic Dandine 5238640 · Mongi Zitouni 5238641 …). No fabricated rows.
- **No dead-ends in the resolved set** (1,676/1,676 profiles resolved to real rows).

## 10. Performance

| Metric | W018 | W019 (actual) |
|---|---|---|
| limit | 2,000 | 2,000 |
| profiles fetched | 2,000 | 1,720 (1,676 resolved + 44 persistent 503s) |
| records fetched | 1,897 real | **0** (records phase not executed) |
| requests | 4,018 | **1,720** |
| non-200 | 18×503 (recovered) | **44×503 (NOT recovered — persistent upstream episode)** |
| breaker | never engaged | **1 trip (CLOSED → OPEN)** |
| 404 / 429 / other 5xx / tracebacks / errors | 0 | 0 / 0 / 0 / 0 / 0 |
| rate | ~3.0 req/s | ~2.96 req/s |
| elapsed | 22.4 min | 9.7 min |

The healthy-gate + breaker behaved exactly as designed (W005-run-1 precedent): partial consumption, 0 integrity violations, queued IDs preserved for a later run.

## 11. Files created / modified

Created: `PRODUCTION_WINDOW_019_CENSUS_BASELINE.json` · `PRODUCTION_WINDOW_019_CENSUS_AFTER.json` · `PRODUCTION_WINDOW_019_CENSUS_SYNC_LOG.txt` (3,823 lines) · this report · `PRODUCTION_WINDOW_019_CENSUS_POST_AUDIT.md`.
Code: **none modified**. Docs updated: `ESPN_PRODUCTION_JOURNEY.md` (appended §33), `ESPN_HANDOFF_STATE.md`.

## 12. Decision gate: **STOP — partial window; completion requires a NEW explicit approval**

**W019 consumed 1,676 of its 2,000-ID budget.** Registry: 36,664 consumed / **1,347 pending** (324 queued from this window's band + 1,023 beyond). **All 1,676 new fighters lack records** (records phase not executed). Records backfill remains CLOSED; Phase D unimplemented. **No automatic re-run, no completion run, no W020-equivalent, no records rerun, no discovery expansion, no commit/push** without a new explicit decision gate. Next pending ID: **5310951**.

## 13. Git safety

No staged files · no commit · no push. No code drift beyond the documented W007 5-file set. DB writes exclusively the approved bounded census run (partial). `backend/mma_stats.db` verified untouched (0 bytes, unmodified).
