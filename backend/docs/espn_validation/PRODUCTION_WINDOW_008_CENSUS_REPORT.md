# PRODUCTION WINDOW 008 — Census Expansion Report (Window 1)

**Date:** 2026-08-11 (UTC) · **Type:** bounded fighter census window (registry-consuming)
**Command:** `ESPN_FIGHTER_SYNC_LIMIT=2000 python sync.py --full --entity fighter` (env: `PYTHONIOENCODING=utf-8` for console capture)

---

## 1. Verdict: **PASS**

Window 1 completed cleanly: `COMPLETED, inserted=3981, updated=0, skipped=0, errors=0`, 1,336,587 ms (~22.3 min). **4,000 API requests (2,000 profiles + 2,000 records), all HTTP 200 — 0×404, 0×429, 0×5xx, 0 retries, 0 breaker engagements, 0 discovery requests** (7/7 discovery walks skipped as COMPLETED). All 2,000 window IDs resolved to fighter profiles; 1,981 carried real record payloads; 19 returned empty payloads (content-dependent absences). Registry consumed advanced exactly +2,000; **consumed↔fighter correspondence 100% (14,988 = 14,988)**.

## 2. Target

First bounded census window: next 2,000 **unconsumed** registry IDs in ascending `external_id` order (deterministic window — `discovery.next_window`). Prior state: 38,011 discovered IDs, 12,988 consumed, 25,023 pending. The fighter job (window-based, crash-safe consumption) is the mechanism — same preflight-verified path.

## 3. Baseline (window 1)

`PRODUCTION_WINDOW_008_CENSUS_BASELINE.json` (2026-08-11T11:00:51Z) — fighters 12,988 · fighter_records 12,559 · missing 429 · registry 38,011 (12,988 consumed / 25,023 pending) · external_ids 13,343 · weight_classes 23 · alembic 008 · HEAD `19a87c7`. All integrity checks 0.

## 4. Execution

- **Window:** 2,000 IDs (`3143226…` → `3891894…` ascending; first batch processed IDs 3143226–3162503, then 3890717–3891894 region — all pending were 3.1M–3.9M range)
- **4,000 API requests** — 2,000 athlete profiles + 2,000 `/records`; all returned **HTTP 200**
- **2,000 fighters inserted** (upsert_batch) · **1,981 fighter_records inserted** · 19 fighters with empty `/records` payloads (never written, never faked — "never reset" rule)
- Registry: consumed 12,988 → **14,988 (+2,000)**; pending 25,023 → **23,023 (−2,000)**
- Sync run `8ff5e625` COMPLETED (1,336,587 ms ≈ 22.3 min ≈ **3.0 req/s** — inside the validated envelope)
- Fighter checkpoint row: COMPLETED (unchanged — window-based job; offsets not used)
- **Zero dead-ends:** all 2,000 IDs resolved — no 404/parse-failure consumption, healthy-gate never triggered a "left queued" path

## 5. Post-window audit — all ✓

| Check | Result |
|---|---|
| duplicate fighters / fighter_records / external_ids / registry | **0 / 0 / 0 / 0** |
| orphan fighter_records / rankings / statistics / competitors / external_ids | **0 / 0 / 0 / 0 / 0** |
| NULL provider/external_id | **0** |
| unresolved rankings | **0 (142/142 resolve)** |
| consumed registry IDs with a persisted fighter row | **14,988 / 14,988 (100%)** ✓ |
| registry total | 38,011 — unchanged (fixed universe; census consumes, never adds) |
| discovery checkpoints | 7/7 COMPLETED — unchanged |

## 6. Before → after / deltas

| Table | Before | After | Δ |
|---|---|---|---|
| fighters | 12,988 | **14,988** | **+2,000** |
| fighter_records | 12,559 | **14,540** | **+1,981** |
| fighters missing records | 429 | 448 | +19 (new genuine absences; 429 residual untouched) |
| statistics | 399 | 399 | 0 |
| rankings | 142 | 142 | 0 |
| competitors | 47 | 47 | 0 |
| external_ids | 13,343 | **15,343** | **+2,000** |
| events | 24 | 24 | 0 |
| competitions | 260 | 260 | 0 |
| promotions | 48 | 48 | 0 |
| weight_classes | 23 | 23 | 0 |
| registry total | 38,011 | 38,011 | 0 |
| registry consumed | 12,988 | **14,988** | **+2,000** |
| registry pending | 25,023 | **23,023** | **−2,000** |

## 7. Representative verification (all 6 PASS)

| Fighter | ext_id | record_summary | W/L/D | KO/TKO | Subs | Fights |
|---|---|---|---|---|---|---|
| Islam Makhachev | 3332412 | 28-1-0 | 28/1/0 | 5 | 13 | 29 |
| Francis Ngannou | 3933168 | 19-3-0 | 19/3/0 | 14 | 4 | 22 |
| Demetrious Johnson | 2512089 | 25-4-1 | 25/4/1 | 5 | 8 | 30 |
| Ronda Rousey | 2563796 | 13-2-0 | 13/2/0 | 3 | 10 | 15 |
| Royce Gracie | 2335697 | 15-2-2 | 15/2/2 | 2 | 11 | 19 |
| Ken Shamrock | 2335653 | 29-17-2 | 29/17/2 | 4 | 22 | 48 |

Freshly inserted (window-1 cohort): 3891789 Andrew Force 0-1-0/1 fight, 3890719 Ruben Vera 0-1-0/1, 3891788 Josh Karney 0-1-0/1, 3891781 Eric Daughetee 0-1-0/1, 3890717 Gerardo Morales 0-1-0/1 — consistent, internally-valid payloads.

## 8. Performance

| Metric | Value |
|---|---|
| limit | 2,000 |
| profiles fetched | 2,000 (100% resolved) |
| records fetched | 2,000 (1,981 real, 19 empty) |
| requests | 4,000 — **all HTTP 200** |
| 404 / 429 / 5xx / retries / breaker | 0 / 0 / 0 / 0 / never engaged |
| rate | ~3.0 req/s (validated envelope) |
| elapsed | 22.3 min |

## 9. Behavior confirmation vs preflight

Every preflight expectation held: durable registry used; ascending window; profiles+records via the existing pipeline; crash-safe consumption; checkpoint semantics preserved (no offsets, no checkpoint writes — window-based); envelope respected; 0 dead-ends (the health-gate had nothing to do). No deviation from the verified path.

## 10. Files created / modified

Created: `PRODUCTION_WINDOW_008_CENSUS_BASELINE.json` · `PRODUCTION_WINDOW_008_CENSUS_AFTER.json` · `PRODUCTION_WINDOW_008_CENSUS_SYNC_LOG.txt` · this report · `PRODUCTION_WINDOW_008_CENSUS_POST_AUDIT.md`.
Code: **none modified**. Docs updated: `ESPN_PRODUCTION_JOURNEY.md` (appended), `ESPN_HANDOFF_STATE.md`.

## 11. Decision gate: **STOP — no further census window without a new explicit approval**

Records backfill remains CLOSED (residual 429 absence floor untouched). Census window 1 consumed exactly its 2,000-ID budget. Per the authorization, no further window (LIMIT=2000 or otherwise), no records rerun, no Phase D, no commit/push. Next window (LIMIT=2000 or revised limit) requires a new decision gate.

## 12. Git safety

No staged files · no commit · no push. No code drift beyond the documented W007 5-file set. DB writes exclusively the approved bounded census window.
