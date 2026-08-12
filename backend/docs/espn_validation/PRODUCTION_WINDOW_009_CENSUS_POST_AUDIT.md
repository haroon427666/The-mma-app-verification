# PRODUCTION WINDOW 009 — Census Expansion Post-Audit (Window 2)

**Session:** 2026-08-11 (UTC) · bounded execution + post-audit
**Objective:** Second fighter census window, `ESPN_FIGHTER_SYNC_LIMIT=2000` — continue expanding the fighter population from the durable discovery registry.

## Summary

- **Verdict: PASS.** 2,000 fighters inserted, 1,971 records backfilled (enrichment), 0 errors, **4,000 requests all HTTP 200 — 0×404/429/5xx, 0 retries, breaker never engaged, 0 discovery requests**.
- **Registry advanced exactly +2,000 consumed** (14,988 → 16,988); pending 23,023 → 21,023. Registry total unchanged (38,011).
- **Consumed↔fighter correspondence 100%**: all 16,988 consumed IDs have a persisted fighter row.
- **Zero dead-ends**: 2000/2000 window IDs resolved to real profiles.
- Records behavior: 1,971/2,000 real payloads; 29 empty (content-dependent absences — never faked, never reset).

## Current DB state (post-window 2)

| Table | Count |
|---|---|
| fighters | **16,988** (+2,000) |
| fighter_records | **16,511** (+1,971) |
| fighters missing records | **477** (448 residual untouched + 29 new genuine absences) |
| statistics / rankings / competitors | 399 / 142 / 47 (unchanged) |
| external_ids | **17,343** (+2,000) |
| events / competitions / promotions / weight_classes | 24 / 260 / 48 / 23 (unchanged) |
| registry total / consumed / pending | 38,011 / **16,988** / **21,023** |
| sync_runs | 23 (+1 COMPLETED `ae3f0e63`) |
| alembic | 008 (unchanged) |

Integrity: 0 duplicates (fighters/records/registry/external_ids) · 0 orphans (all FK tables) · 0 NULLs · rankings 142/142 resolve · checkpoints fighter/ranking/records COMPLETED (unchanged) · discovery checkpoints 7/7 COMPLETED (unchanged). HEAD unchanged `19a87c7`.

## HTTP / retry / breaker forensics

| Signal | Count |
|---|---|
| HTTP 200 | 4,000 (2,000 profiles + 2,000 records) |
| HTTP 404 / 429 / 5xx / 503 | 0 / 0 / 0 / 0 |
| retries / backoff | 0 |
| breaker openings | 0 (never engaged) |
| discovery requests | 0 (7/7 walks skipped as COMPLETED) |
| dead-ended consumption | 0 (2000/2000 resolved) |
| terminal shutdown | COMPLETED, clean exit code 0 |

## Cohort quality

Window-2 cohort (created ≥ 11:46:39 UTC) = exactly 2,000 fighters; **1,971 with fighter_records (98.55%)**; 1,947 with profile W/L/D. Spot-checks internally consistent (record_summary ↔ W/L/D ↔ total_fights): Mark Vorgeas 0-1-1/2 · Augusto Mendes 6-2-0/8 (1 KO, 4 subs) · Maxim Divnich 13-3-0/16. Notable real fighters present: Joilton Lutterbach 38-10-0/49 · Julian Erosa 31-14-0/45 · Kevin Holland 29-15-0/45 · Tatsumitsu Wada 25-13-2/41. No fabricated rows.

## Risks / notes

1. **Absence floor grows with census:** 29 new genuine absences in this cohort (~1.45% — slightly higher than window 1's 0.95%; mild taper expected as bands rise). Records backfill remains CLOSED — residual 477 NOT re-probed.
2. **Mode heuristic note:** strategy logged `mode=incremental` (last sync < 4h). The fighter job ignores mode (registry-window-based) — results identical to window 1; no behavioral divergence.
3. **Session timezone note:** DB session timezone is NOT UTC (+5). Audit queries must use explicit `+00`/tz-aware literals (an initial cohort query mislabeled the window boundaries; corrected with tz-aware parameters — no data impact).
4. **No code committed:** W007 5-file drift + all artifacts remain uncommitted per standing instruction. Window 2 added no code.
5. **Records backfill still CLOSED** — untouched this window.

## Decision gate

**STOP — census window 2 complete (PASS).** No further census window, no records rerun, no Phase D, no commit/push without a new explicit decision gate.

## Git safety

No staged/committed/pushed changes. Code drift limited to the 5 documented W007 files. DB writes exclusively the approved single bounded census window.
