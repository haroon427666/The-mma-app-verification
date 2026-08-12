# PRODUCTION WINDOW 009 — Census Expansion Report (Window 2)

**Date:** 2026-08-11 (UTC) · **Type:** bounded fighter census window (registry-consuming)
**Command:** `ESPN_FIGHTER_SYNC_LIMIT=2000 python sync.py --full --entity fighter` (env: `PYTHONIOENCODING=utf-8` for console capture)

---

## 1. Verdict: **PASS**

Window 2 completed cleanly: `COMPLETED, inserted=3971, updated=0, skipped=0, errors=0`, 1,338,638 ms (~22.3 min). **4,000 API requests (2,000 profiles + 2,000 records), all HTTP 200 — 0×404, 0×429, 0×5xx, 0 retries, 0 breaker engagements, 0 discovery requests** (7/7 discovery walks skipped as COMPLETED). All 2,000 window IDs resolved to fighter profiles; 1,971 carried real record payloads; 29 returned empty payloads (content-dependent absences). Registry consumed advanced exactly +2,000; **consumed↔fighter correspondence 100% (16,988 = 16,988)**.

## 2. Target

Second bounded census window: next 2,000 **unconsumed** registry IDs in ascending `external_id` order (deterministic — `discovery.next_window`). Prior state: 38,011 discovered IDs, 14,988 consumed, 23,023 pending (window 1 completed `8ff5e625`). Same fighter-job mechanism as window 1 (window-based, crash-safe consumption).

## 3. Baseline (window 2)

`PRODUCTION_WINDOW_009_CENSUS_BASELINE.json` (2026-08-11T11:46:33Z) — fighters 14,988 · fighter_records 14,540 · missing 448 · registry 38,011 (14,988 consumed / 23,023 pending) · external_ids 15,343 · weight_classes 23 · alembic 008 · HEAD `19a87c7`. All integrity checks 0. Preflight: live DB matched W008 AFTER exactly; next-window sample identical (`3891894…`); only the 2 pre-existing stale RUNNING rows; no process running; execution path unchanged.

## 4. Execution

- **Window:** 2,000 IDs (`3891894…` → `4010682…` region, ascending)
- **4,000 API requests** — 2,000 athlete profiles + 2,000 `/records`; all returned **HTTP 200**
- **2,000 fighters inserted** (upsert_batch) · **1,971 fighter_records inserted** · 29 fighters with empty `/records` payloads (never written, never faked)
- Registry: consumed 14,988 → **16,988 (+2,000)**; pending 23,023 → **21,023 (−2,000)**
- Sync run `ae3f0e63` COMPLETED (1,338,638 ms ≈ 22.3 min ≈ **3.0 req/s** — inside the validated envelope)
- Fighter checkpoint row: COMPLETED (unchanged)
- **Zero dead-ends:** all 2,000 IDs resolved — no 404/parse-failure consumption
- Note: strategy logged `mode=incremental` (recent-sync heuristic — window 1 ran 44 min earlier). **No behavioral impact**: the fighter job is registry-window-based and ignores the mode decision; consumption and results identical to the verified window-1 path.

## 5. Post-window audit — all ✓

| Check | Result |
|---|---|
| duplicate fighters / fighter_records / external_ids / registry | **0 / 0 / 0 / 0** |
| orphan fighter_records / rankings / statistics / competitors / external_ids | **0 / 0 / 0 / 0 / 0** |
| NULL provider/external_id | **0** |
| unresolved rankings | **0 (142/142 resolve)** |
| consumed registry IDs with a persisted fighter row | **16,988 / 16,988 (100%)** ✓ |
| registry total | 38,011 — unchanged |
| discovery checkpoints | 7/7 COMPLETED — unchanged |
| checkpoints (fighter/ranking/records) | 3/3 COMPLETED — unchanged |

## 6. Before → after / deltas

| Table | Before | After | Δ |
|---|---|---|---|
| fighters | 14,988 | **16,988** | **+2,000** |
| fighter_records | 14,540 | **16,511** | **+1,971** |
| fighters missing records | 448 | 477 | +29 (new genuine absences; residual untouched) |
| statistics | 399 | 399 | 0 |
| rankings | 142 | 142 | 0 |
| competitors | 47 | 47 | 0 |
| external_ids | 15,343 | **17,343** | **+2,000** |
| events | 24 | 24 | 0 |
| competitions | 260 | 260 | 0 |
| promotions | 48 | 48 | 0 |
| weight_classes | 23 | 23 | 0 |
| registry total | 38,011 | 38,011 | 0 |
| registry consumed | 14,988 | **16,988** | **+2,000** |
| registry pending | 23,023 | **21,023** | **−2,000** |

## 7. Representative verification (all 6 PASS — untouched)

| Fighter | ext_id | record_summary | W/L/D | KO/TKO | Subs | Fights |
|---|---|---|---|---|---|---|
| Islam Makhachev | 3332412 | 28-1-0 | 28/1/0 | 5 | 13 | 29 |
| Francis Ngannou | 3933168 | 19-3-0 | 19/3/0 | 14 | 4 | 22 |
| Demetrious Johnson | 2512089 | 25-4-1 | 25/4/1 | 5 | 8 | 30 |
| Ronda Rousey | 2563796 | 13-2-0 | 13/2/0 | 3 | 10 | 15 |
| Royce Gracie | 2335697 | 15-2-2 | 15/2/2 | 2 | 11 | 19 |
| Ken Shamrock | 2335653 | 29-17-2 | 29/17/2 | 4 | 22 | 48 |

## 8. Cohort quality (window-2 cohort, verified live)

- Cohort size: **exactly 2,000** fighters (created ≥ 11:46:39 UTC); **1,971 with fighter_records (98.55%)**; 1,947 with profile-level W/L/D.
- Sample consistency (record_summary ↔ W/L/D ↔ total_fights all match): 3891894 Mark Vorgeas 0-1-1/2 · 3892370 Augusto Mendes 6-2-0/8 (1 KO, 4 subs) · 3892389 Maxim Divnich 13-3-0/16 · 3892395 Kota Shimoishi 3-7-0/10.
- Notable real fighters with plausible careers: Joilton Lutterbach 38-10-0/49 · Julian Erosa 31-14-0/45 · Kevin Holland 29-15-0/45 · Tatsumitsu Wada 25-13-2/41 · Humberto Bandenay 27-10-0/39. No fabricated or internally-inconsistent rows observed.

## 9. Performance

| Metric | W008 (window 1) | W009 (window 2) |
|---|---|---|
| limit | 2,000 | 2,000 |
| profiles fetched | 2,000 (100% resolved) | 2,000 (100% resolved) |
| records fetched | 2,000 (1,981 real / 19 empty) | 2,000 (1,971 real / 29 empty) |
| requests | 4,000 — all HTTP 200 | 4,000 — all HTTP 200 |
| 404 / 429 / 5xx / retries / breaker | 0 / 0 / 0 / 0 / none | 0 / 0 / 0 / 0 / none |
| rate | ~3.0 req/s | ~3.0 req/s |
| elapsed | 22.3 min | 22.3 min |

Behavior materially identical to W008 (yield: 99.05% → 98.55% record payloads — mild taper as the band rises, consistent with expectation).

## 10. Files created / modified

Created: `PRODUCTION_WINDOW_009_CENSUS_BASELINE.json` · `PRODUCTION_WINDOW_009_CENSUS_AFTER.json` · `PRODUCTION_WINDOW_009_CENSUS_SYNC_LOG.txt` · this report · `PRODUCTION_WINDOW_009_CENSUS_POST_AUDIT.md`.
Code: **none modified**. Docs updated: `ESPN_PRODUCTION_JOURNEY.md` (appended §22), `ESPN_HANDOFF_STATE.md`.

## 11. Decision gate: **STOP — no further census window without a new explicit approval**

Window 2 consumed exactly its 2,000-ID budget (registry 16,988 consumed / 21,023 pending). Records backfill remains CLOSED (residual 477 missing untouched). Per the authorization, no further window, no records rerun, no Phase D, no commit/push. Next window (LIMIT=2000 or revised) requires a new decision gate.

## 12. Git safety

No staged files · no commit · no push. No code drift beyond the documented W007 5-file set. DB writes exclusively the approved bounded census window.
