# PRODUCTION WINDOW 011 — Census Expansion Report (Window 4)

**Date:** 2026-08-11 (UTC) · **Type:** bounded fighter census window (registry-consuming)
**Command:** `ESPN_FIGHTER_SYNC_LIMIT=2000 python sync.py --full --entity fighter` (env: `PYTHONIOENCODING=utf-8` for console capture)

---

## 1. Verdict: **PASS**

Window 4 completed cleanly: `COMPLETED, inserted=3967, updated=0, skipped=0, errors=0`, 1,334,852 ms (~22.2 min). **4,000 API requests (2,000 profiles + 2,000 records), all HTTP 200 — 0×404, 0×429, 0×5xx, 0 retries, 0 breaker engagements, 0 discovery requests** (7/7 discovery walks skipped as COMPLETED). All 2,000 window IDs resolved to fighter profiles; 1,967 carried real record payloads; 33 returned empty payloads (content-dependent absences). Registry consumed advanced exactly +2,000; **consumed↔fighter correspondence 100% (20,988 = 20,988)**.

## 2. Target

Fourth bounded census window: next 2,000 **unconsumed** registry IDs in ascending `external_id` order (deterministic — `discovery.next_window`). Prior state: 38,011 discovered IDs, 18,988 consumed, 19,023 pending (window 3 completed `746bf41c`). Same fighter-job mechanism (window-based, crash-safe consumption).

## 3. Baseline (window 4)

`PRODUCTION_WINDOW_011_CENSUS_BASELINE.json` (2026-08-11T12:49:55Z) — fighters 18,988 · fighter_records 18,473 · missing 515 · registry 38,011 (18,988 consumed / 19,023 pending) · external_ids 19,344 · weight_classes 24 · alembic 008 · HEAD `19a87c7`. All integrity checks 0. Preflight: live DB matched W010 AFTER exactly; next-window sample identical (`4204351…`); only the 2 pre-existing stale RUNNING rows; no process running; git/path unchanged.

## 4. Execution

- **Window:** 2,000 IDs (`4204351…` → `4294866…` region, ascending)
- **4,000 API requests** — 2,000 athlete profiles + 2,000 `/records`; all returned **HTTP 200**
- **2,000 fighters inserted** (upsert_batch) · **1,967 fighter_records inserted** · 33 fighters with empty `/records` payloads (never written, never faked)
- **1 new weight class created inline:** "Women's Catch Weight" (external_id 1009) — second class created across the census windows (W010: "Featherweight - DREAM (65kg)"); explains external_ids +2,001 (= 2,000 fighters + 1 weight class)
- Registry: consumed 18,988 → **20,988 (+2,000)**; pending 19,023 → **17,023 (−2,000)**
- Sync run `6b6b0bb5` COMPLETED (1,334,852 ms ≈ 22.2 min ≈ **3.0 req/s** — inside the validated envelope)
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
| consumed registry IDs with a persisted fighter row | **20,988 / 20,988 (100%)** ✓ |
| registry total | 38,011 — unchanged |
| discovery checkpoints | 7/7 COMPLETED — unchanged |
| checkpoints (fighter/ranking/records) | 3/3 COMPLETED — unchanged |

## 6. Before → after / deltas

| Table | Before | After | Δ |
|---|---|---|---|
| fighters | 18,988 | **20,988** | **+2,000** |
| fighter_records | 18,473 | **20,440** | **+1,967** |
| fighters missing records | 515 | 548 | +33 (new genuine absences; residual untouched) |
| statistics | 399 | 399 | 0 |
| rankings | 142 | 142 | 0 |
| competitors | 47 | 47 | 0 |
| external_ids | 19,344 | **21,345** | **+2,001** (2,000 fighters + 1 weight class) |
| events | 24 | 24 | 0 |
| competitions | 260 | 260 | 0 |
| promotions | 48 | 48 | 0 |
| weight_classes | 24 | **25** | **+1** (Women's Catch Weight, ext 1009) |
| registry total | 38,011 | 38,011 | 0 |
| registry consumed | 18,988 | **20,988** | **+2,000** |
| registry pending | 19,023 | **17,023** | **−2,000** |

## 7. Representative verification (all 6 PASS — untouched)

| Fighter | ext_id | record_summary | W/L/D | KO/TKO | Subs | Fights |
|---|---|---|---|---|---|---|
| Islam Makhachev | 3332412 | 28-1-0 | 28/1/0 | 5 | 13 | 29 |
| Francis Ngannou | 3933168 | 19-3-0 | 19/3/0 | 14 | 4 | 22 |
| Demetrious Johnson | 2512089 | 25-4-1 | 25/4/1 | 5 | 8 | 30 |
| Ronda Rousey | 2563796 | 13-2-0 | 13/2/0 | 3 | 10 | 15 |
| Royce Gracie | 2335697 | 15-2-2 | 15/2/2 | 2 | 11 | 19 |
| Ken Shamrock | 2335653 | 29-17-2 | 29/17/2 | 4 | 22 | 48 |

## 8. Cohort quality (window-4 cohort, verified live)

- Cohort size: **exactly 2,000** fighters (created ≥ 12:50:13 UTC); **1,967 with fighter_records (98.35%)**.
- Sample consistency (record_summary ↔ W/L/D ↔ total_fights all match): 4204351 Edson Nilson Gottlieb Jr. 0-1-0/1 · 4204437 Carls John de Tomas 6-4-0/10 (3 subs) · 4204438 Naoki Inoue 21-5-0/26 (2 KO, 9 subs) · 4205092 Alexander Shabliy 25-4-0/29 (12 KO, 7 subs) · 4205093 Sean O'Malley 20-3-0/24 (13 KO, 1 sub). Real notable fighters present (Shabliy, O'Malley, Inoue). No fabricated or internally-inconsistent rows observed.

## 9. Performance

| Metric | W008 | W009 | W010 | W011 |
|---|---|---|---|---|
| limit | 2,000 | 2,000 | 2,000 | 2,000 |
| profiles fetched | 2,000 | 2,000 | 2,000 | 2,000 (100% resolved) |
| records fetched | 2,000 (1,981 real) | 2,000 (1,971 real) | 2,000 (1,962 real) | 2,000 (**1,967 real**) |
| requests | 4,000 — all 200 | 4,000 — all 200 | 4,000 — all 200 | 4,000 — all 200 |
| 404 / 429 / 5xx / retries / breaker | 0 | 0 | 0 | 0 |
| rate | ~3.0 req/s | ~3.0 req/s | ~3.0 req/s | ~3.0 req/s |
| elapsed | 22.3 min | 22.3 min | 22.3 min | 22.2 min |

Behavior materially identical to W008–W010; record-payload yield remains ~98–99% (99.05% → 98.55% → 98.10% → **98.35%** — non-monotonic, content-dependent).

## 10. Files created / modified

Created: `PRODUCTION_WINDOW_011_CENSUS_BASELINE.json` · `PRODUCTION_WINDOW_011_CENSUS_AFTER.json` · `PRODUCTION_WINDOW_011_CENSUS_SYNC_LOG.txt` · this report · `PRODUCTION_WINDOW_011_CENSUS_POST_AUDIT.md`.
Code: **none modified**. Docs updated: `ESPN_PRODUCTION_JOURNEY.md` (appended §24), `ESPN_HANDOFF_STATE.md`.

## 11. Decision gate: **STOP — no further census window without a new explicit approval**

Window 4 consumed exactly its 2,000-ID budget (registry 20,988 consumed / 17,023 pending). Records backfill remains CLOSED (residual 548 missing untouched). Per the authorization, no further window, no records rerun, no Phase D, no commit/push. Next window (LIMIT=2000 or revised) requires a new decision gate.

## 12. Git safety

No staged files · no commit · no push. No code drift beyond the documented W007 5-file set. DB writes exclusively the approved bounded census window.
