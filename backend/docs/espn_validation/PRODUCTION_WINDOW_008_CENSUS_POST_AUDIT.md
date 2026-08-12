# PRODUCTION WINDOW 008 — Census Expansion Post-Audit (Window 1)

**Session:** 2026-08-11 (UTC) · bounded execution + post-audit
**Objective:** First fighter census window, `ESPN_FIGHTER_SYNC_LIMIT=2000` — expand the fighter population from the durable discovery registry.

## Summary

- **Verdict: PASS.** 2,000 fighters inserted, 1,981 records backfilled (enrichment), 0 errors, **4,000 requests all HTTP 200 — 0×404/429/5xx, 0 retries, breaker never engaged, 0 discovery requests**.
- **Registry advanced exactly +2,000 consumed** (12,988 → 14,988); pending 25,023 → 23,023. Registry total unchanged (38,011 — deterministic census, never re-walked).
- **Consumed↔fighter correspondence 100%**: all 14,988 consumed IDs have a persisted fighter row.
- **Zero dead-ends**: all 2,000 window IDs resolved to real profiles (no 404/parse-failure consumption; health-gate never needed).
- Records behavior: 1,981/2,000 real payloads; 19 empty (content-dependent absences — never faked, never reset).

## Current DB state (post-window 1)

| Table | Count |
|---|---|
| fighters | **14,988** (+2,000) |
| fighter_records | **14,540** (+1,981) |
| fighters missing records | 448 (429 residual untouched + 19 new genuine absences) |
| statistics / rankings / competitors | 399 / 142 / 47 (unchanged) |
| external_ids | **15,343** (+2,000) |
| events / competitions / promotions / weight_classes | 24 / 260 / 48 / 23 (unchanged) |
| registry total / consumed / pending | 38,011 / **14,988** / **23,023** |
| sync_runs | 22 (+1 COMPLETED `8ff5e625`) |
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

## Risks / notes

1. **Absence floor unchanged:** the 429 known-empties were NOT re-probed (records job closed); 19 new genuine absences added by the window cohort (~1% of new IDs — consistent with the observed floor).
2. **Non-MMA universe:** the registry's 38,011 IDs span all sports (global listing); every probed ID so far (14,988) resolved to a real profile — dead-end rate 0% to date.
3. **No code committed:** W007 5-file drift + all artifacts remain uncommitted per standing instruction. Window 1 added no code.
4. **Records backfill still CLOSED** — untouched this window.

## Decision gate

**STOP — census window 1 complete (PASS).** No further census window, no records rerun, no Phase D, no commit/push without a new explicit decision gate.

## Git safety

No staged/committed/pushed changes. Code drift limited to the 5 documented W007 files. DB writes exclusively the approved single bounded census window.
