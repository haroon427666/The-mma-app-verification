# PRODUCTION WINDOW 007 — Records Backfill Report (Batch 3)

**Date:** 2026-08-11 (UTC) · **Type:** bounded records-only backfill (batch 3)
**Command:** `PYTHONIOENCODING=utf-8 ESPN_RECORDS_BACKFILL_LIMIT=2000 python sync.py --full --entity records`

---

## 1. Verdict: **PASS**

Batch 3 completed cleanly: `COMPLETED, inserted=1588, updated=0, skipped=412, errors=0`, 670,250 ms (~11.2 min). **2,000 API requests, all HTTP 200 — 0×503, 0×404, 0×429, 0 retries, 0 discovery requests** (breaker never engaged — third consecutive fully-clean records run). The census discovery registry was **not touched** — consumed/pending stayed exactly 12,988 / 25,023.

## 2. Target (unchanged)

Backlog: 3,357 fighters missing `fighter_records` (residual from W006 records-phase gap + genuine ESPN absences). Mechanism: the W007 records-only job (`ESPN_RecordsBackfillJob` → `FighterUpsert.upsert_records`), registry-neutral by construction.

## 3. Baseline (batch 3)

`PRODUCTION_WINDOW_007_RECORDS_BATCH3_BASELINE.json` (2026-08-11T10:05:12Z) — fighters 12,988 · records 9,631 · missing 3,357 · registry 38,011 (12,988 consumed / 25,023 pending) · alembic 008 · HEAD `19a87c7`. All integrity checks 0.

## 4. Execution (batch 3, bounded to 2,000)

- **2,000 API requests** — **0 discovery requests**; every request returned HTTP 200
- Response mix: 2000× HTTP 200, 0× HTTP 404, 0× HTTP 503, 0× HTTP 429, 0 retries
- **1,588 records inserted** (real record payloads) · **412 skipped** (HTTP 200, empty payload — content-dependent absences, per the documented design)
- Registry consumed/pending **unchanged** ✓ (12,988 / 25,023) — registry-neutral invariant held for the third consecutive batch
- Sync run `bda1065a` COMPLETED (670,250 ms ≈ 11.2 min ≈ **3.0 req/s** — inside the validated envelope)
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

## 6. Cumulative quality classification (batches 1–3)

- Successfully backfilled: **3,832** (638 + 1,606 + 1,588); fighter_records 7,387 → **11,219**
- Legitimate absence (HTTP 200, empty payload — officials/placeholders etc.): cumulative **~1,168**
- Operationally missed: **0** this batch (batch 1: ≤10 distinct, 503-related — long since re-probed)
- Still missing after batch 3: **1,769**

## 7. Representatives (spot-check of freshly inserted rows)

External IDs 3099600–3099604 (batch-3 targets, verified directly from `fighter_records`): all real, internally consistent payloads (e.g. 3099600 = 0-1-0/1 fight, 3099603 = 0-3-0/3 fights — `record_summary` matches total_fights). Makhachev / Ngannou / DJ / Rousey / Gracie / Shamrock records untouched (they already had records).

## 8. Performance (batch comparison)

| Metric | W007 batch 1 | W007 batch 2 | W007 batch 3 |
|---|---|---|---|
| limit | 1,000 | 2,000 | 2,000 |
| 503s | 23 (breaker CLOSED, retries absorbed) | **0** | **0** |
| 429s | 0 | 0 | 0 |
| records inserted | 638 | 1,606 | **1,588** |
| yield (inserted/limit) | 63.8% | 80.3% | **79.4%** |
| requests | 1,022 | 2,000 | 2,000 |
| rate | ~3.0 req/s | ~3.0 req/s | ~3.0 req/s |
| elapsed | 5.7 min | 11.1 min | 11.2 min |

Yield holds ≈ 79–80%: the low-ID officials/placeholder band was cleared in batch 1; batches 2–3 probe the main missing cohort where most fighters have real records.

## 9. Known limitation (unchanged, documented)

No persisted "records absent" marker, so known-empty fighters are re-probed on every bounded batch. Optional Phase D absence flag remains not implemented; not required for correctness.

## 10. Files created / modified

Created: `PRODUCTION_WINDOW_007_RECORDS_BATCH3_BASELINE.json` · `PRODUCTION_WINDOW_007_RECORDS_BATCH3_AFTER.json` · `PRODUCTION_WINDOW_007_RECORDS_BATCH3_SYNC_LOG.txt` · this report · `PRODUCTION_WINDOW_007_RECORDS_BATCH3_POST_AUDIT.md`.
Code: **none modified** for batch 3 (batch 1's 5-file minimal change, still uncommitted). Docs updated: `ESPN_PRODUCTION_JOURNEY.md` (appended §19), `ESPN_HANDOFF_STATE.md`.

## 11. Decision gate: **B — continue with another bounded records batch**

Backlog 1,769 (down from 5,601 pre-batch-1; 68% cleared in three bounded runs). Recommendation: **W007 batch 4 — `ESPN_RECORDS_BACKFILL_LIMIT=2000`** (≈11 min). Expect the yield to taper further as the residual set trends toward genuine ESPN absences. Census expansion (C) still waits until the records backlog is resolved.

## 12. Git safety

No staged files · no commit · no push. No code drift beyond batch 1's documented 5 files. DB writes were exclusively the approved bounded backfill.
