# PRODUCTION WINDOW 007 — Records Backfill Post-Audit (Batch 2)

**Session:** 2026-08-11 (UTC) · bounded execution + post-audit
**Objective:** W007 records backfill batch 2 (2,000 fighters) — continue clearing the W006 records-phase gap.

## Summary

- **W007 batch 2 verdict: PASS.** 1,606 records backfilled, 394 skipped (content-dependent absences), 0 errors, **0×503/404/429, 0 retries — all 2,000 requests returned HTTP 200**. Registry untouched (12,988/25,023 unchanged).
- **Yield improved to 80.3%** (batch 1: 63.8%) — the run cleared past the low-ID officials/placeholder band into the main missing cohort.
- **Cumulative:** 2,244 records backfilled across both batches (from 7,387 to 9,631 rows); missing set reduced 5,601 → 3,357.

## Current DB state (post-batch 2)

| Table | Count |
|---|---|
| fighters | 12,988 (unchanged) |
| fighter_records | **9,631** (+1,606) |
| fighters missing records | **3,357** (−1,606) |
| statistics / rankings | 399 / 142 (unchanged) |
| external_ids | 13,343 (unchanged) |
| registry total / consumed / pending | 38,011 / **12,988** / **25,023** (unchanged ✓) |
| sync_runs | 19 (+1 COMPLETED `8ae5866c`) |
| alembic | 008 (unchanged) |

Integrity: 0 duplicates (records/fighters/registry/external_ids) · 0 orphans (all FK tables) · 0 NULLs · rankings 142/142 resolve · `records` checkpoint COMPLETED. HEAD unchanged `19a87c7`.

## Risks / notes

1. **Re-probe waste (low this batch):** known-empty fighters no longer dominate the probe order; 394 absent responses were spread through the band. Phase D absence marker still optional.
2. **Census content caveat (unchanged):** residual missing set (~3,357) is expected to be dominated by officials/placeholders; yield will taper on subsequent batches.
3. **No code committed:** batch 1's 5-file minimal change + this documentation remain uncommitted per standing instruction. Batch 2 added no code.

## Decision gate

**B — continue bounded records batches** (next: `ESPN_RECORDS_BACKFILL_LIMIT=2000`). Census expansion (C) waits until the records backlog is resolved. D (absence marker) optional.

## Git safety

No staged/committed/pushed changes. Code drift limited to the 5 documented W007 files from batch 1. No production window (census) executed.
