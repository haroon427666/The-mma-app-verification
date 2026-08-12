# PRODUCTION WINDOW 012 — Census Expansion Report (Window 5)

**Date:** 2026-08-11 (UTC) · **Type:** bounded fighter census window (registry-consuming)
**Command:** `ESPN_FIGHTER_SYNC_LIMIT=2000 python sync.py --full --entity fighter` (env: `PYTHONIOENCODING=utf-8` for console capture)

---

## 1. Verdict: **PASS**

Window 5 completed cleanly: `COMPLETED, inserted=3964, updated=0, skipped=0, errors=0`, 1,336,349 ms (~22.3 min). **4,000 API requests (2,000 profiles + 2,000 records), all HTTP 200 — 0×404, 0×429, 0×5xx, 0 retries, 0 breaker engagements, 0 discovery requests** (7/7 discovery walks skipped as COMPLETED). All 2,000 window IDs resolved to fighter profiles; 1,964 carried real record payloads; 36 returned empty payloads (content-dependent absences). Registry consumed advanced exactly +2,000; **consumed↔fighter correspondence 100% (22,988 = 22,988)**.

## 2. Target

Fifth bounded census window: next 2,000 **unconsumed** registry IDs in ascending `external_id` order (deterministic — `discovery.next_window`). Prior state: 38,011 discovered IDs, 20,988 consumed, 17,023 pending (window 4 completed `6b6b0bb5`). Same fighter-job mechanism (window-based, crash-safe consumption).

## 3. Baseline (window 5)

`PRODUCTION_WINDOW_012_CENSUS_BASELINE.json` (2026-08-11T13:18:30Z) — fighters 20,988 · fighter_records 20,440 · missing 548 · registry 38,011 (20,988 consumed / 17,023 pending) · external_ids 21,345 · weight_classes 25 · alembic 008 · HEAD `19a87c7`. All integrity checks 0. Preflight: live DB matched W011 AFTER exactly; next-window sample identical (`4294867…`); only the 2 pre-existing stale RUNNING rows; no process running; git/path unchanged.

## 4. Execution

- **Window:** 2,000 IDs (`4294867…` → `4410116…` region, ascending)
- **4,000 API requests** — 2,000 athlete profiles + 2,000 `/records`; all returned **HTTP 200**
- **2,000 fighters inserted** (upsert_batch) · **1,964 fighter_records inserted** · 36 fighters with empty `/records` payloads (never written, never faked)
- **No new weight class** this window (weight_classes 25 → 25) — external_ids delta exactly +2,000 (2,000 fighters, 0 classes)
- Registry: consumed 20,988 → **22,988 (+2,000)**; pending 17,023 → **15,023 (−2,000)**
- Sync run `6c2ba67f` COMPLETED (1,336,349 ms ≈ 22.3 min ≈ **3.0 req/s** — inside the validated envelope)
- Fighter checkpoint row: COMPLETED (unchanged)
- **Zero dead-ends:** all 2,000 IDs resolved
- Mode note: strategy logged `mode=incremental` (recent-sync heuristic) — no behavioral impact (registry-window-based job ignores mode)

## 5. Post-window audit — all ✓

| Check | Result |
|---|---|
| duplicate fighters / fighter_records / external_ids / registry | **0 / 0 / 0 / 0** |
| orphan fighter_records / rankings / statistics / competitors / external_ids | **0 / 0 / 0 / 0 / 0** |
| NULL provider/external_id | **0** |
| unresolved rankings | **0 (142/142 resolve)** |
| consumed registry IDs with a persisted fighter row | **22,988 / 22,988 (100%)** ✓ |
| registry total | 38,011 — unchanged |
| discovery checkpoints | 7/7 COMPLETED — unchanged |
| checkpoints (fighter/ranking/records) | 3/3 COMPLETED — unchanged |

## 6. Before → after / deltas

| Table | Before | After | Δ |
|---|---|---|---|
| fighters | 20,988 | **22,988** | **+2,000** |
| fighter_records | 20,440 | **22,404** | **+1,964** |
| fighters missing records | 548 | 584 | +36 (new genuine absences; residual untouched) |
| statistics | 399 | 399 | 0 |
| rankings | 142 | 142 | 0 |
| competitors | 47 | 47 | 0 |
| external_ids | 21,345 | **23,345** | **+2,000** (2,000 fighters, 0 weight classes) |
| events | 24 | 24 | 0 |
| competitions | 260 | 260 | 0 |
| promotions | 48 | 48 | 0 |
| weight_classes | 25 | 25 | 0 |
| registry total | 38,011 | 38,011 | 0 |
| registry consumed | 20,988 | **22,988** | **+2,000** |
| registry pending | 17,023 | **15,023** | **−2,000** |

## 7. Representative verification (all 6 PASS — untouched)

| Fighter | ext_id | record_summary | W/L/D | KO/TKO | Subs | Fights |
|---|---|---|---|---|---|---|
| Islam Makhachev | 3332412 | 28-1-0 | 28/1/0 | 5 | 13 | 29 |
| Francis Ngannou | 3933168 | 19-3-0 | 19/3/0 | 14 | 4 | 22 |
| Demetrious Johnson | 2512089 | 25-4-1 | 25/4/1 | 5 | 8 | 30 |
| Ronda Rousey | 2563796 | 13-2-0 | 13/2/0 | 3 | 10 | 15 |
| Royce Gracie | 2335697 | 15-2-2 | 15/2/2 | 2 | 11 | 19 |
| Ken Shamrock | 2335653 | 29-17-2 | 29/17/2 | 4 | 22 | 48 |

## 8. Cohort quality (window-5 cohort, verified live)

- Cohort size: **exactly 2,000** fighters (created ≥ 13:18:40 UTC); **1,964 with fighter_records (98.2%)**.
- Sample consistency (record_summary ↔ W/L/D ↔ total_fights all match): 4294867 Daisuke Yamaji 0-1-0/1 · 4294870 Magomedsaygid Alibekov 9-1-0/10 (1 KO, 2 subs) · 4294871 Nariman Abbasov 28-4-0/32 (12 KO, 5 subs) · 4410116 Leonardo Damiani 11-7-1/19. No fabricated or internally inconsistent rows observed.

## 9. Performance

| Metric | W008 | W009 | W010 | W011 | W012 |
|---|---|---|---|---|---|
| limit | 2,000 | 2,000 | 2,000 | 2,000 | 2,000 |
| profiles fetched | 2,000 | 2,000 | 2,000 | 2,000 | 2,000 (100% resolved) |
| records fetched | 1,981 real | 1,971 real | 1,962 real | 1,967 real | **1,964 real** |
| requests | 4,000 — all 200 | 4,000 — all 200 | 4,000 — all 200 | 4,000 — all 200 | 4,000 — all 200 |
| 404 / 429 / 5xx / retries / breaker | 0 | 0 | 0 | 0 | 0 |
| rate | ~3.0 req/s | ~3.0 req/s | ~3.0 req/s | ~3.0 req/s | ~3.0 req/s |
| elapsed | 22.3 min | 22.3 min | 22.3 min | 22.2 min | 22.3 min |

Behavior materially identical to W008–W011; record-payload yield remains ~98% (99.05 → 98.55 → 98.10 → 98.35 → **98.2%** — content-dependent).

## 10. Files created / modified

Created: `PRODUCTION_WINDOW_012_CENSUS_BASELINE.json` · `PRODUCTION_WINDOW_012_CENSUS_AFTER.json` · `PRODUCTION_WINDOW_012_CENSUS_SYNC_LOG.txt` · this report · `PRODUCTION_WINDOW_012_CENSUS_POST_AUDIT.md`.
Code: **none modified**. Docs updated: `ESPN_PRODUCTION_JOURNEY.md` (appended §25), `ESPN_HANDOFF_STATE.md`.

## 11. Decision gate: **STOP — no further census window without a new explicit approval**

Window 5 consumed exactly its 2,000-ID budget (registry 22,988 consumed / 15,023 pending). Records backfill remains CLOSED (residual 584 missing untouched). Per the authorization, no further window, no records rerun, no Phase D, no commit/push. Next window (LIMIT=2000 or revised) requires a new decision gate.

## 12. Git safety

No staged files · no commit · no push. No code drift beyond the documented W007 5-file set. DB writes exclusively the approved bounded census window.
