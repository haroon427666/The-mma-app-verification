# PRODUCTION WINDOW 014 — Census Expansion Report (Window 7)

**Date:** 2026-08-11 (UTC) · **Type:** bounded fighter census window (registry-consuming)
**Command:** `ESPN_FIGHTER_SYNC_LIMIT=2000 python sync.py --full --entity fighter` (env: `PYTHONIOENCODING=utf-8` for console capture)

---

## 1. Verdict: **PASS**

Window 7 completed cleanly: `COMPLETED, inserted=3991, updated=0, skipped=0, errors=0`, 1,334,418 ms (~22.2 min). **4,000 API requests (2,000 profiles + 2,000 records), all HTTP 200 — 0×404, 0×429, 0×5xx, 0 retries, 0 breaker engagements, 0 discovery requests** (7/7 discovery walks skipped as COMPLETED). All 2,000 window IDs resolved to fighter profiles (100%); **1,991 carried real record payloads (99.55% yield — recovered to the W008–W012 band)**; 9 returned empty payloads (content-dependent absences). Registry consumed advanced exactly +2,000; **consumed↔fighter correspondence 100% (26,988 = 26,988)**.

## 2. Target

Seventh bounded census window: next 2,000 **unconsumed** registry IDs in ascending `external_id` order (deterministic — `discovery.next_window`). Prior state: 38,011 discovered IDs, 24,988 consumed, 13,023 pending (window 6 completed `37e7c153`). Same fighter-job mechanism (window-based, crash-safe consumption).

## 3. Baseline (window 7)

`PRODUCTION_WINDOW_014_CENSUS_BASELINE.json` (2026-08-11T14:28:21Z) — fighters 24,988 · fighter_records 24,325 · missing 663 · registry 38,011 (24,988 consumed / 13,023 pending) · external_ids 25,345 · weight_classes 25 · alembic 008 · HEAD `19a87c7`. All integrity checks 0. Preflight: live DB matched W013 AFTER exactly (all 20 invariants OK); next-window sample identical (`4683575…`); only the 2 pre-existing stale RUNNING rows; no python sync process running; git clean (nothing staged); HEAD unchanged.

## 4. Execution

- **Window:** 2,000 IDs (`4683575…` → `4869213…` region, ascending)
- **4,000 API requests** — 2,000 athlete profiles + 2,000 `/records`; all returned **HTTP 200**
- **2,000 fighters inserted** (upsert_batch) · **1,991 fighter_records inserted** · 9 fighters with empty `/records` payloads (never written, never faked)
- **No new weight class** (weight_classes 25 → 25); external_ids delta exactly **+2,000** (2,000 fighters, 0 classes)
- Registry: consumed 24,988 → **26,988 (+2,000)**; pending 13,023 → **11,023 (−2,000)**
- Sync run `200a3500` COMPLETED (1,334,418 ms ≈ 22.2 min ≈ **3.0 req/s** — inside the validated envelope)
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
| consumed registry IDs with a persisted fighter row | **26,988 / 26,988 (100%)** ✓ |
| registry total | 38,011 — unchanged |
| discovery checkpoints | 7/7 COMPLETED — unchanged |
| checkpoints (fighter/ranking/records) | 3/3 COMPLETED — unchanged |

## 6. Before → after / deltas

| Table | Before | After | Δ |
|---|---|---|---|
| fighters | 24,988 | **26,988** | **+2,000** |
| fighter_records | 24,325 | **26,316** | **+1,991** |
| fighters missing records | 663 | 672 | +9 (new genuine absences; residual untouched) |
| statistics | 399 | 399 | 0 |
| rankings | 142 | 142 | 0 |
| competitors | 47 | 47 | 0 |
| external_ids | 25,345 | **27,345** | **+2,000** (2,000 fighters, 0 weight classes) |
| events | 24 | 24 | 0 |
| competitions | 260 | 260 | 0 |
| promotions | 48 | 48 | 0 |
| weight_classes | 25 | 25 | 0 |
| registry total | 38,011 | 38,011 | 0 |
| registry consumed | 24,988 | **26,988** | **+2,000** |
| registry pending | 13,023 | **11,023** | **−2,000** |

## 7. Representative verification (all 6 PASS — untouched)

| Fighter | ext_id | record_summary | W/L/D | KO/TKO | Subs | Fights |
|---|---|---|---|---|---|---|
| Islam Makhachev | 3332412 | 28-1-0 | 28/1/0 | 5 | 13 | 29 |
| Francis Ngannou | 3933168 | 19-3-0 | 19/3/0 | 14 | 4 | 22 |
| Demetrious Johnson | 2512089 | 25-4-1 | 25/4/1 | 5 | 8 | 30 |
| Ronda Rousey | 2563796 | 13-2-0 | 13/2/0 | 3 | 10 | 15 |
| Royce Gracie | 2335697 | 15-2-2 | 15/2/2 | 2 | 11 | 19 |
| Ken Shamrock | 2335653 | 29-17-2 | 29/17/2 | 4 | 22 | 48 |

## 8. Cohort quality (window-7 cohort, verified live)

- Cohort size: **exactly 2,000** fighters (created ≥ 14:28:33 UTC); **1,991 with fighter_records (99.55%)** — yield recovered from W013's placeholder-band dip to the normal band.
- Sample consistency (record_summary ↔ W/L/D ↔ total_fights all match): 4683575 Alejandro Zea 0-2-0/2 · 4683578 Desmond Moore 1-1-0/2 · 4683580 Greg Fischer 10-4-0/14 (5 subs) · 4683651 Washington Luiz 0-2-0/2 · 4868779 Wellington Prado 12-4-0/16. Notable real fighter: **Darnell Pettis** (4683576, 0-1-0/1). No fabricated or internally inconsistent rows observed.

## 9. Performance

| Metric | W009 | W012 | W013 | W014 |
|---|---|---|---|---|
| limit | 2,000 | 2,000 | 2,000 | 2,000 |
| profiles fetched | 2,000 | 2,000 | 2,000 | 2,000 (100% resolved) |
| records fetched | 1,971 real | 1,964 real | 1,921 real | **1,991 real** |
| requests | 4,000 all 200 | 4,000 all 200 | 4,000 all 200 | 4,000 all 200 |
| 404 / 429 / 5xx / retries / breaker | 0 | 0 | 0 | 0 |
| rate | ~3.0 req/s | ~3.0 req/s | ~3.0 req/s | ~3.0 req/s |
| elapsed | 22.3 min | 22.3 min | 22.2 min | 22.2 min |

Behavior materially identical to W008–W013. Record-payload yield: 99.05 → 98.55 → 98.10 → 98.35 → 98.2 → 96.05 → **99.55%** — W013's dip confirmed as a one-off placeholder-band artifact; no trend.

## 10. Files created / modified

Created: `PRODUCTION_WINDOW_014_CENSUS_BASELINE.json` · `PRODUCTION_WINDOW_014_CENSUS_AFTER.json` · `PRODUCTION_WINDOW_014_CENSUS_SYNC_LOG.txt` · this report · `PRODUCTION_WINDOW_014_CENSUS_POST_AUDIT.md`.
Code: **none modified**. Docs updated: `ESPN_PRODUCTION_JOURNEY.md` (appended §27), `ESPN_HANDOFF_STATE.md`.

## 11. Decision gate: **STOP — no further census window without a new explicit approval**

Window 7 consumed exactly its 2,000-ID budget (registry 26,988 consumed / 11,023 pending). Records backfill remains CLOSED (residual 672 missing untouched). Per the authorization, no further window, no records rerun, no Phase D, no commit/push. Next window (W015, LIMIT=2000 or revised) requires a new decision gate.

## 12. Git safety

No staged files · no commit · no push. No code drift beyond the documented W007 5-file set. DB writes exclusively the approved bounded census window.
