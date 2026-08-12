# RECORDS BACKFILL — BATCH 2 (LIMIT=3000) REPORT

> **Phase:** TASK 2 (records backfill) · **Batch:** 2 (final remaining sweep)
> **Date (UTC):** 2026-08-11 19:48:36 → 20:05:21 · **Git HEAD:** `19a87c7`

## A. Verdict
**PASS — Batch 2 completed cleanly (exit 0).** +1,781 real records inserted. **3,000/3,000 HTTP 200 · 0 retries · 0 breaker events · 0 connection errors · 0 errors** — another fully clean run. Registry untouched (registry-neutral invariant held, 6th production confirmation). Overall yield 59.4% is **explained, not a failure**: the ascending sweep re-probed the **805-ID genuine-absence floor (0% yield by design)** plus the **Mongi Zitouni/Ludovic Dandine placeholder cluster** that extends into the W019 band (genuine empty payloads). **Cumulative Task 2: +1,876 records (3,388 → 1,512 missing).**

## B. Run ID / execution
| Field | Value |
|---|---|
| Run ID | `66dc4dfa-b6e7-44b7-b8a7-b71efa449a47` |
| Status | COMPLETED · exit 0 |
| Command | `PYTHONIOENCODING=utf-8 ESPN_RECORDS_BACKFILL_LIMIT=3000 python sync.py --full --entity records` |
| Duration | 1,005,469 ms (~16.8 min) |
| Result counters | inserted **1,781** · updated 0 · skipped 1,219 · errors **0** |

## C. Before → After → Delta (live DB, verified)
| Entity | Before | After | Δ |
|---|---|---|---|
| fighter_records | 34,718 | **36,499** | **+1,781** |
| fighters missing records | 3,293 | **1,512** | **−1,781** |
| fighters | 38,011 | 38,011 | **0** (backfill never touches fighters) |
| external_ids / weight_classes / rankings / statistics / competitors / events / competitions / promotions | 38,368 / 25 / 142 / 399 / 47 / 24 / 260 / 48 | unchanged | 0 |

## D. Target cohort
Ascending sweep of the 3,000 lowest-ID missing fighters: **805-ID genuine floor (re-probed, 0% yield)** + **2,195 of the 2,488 deferred**. The floor sorts first, so the 3000-ID window covered only 2,195 deferred — **293 deferred (highest-ID tail, up to 5386479) remain unprobed** and would need a final small sweep.

## E. Records results
- **1,781/3,000 real payloads** (log: `Records backfill: 1781/3000 returned real record payloads (1219 empty/404/unavailable)`)
- Deferred portion yield **81.1%** (1,781/2,195); 414 deferred genuine empties (placeholder cluster + content-dependent)
- Sample inserted records internally consistent (8-0-0 · 7-1-0 · 9-3-0 · 0-0-1 · 0-1-0 …) — no fabricated values
- Empty responses → **no row**; stored values never reset

## F. HTTP / retry / breaker
- **3,000 requests (all `/records`)** — **3000×HTTP 200 · 0×404 · 0×429 · 0×503 · 0 other 5xx · 0 connection errors · 0 retries · 0 breaker events · 0 errors · 0 tracebacks**
- **0 discovery requests** — discovery untouched (registry-neutral by construction)

## G. Performance
**~2.98 req/s** (3,000 / 1,005.5 s) · **~16.8 min**. Envelope = token bucket 3 rps / burst 6 / concurrency 6 (defaults).

## H. Integrity (fresh live audit — all ✓)
dupes fighters/records/registry/ext_ids **0** · orphans records/rankings/statistics/competitors/ext_ids **0** · NULL provider/external_id **0** · unresolved rankings **0 (142/142)** · consumed↔fighter 100%.

## I. Representatives (6/6 — untouched)
Makhachev **28-1-0** · Ngannou **19-3-0** · DJ **25-4-1** · Rousey **13-2-0** · Gracie **15-2-2** · Shamrock **29-17-2**.

## J. Checkpoint / discovery state
checkpoints **3/3 COMPLETED** (unchanged) · discovery **7/7 COMPLETED** (unchanged) · alembic **008**.

## K. Artifacts
- `PRODUCTION_RECORDS_BACKFILL_BATCH2_BASELINE.json`
- `PRODUCTION_RECORDS_BACKFILL_BATCH2_SYNC_LOG.txt` (3,029 lines)
- `PRODUCTION_RECORDS_BACKFILL_BATCH2_AFTER.json`
- `PRODUCTION_RECORDS_BACKFILL_BATCH2_REPORT.md`
- `PRODUCTION_RECORDS_BACKFILL_BATCH2_POST_AUDIT.md`

## L. Documentation
Journey + handoff updated to reflect Batch 2 (Task 2 progress). Historical records untouched.

## M. Git state
HEAD `19a87c7` · 0/0 ahead/behind origin/main · nothing staged/committed/pushed · W007 code drift untouched · mobile/planning/research untouched · no code changes.

## N. Remaining records
**1,512 fighters lack `fighter_records`** = **805 genuine-absence floor** (permanent, 0% yield) + **707 post-W019** (≈414 probed-empty genuine empties + **293 unprobed tail**). Cumulative Task 2: deferred backlog **2,580 → 293**.

## O. Next decision gate
**STOP.** Batch 2 complete and verified. **A final small sweep (LIMIT≈300) to probe the remaining 293-deferred tail is NOT auto-authorized** — requires a new explicit decision gate. No fabrication, no Phase D (absence flag — would eliminate floor re-probes), no commit/push, no additional production operation without approval.
