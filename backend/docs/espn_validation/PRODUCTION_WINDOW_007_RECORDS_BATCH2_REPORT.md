# PRODUCTION WINDOW 007 — Records Backfill Report (Batch 2)

**Date:** 2026-08-11 (UTC) · **Type:** bounded records-only backfill (batch 2)
**Command:** `PYTHONIOENCODING=utf-8 ESPN_RECORDS_BACKFILL_LIMIT=2000 python sync.py --full --entity records`

---

## 1. Verdict: **PASS**

Batch 2 completed cleanly: `COMPLETED, inserted=1606, updated=0, skipped=394, errors=0`, 667,873 ms (~11.1 min). **2,000 API requests, all HTTP 200 — 0×503, 0×404, 0×429, 0 retries** (cleanest records run so far; breaker never engaged). The census discovery registry was **not touched** — consumed/pending stayed exactly 12,988 / 25,023.

## 2. Target (unchanged from batch 1)

Backlog: 4,963 fighters missing `fighter_records` (W006 records-phase gap + pre-existing). Mechanism: the Phase 1 records-only job (`ESPN_RecordsBackfillJob` → `FighterUpsert.upsert_records`), registry-neutral by construction.

## 3. Baseline (batch 2)

`PRODUCTION_WINDOW_007_RECORDS_BATCH2_BASELINE.json` — fighters 12,988 · records 8,025 · missing 4,963 · registry 38,011 (12,988 consumed / 25,023 pending) · alembic 008 · HEAD `19a87c7`. All integrity checks 0.

## 4. Execution (batch 2, bounded to 2,000)

- **2,000 API requests** — **0 discovery requests**; every request returned HTTP 200
- Response mix: 2000× HTTP 200, 0× HTTP 404, 0× HTTP 503, 0× HTTP 429, 0 retries
- **1,606 records inserted** (real record payloads) · **394 skipped** (HTTP 200, empty payload — content-dependent absences, per the documented design)
- Registry consumed/pending **unchanged** ✓ (12,988 / 25,023) — the backfill is registry-neutral by construction
- Sync run `8ae5866c` COMPLETED (667,873 ms ≈ 11.1 min ≈ **3.0 req/s** — inside the validated envelope)
- `records` checkpoint row: COMPLETED (unchanged)

## 5. Post-backfill audit — all ✓

| Check | Result |
|---|---|
| duplicate fighter_records | **0** |
| duplicate fighters / external_ids / registry rows | **0 / 0 / 0** |
| orphan fighter_records / rankings / statistics / competitors / external_ids | **0 / 0 / 0 / 0 / 0** |
| NULL provider/external_id | **0** |
| unresolved rankings | **0 (142/142 resolve)** |
| registry consumed/pending | **12,988 / 25,023 — unchanged** |
| fighters (identity) | 12,988 — unchanged (no new/duplicated fighters) |
| external_ids | 13,343 — unchanged |

## 6. Cumulative quality classification (batches 1 + 2)

- Successfully backfilled: **2,244** (638 + 1,606)
- Legitimate absence (HTTP 200, empty payload — officials/placeholders): cumulative **~756**
- Operationally missed: **0** this batch (batch 1: ≤10 distinct, 503-related — all re-probed, remain queued)
- Still missing after batch 2: **3,357**

## 7. Representatives (spot-check of freshly inserted rows)

External IDs 2431357 / 2431358 / 2431360 (batch-2 targets, verified directly from `fighter_records`):

| external_id | W-L-D | KO/TKO | Sub | Fights |
|---|---|---|---|---|
| 2431357 | 24-8-1 | 13 | 7 | 33 |
| 2431358 | 3-3-0 | 2 | 0 | 6 |
| 2431360 | 23-7-0 | 6 | 7 | 30 |

Real, internally consistent record payloads (`record_summary` matches W-L-D breakdown). Makhachev / Ngannou / Rousey / Gracie / Shamrock records untouched (they already had records).

## 8. Performance (batch comparison)

| Metric | W007 batch 1 | W007 batch 2 |
|---|---|---|
| limit | 1,000 | 2,000 |
| 503s | 23 (breaker CLOSED, retries absorbed) | **0** |
| 429s | 0 | 0 |
| records inserted | 638 | **1,606** |
| yield (inserted/limit) | 63.8% | **80.3%** |
| requests | 1,022 | 2,000 |
| rate | ~3.0 req/s | ~3.0 req/s |
| elapsed | 5.7 min | 11.1 min |

Yield improved 63.8% → 80.3%: batch 2 cleared past the low-ID officials/placeholder band into the main missing cohort. The residual ~394 absent responses are distributed across the probed band — consistent with census non-MMA content.

## 9. Known limitation (unchanged, documented)

No persisted "records absent" marker, so known-empty fighters are re-probed on every bounded batch. Not observed to waste this batch's budget (no leading absence tail anymore); a Phase D absence flag remains optional.

## 10. Files created / modified

Created: `PRODUCTION_WINDOW_007_RECORDS_BATCH2_BASELINE.json` · `PRODUCTION_WINDOW_007_RECORDS_BATCH2_AFTER.json` · `PRODUCTION_WINDOW_007_RECORDS_BATCH2_SYNC_LOG.txt` · this report · `PRODUCTION_WINDOW_007_RECORDS_BATCH2_POST_AUDIT.md`.
Code: **none modified** for batch 2 (batch 1's 5-file minimal change, still uncommitted). Docs updated: `ESPN_PRODUCTION_JOURNEY.md` (appended §17), `ESPN_HANDOFF_STATE.md`.

## 11. Decision gate: **B — continue with another bounded records batch**

Backlog 3,357 (down from 5,601 pre-batch-1; 40% cleared in two bounded runs). The mechanism is proven safe — this batch recorded zero transient failures. Recommendation: **W007 batch 3 — `ESPN_RECORDS_BACKFILL_LIMIT=2000`** (≈11 min). The residual set is dominated by the officials/placeholder floor; expect the yield to taper. Census expansion (C) waits until the records backlog is resolved.

## 12. Git safety

No staged files · no commit · no push. No code drift beyond batch 1's documented 5 files. DB writes were exclusively the approved bounded backfill.
