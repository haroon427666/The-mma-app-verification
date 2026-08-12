# PRODUCTION_WINDOW_006_POST_AUDIT.md

> **Date:** 2026-08-10
> **Type:** Post-window audit (W006, LIMIT=5000)
> **Verdict:** **PASS-WITH-NOTES** — census objective met; notes on the records-phase gap and recurring transient 503s.

---

## 1. Objective

Execute the approved 5,000-fighter window (decision gate B from the W005 audit) with full before/after capture, integrity sweep, coverage check, and documentation. No unbounded census; no code/migration/test/mobile/research changes; no commits/pushes.

## 2. Execution

- Command: `PYTHONIOENCODING=utf-8 ESPN_FIGHTER_SYNC_LIMIT=5000 sync.py --full --entity fighter`
- Run `41f13f93` — 18:13:16 → 18:43:43 UTC — **30.4 min** — COMPLETED, errors=0
- Requests: **5,437** (5,000 profiles + 437 records) · **0 discovery** · **~3.0 req/s**
- HTTP: **0×429 · 44×503** (transient ESPN-side, records-phase tail) → breaker CLOSED→OPEN (correct)

## 3. Results (before → after)

| Metric | Before | After | Δ |
|---|---|---|---|
| fighters | 7,988 | **12,988** | +5,000 |
| fighter_records | 6,995 | 7,387 | +392 ⚠️ |
| external_ids | 8,341 | 13,343 | +5,002 |
| registry consumed | 7,988 | **12,988** | +5,000 |
| registry pending | 30,023 | **25,023** | −5,000 |
| sync_runs | 16 | 17 | +1 COMPLETED |
| rankings / statistics | 142 / 399 | 142 / 399 | 0 |

## 4. Registry / checkpoint behavior

- 5,000/5,000 profiles resolved → **all 5,000 consumed** (no unresolved IDs → no leftover queue, no retry needed).
- Consumption ⇔ persistence exact (consumed == fighters == 12,988).
- Checkpoints: fighter + ranking COMPLETED; 7/7 discovery COMPLETED. 0 discovery requests.

## 5. Integrity (all ✓)

0 dupes (fighters/registry/ext_ids) · 0 orphans (records/rankings/statistics/competitors/ext_ids) · 0 NULLs · 0 unresolved rankings (142/142) · 2 stale RUNNING rows (pre-existing, not W006).

## 6. Coverage

confirmed_mma synced **846 → 1,057 (38.3%)**; pending 1,706 (all still queued). mma_likely synced 11,219. Remaining-census yield 6.8%.

## 7. Representatives (unchanged)

Makhachev 3332412 (28-1-0) · Ngannou 3933168 (19-3-0) · DJ 2512089 (25-4-1) · Rousey 2563796 (13-2-0) · Gracie 2335697 (15-2-2) · Shamrock 2335653 (29-17-2) — all present.

## 8. Anomalies / notes

1. **Records-phase gap (primary note):** the 44×503s hit after all profiles resolved; only 392/5,000 new fighters got `fighter_records`. **5,601 fighters now lack records** (~993 pre-existing + ~4,608 from W006). No fighter rows lost; records are best-effort by design. Consumed fighters are never re-windowed → requires a **records-backfill capability** (no such job exists today).
2. **503 recurrence:** second production occurrence (W005 run 1, W006). Episodic ESPN-side; breaker + resume handle it. No rate-envelope breach (0×429).
3. external_ids delta +5,002 vs +5,000 fighters (2-row quirk; 0 duplicates, no integrity impact).

## 9. W006 classification

| Mechanism | Verdict |
|---|---|
| Window execution | PASS |
| Registry consumption | PASS |
| Circuit breaker | PASS |
| Checkpoint/resume | PASS (not exercised — no unresolved IDs) |
| Idempotency / integrity | PASS |
| Data completeness (records) | **NOTES** — 4,608 W006 fighters await records backfill |

## 10. Recommendation for W007

1. **Bounded records backfill** for the ~5,601 fighters missing `fighter_records` (new capability; ~11,200 requests ≈ 60 min at 3 rps) — highest priority (closes the largest data-quality gap).
2. Then next census window: **LIMIT=5000** (pending → ~20,023; ~+340 confirmed MMA expected at ~6.8% yield).

---

**Audit statement:** observation + documentation only. W006 executed as approved; no further windows run; no code/migration/test/mobile/research changes; nothing staged/committed/pushed.
