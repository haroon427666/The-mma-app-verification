# PRODUCTION_WINDOW_006_REPORT.md

> **Date:** 2026-08-10
> **Type:** Production window report (W006, LIMIT=5000)
> **Verdict:** **PASS-WITH-NOTES** (records-phase 503/breaker gap — no data loss)

---

## Exact command

```
PYTHONIOENCODING=utf-8 ESPN_FIGHTER_SYNC_LIMIT=5000 python sync.py --full --entity fighter
```

## Timeline / run identity

| Item | Value |
|---|---|
| Run ID | `41f13f93-0b4c-41a8-86c2-3fcf4b055d9b` |
| Start | 2026-08-10 18:13:16 UTC (23:13 local) |
| End | 2026-08-10 18:43:43 UTC (23:43 local) |
| Duration | **1,826,404 ms = 30.4 min** |
| Status | COMPLETED (jobs=1, errors=0) |
| API requests | **5,437** (5,000 profiles + 437 records) |
| Effective rate | **~3.0 req/s** (5,437 / 1,826 s) |
| Discovery requests | **0** (all 7 sources COMPLETED, skipped) |
| HTTP 429 | **0** |
| HTTP 5xx | **44 × 503** (transient, ESPN-side, tail of records phase) |
| Circuit breaker | Tripped CLOSED→OPEN at 18:43:31 UTC (5 consecutive 503s) — correct behavior |
| Retries | 0 (breaker blocked further records fetches; no retry loop) |

## Before / After / Deltas

| Metric | Before | After | Δ |
|---|---|---|---|
| fighters | 7,988 | **12,988** | **+5,000** |
| fighter_records | 6,995 | 7,387 | **+392** (see note) |
| external_ids | 8,341 | 13,343 | +5,002 |
| rankings | 142 | 142 | 0 |
| statistics | 399 | 399 | 0 |
| sync_runs | 16 | 17 | +1 (COMPLETED) |
| registry consumed | 7,988 | **12,988** | **+5,000** |
| registry pending | 30,023 | **25,023** | **−5,000** |
| registry total | 38,011 | 38,011 | 0 |
| alembic | 008 | 008 | — |

## Registry / checkpoint behavior

- Window: 5,000 unconsumed IDs (ascending) → **5,000/5,000 resolved** → 5,000 consumed.
- No unresolved IDs (all profiles fetched before the 503 episode began) → **no dead-end consumption, no leftover queue**.
- Checkpoints: fighter + ranking COMPLETED; 7/7 discovery checkpoints COMPLETED (unchanged).
- Consumption ⇔ persistence: consumed == fighters == 12,988 exactly.

## Integrity sweep (post-run, all ✓)

| Check | Result |
|---|---|
| Duplicate fighters (provider, external_id) | 0 |
| Duplicate external_ids | 0 |
| Duplicate registry rows | 0 |
| Orphan fighter_records / rankings / statistics / competitors / external_ids | 0 / 0 / 0 / 0 / 0 |
| NULL provider/external_id | 0 |
| Unresolved ranking references | 0 |
| Stale RUNNING sync_runs | 2 (pre-existing killed-process artifacts, NOT from W006) |

## Note — records-phase gap (the "notes" in PASS-WITH-NOTES)

- The 44×503s arrived at the **tail of the records phase** (profiles all resolved first).
- The breaker correctly stopped further record fetches; only **392 of 5,000** new fighters received `fighter_records`.
- **5,601 fighters now lack fighter_records** (12,988 − 7,387): ~993 pre-existing + **~4,608 from W006**.
- No fighter rows were lost; records simply weren't attached (records are best-effort by design, never reset).
- Consumed fighters are never re-windowed, so these records are missing **until a records-backfill mechanism exists** (no such job today — records attach only inside the fighter window).
- **Recommendation for W007:** add/run a bounded records-backfill (fetch `/athletes/{id}/records` for fighters missing `fighter_records`, e.g. 5,601 rows ≈ 11,200 requests ≈ 60 min at 3 rps) before or instead of the next census window.

## Confirmed-MMA coverage (frozen census cross-check)

| Classification | Before | After | Δ |
|---|---|---|---|
| confirmed_mma synced | 846 (30.6%) | **1,057 (38.3%)** | +211 |
| confirmed_mma pending | 1,917 | **1,706** | −211 |
| mma_likely synced | 6,547 | 11,219 | +4,672 |
| Remaining-census confirmed yield | 6.4% | 6.8% (1,706/25,023) | — |

## Representative fighters (unchanged, present with records)

| Athlete | ID | Record |
|---|---|---|
| Islam Makhachev | 3332412 | 28-1-0 ✅ |
| Francis Ngannou | 3933168 | 19-3-0 ✅ |
| Demetrious Johnson | 2512089 | 25-4-1 ✅ |
| Ronda Rousey | 2563796 | 13-2-0 ✅ |
| Royce Gracie | 2335697 | 15-2-2 ✅ |
| Ken Shamrock | 2335653 | 29-17-2 ✅ |

## Anomalies

1. 44 transient 503s (ESPN-side; handled by breaker — second occurrence after W005; appears episodic).
2. Records-phase gap: 5,601 fighters without `fighter_records` (largest data-quality gap to date).
3. +5,002 external_ids vs +5,000 fighters (2-row quirk; 0 duplicates — no integrity impact).

## W006 verdict

**PASS-WITH-NOTES** — the window's census objective was fully met (+5,000 consumed, 0 duplicates, 0 integrity violations, 0×429, breaker behaved correctly). The notes concern the records-phase gap, which requires a backfill capability for W007.

## Recommendation for W007

1. **Priority: bounded records backfill** for the ~5,601 fighters missing `fighter_records` (new capability; ~11,200 requests, ~60 min at 3 rps) — closes the W006 gap and improves data quality across all windows.
2. Then the next census window: **LIMIT=5000 again** (same envelope; pending → 20,023; ~+340 confirmed MMA expected at the current ~6.8% yield).
