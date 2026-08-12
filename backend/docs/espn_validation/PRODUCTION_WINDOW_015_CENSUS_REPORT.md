# PRODUCTION WINDOW 015 — Census Expansion Report (Window 8)

**Date:** 2026-08-11 (UTC) · **Type:** bounded fighter census window (registry-consuming)
**Command:** `ESPN_FIGHTER_SYNC_LIMIT=2000 python sync.py --full --entity fighter` (env: `PYTHONIOENCODING=utf-8` for console capture)
**DB context:** production = PostgreSQL 18 `localhost:5432/mma` (authoritative; `backend/mma_stats.db` is a 0-byte placeholder from the forensic probe — never production, untouched).

---

## 1. Verdict: **PASS**

Window 8 completed cleanly: `COMPLETED, inserted=3995, updated=0, skipped=0, errors=0`, 1,334,775 ms (~22.2 min). **4,000 API requests (2,000 profiles + 2,000 /records), all HTTP 200 — 0×404, 0×429, 0×5xx, 0 retries, 0 breaker engagements, 0 discovery requests** (7/7 discovery walks skipped as COMPLETED — 14 "already completed — skipping" lines incl. fighter-job repeats). All 2,000 window IDs resolved to fighter profiles (100%); **1,995 carried real record payloads (99.75% yield)**; 5 returned empty payloads (content-dependent absences). Registry consumed advanced exactly +2,000; **consumed↔fighter correspondence 100% (28,988 = 28,988)**.

## 2. Target

Eighth bounded census window: next 2,000 **unconsumed** registry IDs in ascending `external_id` order (deterministic — `discovery.next_window`). Prior state: 38,011 discovered IDs, 26,988 consumed, 11,023 pending (window 7 completed `200a3500`). Same fighter-job mechanism (window-based, crash-safe consumption).

## 3. Baseline (window 8)

`PRODUCTION_WINDOW_015_CENSUS_BASELINE.json` (2026-08-11T15:17:30Z) — fighters 26,988 · fighter_records 26,316 · missing 672 · registry 38,011 (26,988 consumed / 11,023 pending) · external_ids 27,345 · weight_classes 25 · alembic 008 · HEAD `19a87c7`. All integrity checks 0. Preflight: PostgreSQL reachable (service `postgresql-x64-18` Running, port 5432 open), DSN `postgresql://mma:mma@localhost:5432/mma`, live counts matched W014 AFTER exactly (all invariants), next-window first ID `4869216`, no python sync process running, discovery 7/7 COMPLETED, git main @ `19a87c7` (nothing staged).

## 4. Execution

- **Window:** 2,000 IDs (`4869216…` → `5007664…` region, ascending — sparse high-ID band; only ~2,000 registered IDs exist in this ~138K range, consistent with the documented low-yield/inactive band note)
- **4,000 API requests** — 2,000 athlete profiles + 2,000 `/records`; all returned **HTTP 200**
- **2,000 fighters inserted** (upsert_batch) · **1,995 fighter_records inserted** · 5 fighters with empty `/records` payloads (never written, never faked)
- **No new weight class** (weight_classes 25 → 25); external_ids delta exactly **+2,000** (2,000 fighters, 0 classes)
- Registry: consumed 26,988 → **28,988 (+2,000)**; pending 11,023 → **9,023 (−2,000)**
- Sync run `24f66550` COMPLETED (1,334,775 ms ≈ 22.2 min ≈ **3.0 req/s** — inside the validated envelope)
- Checkpoints: fighter/ranking/records all COMPLETED (unchanged)
- **Zero dead-ends:** all 2,000 IDs resolved
- Mode note: strategy logged `mode=incremental` (recent-sync heuristic) — no behavioral impact (registry-window-based job ignores mode)

## 5. Post-window audit — all ✓

| Check | Result |
|---|---|
| duplicate fighters / fighter_records / external_ids / registry | **0 / 0 / 0 / 0** |
| orphan fighter_records / rankings / statistics / competitors / external_ids | **0 / 0 / 0 / 0 / 0** |
| NULL provider/external_id | **0** |
| unresolved rankings | **0 (142/142 resolve)** |
| consumed registry IDs with a persisted fighter row | **28,988 / 28,988 (100%)** ✓ |
| registry total | 38,011 — unchanged |
| discovery checkpoints | 7/7 COMPLETED — unchanged |
| checkpoints (fighter/ranking/records) | 3/3 COMPLETED — unchanged |

## 6. Before → after / deltas

| Table | Before | After | Δ |
|---|---|---|---|
| fighters | 26,988 | **28,988** | **+2,000** |
| fighter_records | 26,316 | **28,311** | **+1,995** |
| fighters missing records | 672 | 677 | +5 (new genuine absences; residual untouched) |
| statistics | 399 | 399 | 0 |
| rankings | 142 | 142 | 0 |
| competitors | 47 | 47 | 0 |
| external_ids | 27,345 | **29,345** | **+2,000** (2,000 fighters, 0 weight classes) |
| events | 24 | 24 | 0 |
| competitions | 260 | 260 | 0 |
| promotions | 48 | 48 | 0 |
| weight_classes | 25 | 25 | 0 |
| registry total | 38,011 | 38,011 | 0 |
| registry consumed | 26,988 | **28,988** | **+2,000** |
| registry pending | 11,023 | **9,023** | **−2,000** |

## 7. Representative verification (all 6 PASS — untouched)

| Fighter | ext_id | record_summary | W/L/D | KO/TKO | Subs | Fights |
|---|---|---|---|---|---|---|
| Islam Makhachev | 3332412 | 28-1-0 | 28/1/0 | 5 | 13 | 29 |
| Francis Ngannou | 3933168 | 19-3-0 | 19/3/0 | 14 | 4 | 22 |
| Demetrious Johnson | 2512089 | 25-4-1 | 25/4/1 | 5 | 8 | 30 |
| Ronda Rousey | 2563796 | 13-2-0 | 13/2/0 | 3 | 10 | 15 |
| Royce Gracie | 2335697 | 15-2-2 | 15/2/2 | 2 | 11 | 19 |
| Ken Shamrock | 2335653 | 29-17-2 | 29/17/2 | 4 | 22 | 48 |

## 8. Cohort quality (window-8 cohort, verified live)

- Cohort size: **exactly 2,000** fighters (created 15:40:00–15:40:03 UTC — bulk-stamp at flush end; identical pattern to W014's cohort, which was stamped 14:50:46–14:50:48); **1,995 with fighter_records (99.75%)** — top band of observed yields.
- Missing-records members (5, all genuine absences): 4915531 Chris Crail · 4915532 Marcel Valera · 4920440 Ivan Guzman · 5002957 Chad Trukovich · 5003753 Todd Schwarz.
- Sample consistency (record_summary ↔ W/L/D ↔ total_fights all match): 5007659 Peter Varadi Akos 0-1-0/1 · 5007657 Wojciech Marjanski 0-1-0/1 · 5007658 Michal Mokry 0-1-0/1 · 5007664 Kacper Koziorzebski 0-3-0/3 · 5007654 Mikolaj Zukowski 0-1-0/1. No fabricated or internally inconsistent rows observed.

## 9. Performance

| Metric | W012 | W013 | W014 | W015 |
|---|---|---|---|---|
| limit | 2,000 | 2,000 | 2,000 | 2,000 |
| profiles fetched | 2,000 | 2,000 | 2,000 | 2,000 (100% resolved) |
| records fetched | 1,964 real | 1,921 real | 1,991 real | **1,995 real** |
| requests | 4,000 all 200 | 4,000 all 200 | 4,000 all 200 | 4,000 all 200 |
| 404 / 429 / 5xx / retries / breaker | 0 | 0 | 0 | 0 |
| rate | ~3.0 req/s | ~3.0 req/s | ~3.0 req/s | ~3.0 req/s |
| elapsed | 22.3 min | 22.2 min | 22.2 min | 22.2 min |

Behavior materially identical to W008–W014. Record-payload yield: … 98.2 → 96.05 → 99.55 → **99.75%** — continues the recovery trend; W013's dip remains a confirmed one-off placeholder-band artifact.

## 10. Files created / modified

Created: `PRODUCTION_WINDOW_015_CENSUS_BASELINE.json` · `PRODUCTION_WINDOW_015_CENSUS_AFTER.json` · `PRODUCTION_WINDOW_015_CENSUS_SYNC_LOG.txt` · this report · `PRODUCTION_WINDOW_015_CENSUS_POST_AUDIT.md`.
Code: **none modified**. Docs updated: `ESPN_PRODUCTION_JOURNEY.md` (appended §28), `ESPN_HANDOFF_STATE.md`.

## 11. Decision gate: **STOP — no further census window without a new explicit approval**

Window 8 consumed exactly its 2,000-ID budget (registry 28,988 consumed / 9,023 pending). Records backfill remains CLOSED (residual 677 missing untouched). Per the authorization, no further window, no records rerun, no Phase D, no commit/push. Next window (W016, LIMIT=2000 or revised) requires a new decision gate. Next pending ID: **5007665**.

## 12. Git safety

No staged files · no commit · no push. No code drift beyond the documented W007 5-file set. DB writes exclusively the approved bounded census window. `backend/mma_stats.db` verified untouched (0 bytes, unmodified).
