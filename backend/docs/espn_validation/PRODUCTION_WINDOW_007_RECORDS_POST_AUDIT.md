# PRODUCTION WINDOW 007 — Records Backfill Post-Audit

**Session:** 2026-08-11 (UTC) · observation + bounded execution + documentation
**Objective:** W007 records backfill batch 1 (1,000 fighters) — resolve the W006 records-phase gap.

## Summary

- **W007 verdict: PASS.** Batch 1: 638 records backfilled, 362 skipped (content-dependent absences), 0 errors, 0×429, breaker never opened. Registry untouched (12,988/25,023 unchanged).
- **Architecture gap found and closed (minimally):** no records-only mechanism existed; added `EntityType.RECORDS` + `ESPN_RecordsBackfillJob` + `FighterUpsert.upsert_records` (record-only writes — a partial DTO through `upsert_batch` would clobber fighter profiles). Ruff/mypy/imports clean; focused tests 49/49.
- **Classification after giving ESPN a clean opportunity:** of 5,601 missing-record fighters, batch 1 probed 1,000 → **638 genuine records**, **~352 genuine absences** (low-ID census band is dominated by officials/placeholders like Herb Dean, John McCarthy, "Opponent TBA"), **≤10 operationally missed** (503s, remain queued).

## Current DB state (post-W007)

| Table | Count |
|---|---|
| fighters | 12,988 |
| fighter_records | **8,025** (+638) |
| fighters missing records | **4,963** (−638) |
| statistics / rankings | 399 / 142 |
| external_ids | 13,343 |
| registry total / consumed / pending | 38,011 / **12,988** / **25,023** (unchanged ✓) |
| sync_runs | 18 (+1 COMPLETED `9d04653c`) |
| alembic | 008 |

Integrity: 0 duplicates (records/fighters/registry/external_ids) · 0 orphans (all FK tables) · 0 NULLs · rankings 142/142 resolve · `records` checkpoint COMPLETED.

## Risks / notes

1. **Re-probe waste:** known-empty fighters lead the ordering and are re-probed each batch (~36% waste). Optional Phase D: persisted absence marker (migration). Not a blocker.
2. **Census content caveat (unchanged):** the registry contains non-MMA athletes (officials etc.); they resolve to fighters but yield no records — expected, not an error.
3. **Rousey ID collision (unchanged):** still documented, unresolved by design.
4. **No code committed:** the 5-file minimal change + this documentation are uncommitted per standing instruction.

## Decision gate

**B — continue bounded records batches** (next: `ESPN_RECORDS_BACKFILL_LIMIT=1000`). Census expansion (C) waits until the records backlog is resolved. D (absence marker) optional efficiency improvement for a future phase.

## Git safety

No staged/committed/pushed changes. Code drift limited to the 5 documented W007 files. Mobile/planning/session/research untouched. No production window (census) executed.
