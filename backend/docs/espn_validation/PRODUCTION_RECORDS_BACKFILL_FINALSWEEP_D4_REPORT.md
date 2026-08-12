# PHASE D D4 — HISTORICAL ABSENCE CLASSIFICATION BACKFILL · REPORT

> **Phase:** PHASE D D4 (one-time historical classification write) · **Date (UTC):** 2026-08-12 · **Git HEAD:** `19a87c7`
> **Scope:** persist the 1,224 confirmed ESPN record absences as explicit `CONFIRMED_ABSENT` state. **No ESPN requests. No `sync.py`. No registry/discovery. No `fighter_records` fabrication.**

## A. Verdict
**PASS.** Reconciliation derived **exactly 1,224 fighters** (805 pre-W019 floor + 414 batch-probed + 5 final-sweep), every one with **no `fighter_records` row** and **confirmed HTTP-200 empty-payload evidence** from the final sweep (`7852a339`). All 1,224 were inserted as `CONFIRMED_ABSENT` (provider `espn`) in a single transaction; the re-run proved **idempotency (0 new rows)**. All invariants held; all six representatives unchanged.

## B. Execution
| Field | Value |
|---|---|
| Operation | One-time INSERT into `fighter_provider_record_status` (no source-code change; DB write only) |
| Method | `INSERT … ON CONFLICT (fighter_id, provider) DO NOTHING`, single transaction, `executemany` |
| Inserted rows | **1,224** (delta 0 → 1,224) |
| Idempotent rerun | **0 new rows** (verified) |
| Status value | `CONFIRMED_ABSENT` (per approved D4 — the D4 brief's "confirmed_empty" wording maps to the D1–D3 `RecordFetchStatus.CONFIRMED_ABSENT` enum value) |
| Evidence basis | `last_checked_at` = final sweep completion **2026-08-12 08:47:45 UTC** · `last_run_id` = `7852a339-2a20-4ceb-868e-c9888d3a22cd` (verified COMPLETED in `sync_runs`) · `last_http_status` = 200 (final sweep: 1512×200, 0 errors — FINALSWEEP POST_AUDIT §8) |

## C. Provenance breakdown
| Provenance | Count | Basis |
|---|---|---|
| `CENSUS_FLOOR` | **805** | pre-W019 genuine-absence floor (`external_id` < 5238639); officials/referees/placeholder profiles; re-probed at 0% yield in every sweep |
| `BACKFILL_BATCH` | **414** | post-W019 genuine empties probed by records-backfill **Batches 1–2** (`0f8d2a74` +95 / `66dc4dfa` +1,781); placeholder clusters (Brian Tyler, Mongi Zitouni, Ludovic Dandine, Christopher Edgehill, Ziad Harb, Solimar Miranda, Jason Tatlow) + singleton empties |
| `FINAL_SWEEP` | **5** | 5350060 Giovanna Scano · 5350061 Vincent Dudley · 5369837 Sarah Cotton · 5386478 Dejan Tesic · 5386479 Vladimir Badrljica — confirmed empty by the final sweep |
| **Total** | **1,224** | = 805 + 419 (414 + 5), matching `FINALSWEEP_AFTER.json` |

> **Honesty note:** the 414's exact per-ID Batch-1-vs-Batch-2 attribution is not derivable from the artifacts (no per-request batch logs retained), so a single documented cohort value `BACKFILL_BATCH` is used — no invented attribution.

## D. DB invariants (verified before and after)
| Metric | Before | After |
|---|---|---|
| fighters | 38,011 | 38,011 |
| fighter_records | 36,787 | 36,787 |
| fighters missing records | 1,224 | 1,224 |
| external_ids / weight_classes / rankings / statistics / competitors / events / competitions / promotions | 38,368 / 25 / 142 / 399 / 47 / 24 / 260 / 48 | unchanged |
| alembic | 009 | 009 |

## E. Registry invariant — HELD
`sync_discovered_athletes` total **38,011** · consumed **38,011** · pending **0** — untouched (no discovery, no registry writes; census not altered).

## F. Status-table audit (post-write)
- rows = **1,224** · provider=`espn` AND status=`CONFIRMED_ABSENT` = **1,224**
- duplicate `(fighter_id, provider)` identities = **0**
- orphan status rows (no fighter) = **0** · NULL required fields = **0**
- provenance counts: CENSUS_FLOOR 805 · BACKFILL_BATCH 414 · FINAL_SWEEP 5

## G. Test results (post-backfill, relevant surface)
**34 passed / 0 failed** — `test_record_fetch_outcome.py` + `test_record_fetch_status.py` + `test_espn_records_and_stats.py` + `test_migration_coverage.py`. Confirms: real records untouched · status rows idempotent · registry untouched · no fake `fighter_records` · no status duplicates.

## H. Representatives (6/6 — unchanged)
Makhachev **28-1-0** · Ngannou **19-3-0** · DJ **25-4-1** · Rousey **13-2-0** · Gracie **15-2-2** · Shamrock **29-17-2**.

## I. Artifacts
- `PRODUCTION_RECORDS_BACKFILL_FINALSWEEP_D4_BASELINE.json` (pre-D4 snapshot; status table 0 rows)
- `PRODUCTION_RECORDS_BACKFILL_FINALSWEEP_D4_AFTER.json` (post-D4 audit; 1,224 rows)
- `PRODUCTION_RECORDS_BACKFILL_FINALSWEEP_D4_REPORT.md` (this file)
- `PRODUCTION_RECORDS_BACKFILL_FINALSWEEP_D4_POST_AUDIT.md`
- `PRODUCTION_RECORDS_BACKFILL_FINALSWEEP_D4_RECONCILIATION.json` (derivation manifest)

## J. Git state / next gate
HEAD `19a87c7` · 0/0 ahead/behind · **nothing staged/committed/pushed**. **D5 (API exposure) NOT EXECUTED — requires a new explicit approval gate.** D6 docs limited to the D4 completion state.
