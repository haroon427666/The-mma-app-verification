# PRODUCTION WINDOW 007 — Records Backfill Report (Batch 4)

**Date:** 2026-08-11 (UTC) · **Type:** bounded records-only backfill (batch 4)
**Command:** `PYTHONIOENCODING=utf-8 ESPN_RECORDS_BACKFILL_LIMIT=2000 python sync.py --full --entity records`

---

## 1. Verdict: **PASS**

Batch 4 completed cleanly: `COMPLETED, inserted=1340, updated=0, skipped=429, errors=0`, 590,616 ms (~9.8 min). **1,769 API requests, all HTTP 200 — 0×503, 0×404, 0×429, 0 retries, 0 discovery requests** (breaker never engaged; fourth consecutive fully-clean records run). The census discovery registry was **not touched** — consumed/pending stayed exactly 12,988 / 25,023.

**Notable:** the remaining backlog (1,769) was SMALLER than the LIMIT=2000 budget, so the job exhausted the entire missing set in this run — every fighter lacking `fighter_records` was probed. The 429 residual are the genuine-absence floor (probed, returned empty payloads).

## 2. Target

Backlog: 1,769 fighters missing `fighter_records` (residual from W006 records-phase gap + genuine ESPN absences). Mechanism: the W007 records-only job (`ESPN_RecordsBackfillJob` → `FighterUpsert.upsert_records`), registry-neutral by construction.

## 3. Baseline (batch 4)

`PRODUCTION_WINDOW_007_RECORDS_BATCH4_BASELINE.json` (2026-08-11T10:28:03Z) — fighters 12,988 · records 11,219 · missing 1,769 · registry 38,011 (12,988 consumed / 25,023 pending) · alembic 008 · HEAD `19a87c7`. All integrity checks 0.

## 4. Execution (batch 4 — exhausted the full backlog)

- **1,769 API requests** (backlog < LIMIT=2000 → all candidates processed) — **0 discovery requests**; every request returned HTTP 200
- Response mix: 1769× HTTP 200, 0× HTTP 404, 0× HTTP 503, 0× HTTP 429, 0 retries
- **1,340 records inserted** (real record payloads) · **429 skipped** (HTTP 200, empty payload — content-dependent absences)
- Registry consumed/pending **unchanged** ✓ (12,988 / 25,023) — registry-neutral invariant held for the 4th consecutive batch
- Sync run `4754f082` COMPLETED (590,616 ms ≈ 9.8 min ≈ **3.0 req/s** — inside the validated envelope)
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

## 6. Cumulative quality classification (batches 1–4)

- Successfully backfilled: **5,172** (638 + 1,606 + 1,588 + 1,340); fighter_records 7,387 → **12,559**
- Legitimate absence (HTTP 200, empty payload — officials/placeholders etc.): cumulative **~1,597**
- Operationally missed: **0** this batch (batch 1: ≤10 distinct, 503-related — long since re-probed)
- Still missing after batch 4: **429** — the residual is the genuine ESPN absence floor (officials/placeholders/empty payloads)

## 7. Representatives (spot-check of freshly inserted rows)

External IDs 3142505–3142694 (batch-4 targets, verified directly from `fighter_records`): all real, internally consistent payloads (e.g. 3142663 = 0-2-0/2 fights, 3142664 = 3-7-0/10 fights, 3142694 = 0-2-1/3 fights — `record_summary` matches total_fights). Makhachev / Ngannou / DJ / Rousey / Gracie / Shamrock records untouched (they already had records).

## 8. Performance (batch comparison)

| Metric | Batch 1 | Batch 2 | Batch 3 | Batch 4 |
|---|---|---|---|---|
| limit | 1,000 | 2,000 | 2,000 | 2,000 (backlog 1,769) |
| 503s | 23 (breaker CLOSED) | **0** | **0** | **0** |
| 429s | 0 | 0 | 0 | 0 |
| records inserted | 638 | 1,606 | 1,588 | **1,340** |
| yield (inserted/probed) | 63.8% | 80.3% | 79.4% | **75.7%** |
| requests | 1,022 | 2,000 | 2,000 | 1,769 |
| rate | ~3.0 req/s | ~3.0 req/s | ~3.0 req/s | ~3.0 req/s |
| elapsed | 5.7 min | 11.1 min | 11.2 min | 9.8 min |

## 9. Known limitation — now the decisive factor

No persisted "records absent" marker exists. Batch 4 probed the **entire** remaining backlog; the 429 residuals returned empty payloads (genuine absences). **A future batch would re-probe exactly these 429 known-empties with 0% new-record yield** — pure request waste (~7 min, 429 requests). Options: (a) STOP records backfill — the backlog is at the genuine-absence floor; (b) Phase D (approved small migration adding a persisted absence flag) to record absences once and stop re-probing; (c) a single small "mop-up" rerun for completeness, accepting the waste. Not required for correctness.

## 10. Files created / modified

Created: `PRODUCTION_WINDOW_007_RECORDS_BATCH4_BASELINE.json` · `PRODUCTION_WINDOW_007_RECORDS_BATCH4_AFTER.json` · `PRODUCTION_WINDOW_007_RECORDS_BATCH4_SYNC_LOG.txt` · this report · `PRODUCTION_WINDOW_007_RECORDS_BATCH4_POST_AUDIT.md`.
Code: **none modified** for batch 4 (batch 1's 5-file minimal change, still uncommitted). Docs updated: `ESPN_PRODUCTION_JOURNEY.md` (appended §20), `ESPN_HANDOFF_STATE.md`.

## 11. Decision gate: **A — records backlog resolved (at the absence floor); STOP further batches unless Phase D is approved**

Backlog 429 (down from 5,601 pre-batch-1; **92.3% cleared** in four bounded runs). Further batches re-probe known-empties (0% yield). Census expansion (C) remains on hold pending a separate explicit decision gate.

## 12. Git safety

No staged files · no commit · no push. No code drift beyond batch 1's documented 5 files. DB writes were exclusively the approved bounded backfill.
