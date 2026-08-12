# PRODUCTION WINDOW 010 — Census Expansion Report (Window 3)

**Date:** 2026-08-11 (UTC) · **Type:** bounded fighter census window (registry-consuming)
**Command:** `ESPN_FIGHTER_SYNC_LIMIT=2000 python sync.py --full --entity fighter` (env: `PYTHONIOENCODING=utf-8` for console capture)

---

## 1. Verdict: **PASS**

Window 3 completed cleanly: `COMPLETED, inserted=3962, updated=0, skipped=0, errors=0`, 1,338,777 ms (~22.3 min). **4,000 API requests (2,000 profiles + 2,000 records), all HTTP 200 — 0×404, 0×429, 0×5xx, 0 retries, 0 breaker engagements, 0 discovery requests** (7/7 discovery walks skipped as COMPLETED). All 2,000 window IDs resolved to fighter profiles; 1,962 carried real record payloads; 38 returned empty payloads (content-dependent absences). Registry consumed advanced exactly +2,000; **consumed↔fighter correspondence 100% (18,988 = 18,988)**.

## 2. Target

Third bounded census window: next 2,000 **unconsumed** registry IDs in ascending `external_id` order (deterministic — `discovery.next_window`). Prior state: 38,011 discovered IDs, 16,988 consumed, 21,023 pending (window 2 completed `ae3f0e63`). Same fighter-job mechanism (window-based, crash-safe consumption).

## 3. Baseline (window 3)

`PRODUCTION_WINDOW_010_CENSUS_BASELINE.json` (2026-08-11T12:17:20Z) — fighters 16,988 · fighter_records 16,511 · missing 477 · registry 38,011 (16,988 consumed / 21,023 pending) · external_ids 17,343 · weight_classes 23 · alembic 008 · HEAD `19a87c7`. All integrity checks 0. Preflight: live DB matched W009 AFTER exactly; next-window sample identical (`4010357…`); only the 2 pre-existing stale RUNNING rows; no process running; git/path unchanged.

## 4. Execution

- **Window:** 2,000 IDs (`4010357…` → `4204438…` region, ascending)
- **4,000 API requests** — 2,000 athlete profiles + 2,000 `/records`; all returned **HTTP 200**
- **2,000 fighters inserted** (upsert_batch) · **1,962 fighter_records inserted** · 38 fighters with empty `/records` payloads (never written, never faked)
- **1 new weight class created inline:** "Featherweight - DREAM (65kg)" (external_id 954) — first new class since before W008; explains external_ids +2,001 (= 2,000 fighters + 1 weight class)
- Registry: consumed 16,988 → **18,988 (+2,000)**; pending 21,023 → **19,023 (−2,000)**
- Sync run `746bf41c` COMPLETED (1,338,777 ms ≈ 22.3 min ≈ **3.0 req/s** — inside the validated envelope)
- Fighter checkpoint row: COMPLETED (unchanged)
- **Zero dead-ends:** all 2,000 IDs resolved
- Mode note: strategy logged `mode=incremental` again (recent-sync heuristic) — no behavioral impact (registry-window-based job ignores mode)

## 5. Post-window audit — all ✓

| Check | Result |
|---|---|
| duplicate fighters / fighter_records / external_ids / registry | **0 / 0 / 0 / 0** |
| orphan fighter_records / rankings / statistics / competitors / external_ids | **0 / 0 / 0 / 0 / 0** |
| NULL provider/external_id | **0** |
| unresolved rankings | **0 (142/142 resolve)** |
| consumed registry IDs with a persisted fighter row | **18,988 / 18,988 (100%)** ✓ |
| registry total | 38,011 — unchanged |
| discovery checkpoints | 7/7 COMPLETED — unchanged |
| checkpoints (fighter/ranking/records) | 3/3 COMPLETED — unchanged |

## 6. Before → after / deltas

| Table | Before | After | Δ |
|---|---|---|---|
| fighters | 16,988 | **18,988** | **+2,000** |
| fighter_records | 16,511 | **18,473** | **+1,962** |
| fighters missing records | 477 | 515 | +38 (new genuine absences; residual untouched) |
| statistics | 399 | 399 | 0 |
| rankings | 142 | 142 | 0 |
| competitors | 47 | 47 | 0 |
| external_ids | 17,343 | **19,344** | **+2,001** (2,000 fighters + 1 weight class) |
| events | 24 | 24 | 0 |
| competitions | 260 | 260 | 0 |
| promotions | 48 | 48 | 0 |
| weight_classes | 23 | **24** | **+1** (Featherweight - DREAM (65kg)) |
| registry total | 38,011 | 38,011 | 0 |
| registry consumed | 16,988 | **18,988** | **+2,000** |
| registry pending | 21,023 | **19,023** | **−2,000** |

## 7. Representative verification (all 6 PASS — untouched)

| Fighter | ext_id | record_summary | W/L/D | KO/TKO | Subs | Fights |
|---|---|---|---|---|---|---|
| Islam Makhachev | 3332412 | 28-1-0 | 28/1/0 | 5 | 13 | 29 |
| Francis Ngannou | 3933168 | 19-3-0 | 19/3/0 | 14 | 4 | 22 |
| Demetrious Johnson | 2512089 | 25-4-1 | 25/4/1 | 5 | 8 | 30 |
| Ronda Rousey | 2563796 | 13-2-0 | 13/2/0 | 3 | 10 | 15 |
| Royce Gracie | 2335697 | 15-2-2 | 15/2/2 | 2 | 11 | 19 |
| Ken Shamrock | 2335653 | 29-17-2 | 29/17/2 | 4 | 22 | 48 |

## 8. Cohort quality (window-3 cohort, verified live)

- Cohort size: **exactly 2,000** fighters (created ≥ 12:17:23 UTC); **1,962 with fighter_records (98.1%)**.
- Sample consistency (record_summary ↔ W/L/D ↔ total_fights all match): 4010357 Mina Kurobe 12-6-0/18 (1 KO, 3 subs) · 4010358 Akiko Naito 0-1-0/1 · 4010402 Morgana Silva 0-2-0/2. No fabricated or internally-inconsistent rows observed.

## 9. Performance

| Metric | W008 | W009 | W010 |
|---|---|---|---|
| limit | 2,000 | 2,000 | 2,000 |
| profiles fetched | 2,000 | 2,000 | 2,000 (100% resolved) |
| records fetched | 2,000 (1,981 real) | 2,000 (1,971 real) | 2,000 (**1,962 real**) |
| requests | 4,000 — all 200 | 4,000 — all 200 | 4,000 — all 200 |
| 404 / 429 / 5xx / retries / breaker | 0 | 0 | 0 |
| rate | ~3.0 req/s | ~3.0 req/s | ~3.0 req/s |
| elapsed | 22.3 min | 22.3 min | 22.3 min |

Behavior materially identical to W008/W009; record-payload yield tapering gradually (99.05% → 98.55% → 98.10%).

## 10. Files created / modified

Created: `PRODUCTION_WINDOW_010_CENSUS_BASELINE.json` · `PRODUCTION_WINDOW_010_CENSUS_AFTER.json` · `PRODUCTION_WINDOW_010_CENSUS_SYNC_LOG.txt` · this report · `PRODUCTION_WINDOW_010_CENSUS_POST_AUDIT.md`.
Code: **none modified**. Docs updated: `ESPN_PRODUCTION_JOURNEY.md` (appended §23), `ESPN_HANDOFF_STATE.md`.

## 11. Decision gate: **STOP — no further census window without a new explicit approval**

Window 3 consumed exactly its 2,000-ID budget (registry 18,988 consumed / 19,023 pending). Records backfill remains CLOSED (residual 515 missing untouched). Per the authorization, no further window, no records rerun, no Phase D, no commit/push. Next window (LIMIT=2000 or revised) requires a new decision gate.

## 12. Git safety

No staged files · no commit · no push. No code drift beyond the documented W007 5-file set. DB writes exclusively the approved bounded census window.
