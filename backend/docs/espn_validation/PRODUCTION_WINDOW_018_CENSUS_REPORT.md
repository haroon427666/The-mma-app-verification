# PRODUCTION WINDOW 018 — Census Expansion Report (Window 11)

**Date:** 2026-08-11 (UTC) · **Type:** bounded fighter census window (registry-consuming)
**Command:** `ESPN_FIGHTER_SYNC_LIMIT=2000 python sync.py --full --entity fighter` (env: `PYTHONIOENCODING=utf-8 PYTHONUTF8=1` for console capture)
**DB context:** production = PostgreSQL 18 `localhost:5432/mma` (authoritative; `backend/mma_stats.db` is a 0-byte placeholder from the earlier forensic probe — never production, untouched).

---

## 1. Verdict: **PASS**

Window 11 completed cleanly: `COMPLETED, inserted=3897, updated=0, skipped=0, errors=0`, 1,342,109 ms (~22.4 min). **4,018 API requests (2,000 profiles + 2,018 records) — 4,000×HTTP 200, 18×HTTP 503, 0×404, 0×429, 0 other 5xx; all 18 503s were transient "Backend fetch failed" responses on SIX athletes' `/records`, each absorbed by the built-in exponential-backoff retry and recovered on the final attempt — 0 retries exhausted, 0 dead-ends, breaker never engaged.** All 7 discovery walks skipped (COMPLETED) — 0 discovery requests. All 2,000 window IDs resolved to fighter profiles (100%); **1,897 carried real record payloads (94.85% yield)**; 103 returned empty payloads — **the dip is fully explained: 82 are a single placeholder band (consecutive roster IDs 5238536–5238638 mapping to "Mongi Zitouni"/"Ludovic Dandine" — the documented officials/placeholder pattern, cf. W013, at larger scale) plus 21 genuine scattered absences; 0 fabricated rows, all empty payloads were HTTP 200**. Registry consumed advanced exactly +2,000; **consumed↔fighter correspondence 100% (34,988 = 34,988)**.

## 2. Target

Eleventh bounded census window: next 2,000 **unconsumed** registry IDs in ascending `external_id` order (deterministic — `discovery.next_window`). Prior state: 38,011 discovered IDs, 32,988 consumed, 5,023 pending (window 10 completed `e408afbb`). Same fighter-job mechanism (window-based, crash-safe consumption).

## 3. Baseline (window 11)

`PRODUCTION_WINDOW_018_CENSUS_BASELINE.json` (2026-08-11T17:17:21Z) — fighters 32,988 · fighter_records 32,286 · missing 702 · registry 38,011 (32,988 consumed / 5,023 pending) · external_ids 33,345 · weight_classes 25 · alembic 008 · HEAD `19a87c7`. All integrity checks 0. Preflight 17/17: PostgreSQL reachable (service running, port 5432), live counts matched W017 AFTER exactly (fighters 32,988 · records 32,286 · missing 702 · registry 32,988/5,023/38,011 · next 5153044 · alembic 008 · discovery 7/7 · checkpoints 3/3 · last run `e408afbb` COMPLETED · reps 6/6), consumed↔fighter 0 gaps, **no python sync process running**, git main @ `19a87c7` (nothing staged).

## 4. Execution

- **Window:** 2,000 IDs (`5153044…` → `5238638`, ascending — deterministic `next_window` filter)
- **4,018 API requests** — 2,000 athlete profiles + 2,018 `/records` (includes 18 retries; see §5)
- **2,000 fighters inserted** (upsert_batch) · **1,897 fighter_records inserted** · 103 fighters with empty `/records` payloads (never written, never faked)
- **No new weight class** (weight_classes 25 → 25); external_ids delta exactly **+2,000** (2,000 fighters, 0 classes)
- Registry: consumed 32,988 → **34,988 (+2,000)**; pending 5,023 → **3,023 (−2,000)**
- Sync run `7caf5f7b` COMPLETED (1,342,109 ms ≈ 22.4 min ≈ **3.0 req/s** — inside the validated envelope)
- Checkpoints: fighter/ranking/records all COMPLETED (unchanged)
- **Zero dead-ends:** all 2,000 IDs resolved
- Mode note: strategy logged `mode=incremental` (recent-sync heuristic) — no behavioral impact (registry-window-based job ignores mode)

## 5. Transient 503 episode — fully explained and recovered

A transient failure burst occurred at 22:29:01–22:29:06 local (17:29 UTC) on **six athletes' `/records` requests**; all were absorbed by the client's exponential-backoff retry and **all succeeded on the final attempt. No payload was lost, no dead-end, no breaker trip (breaker_lines = 0), no error count.**

| Athlete | Endpoint | Recovery (verified persisted) |
|---|---|---|
| **5157180** (Mateusz Grzezolkowski) | /records | final attempt → 200; record persisted (0-1-0) |
| **5157184** (Lukasz Stanek) | /records | final attempt → 200; record persisted (0-1-0) |
| **5157186** (Henry Fadipe) | /records | final attempt → 200; record persisted (0-1-0) |
| **5157247** (Manolo Zecchini) | /records | final attempt → 200; record persisted (11-5-0) |
| **5157251** (Sufiev Karomatullo) | /records | final attempt → 200; record persisted (1-0-0) |
| **5157252** (Guilherme Neto) | /records | final attempt → 200; record persisted (0-1-0) |

All other 2,000 profiles and 1,994 other records: single clean request, HTTP 200. Total request count 4,018 = 4,000 nominal + 18 retries. Same documented transient-503 pattern (W005/W006/W016/W017 experience) handled entirely by the existing retry logic — no operational gap. All six affected records verified persisted in the live DB (see §9).

## 6. Post-window audit — all ✓

| Check | Result |
|---|---|
| duplicate fighters / fighter_records / external_ids / registry | **0 / 0 / 0 / 0** |
| orphan fighter_records / rankings / statistics / competitors / external_ids | **0 / 0 / 0 / 0 / 0** |
| NULL provider/external_id | **0** |
| unresolved rankings | **0 (142/142 resolve)** |
| consumed registry IDs with a persisted fighter row | **34,988 / 34,988 (100%)** ✓ |
| registry total | 38,011 — unchanged |
| discovery checkpoints | 7/7 COMPLETED — unchanged |
| checkpoints (fighter/ranking/records) | 3/3 COMPLETED — unchanged |

## 7. Before → after / deltas

| Table | Before | After | Δ |
|---|---|---|---|
| fighters | 32,988 | **34,988** | **+2,000** |
| fighter_records | 32,286 | **34,183** | **+1,897** |
| fighters missing records | 702 | 805 | +103 (82 placeholder-band + 21 genuine absences; residual untouched) |
| statistics | 399 | 399 | 0 |
| rankings | 142 | 142 | 0 |
| competitors | 47 | 47 | 0 |
| external_ids | 33,345 | **35,345** | **+2,000** (2,000 fighters, 0 weight classes) |
| events | 24 | 24 | 0 |
| competitions | 260 | 260 | 0 |
| promotions | 48 | 48 | 0 |
| weight_classes | 25 | 25 | 0 |
| registry total | 38,011 | 38,011 | 0 |
| registry consumed | 32,988 | **34,988** | **+2,000** |
| registry pending | 5,023 | **3,023** | **−2,000** |

## 8. Representative verification (all 6 PASS — untouched)

| Fighter | ext_id | record_summary | W/L/D |
|---|---|---|---|
| Islam Makhachev | 3332412 | 28-1-0 | 28/1/0 |
| Francis Ngannou | 3933168 | 19-3-0 | 19/3/0 |
| Demetrious Johnson | 2512089 | 25-4-1 | 25/4/1 |
| Ronda Rousey | 2563796 | 13-2-0 | 13/2/0 |
| Royce Gracie | 2335697 | 15-2-2 | 15/2/2 |
| Ken Shamrock | 2335653 | 29-17-2 | 29/17/2 |

## 9. Cohort quality (window-11 cohort, verified live)

- Cohort size: **exactly 2,000 fighters** (created 17:40:00–17:40:02 UTC — bulk-stamp at flush end; identical pattern to W014–W017); **1,897 with fighter_records (94.85%)**.
- **Yield dip EXPLAINED (benign):** 82 of the 103 missing are a single placeholder band — consecutive roster IDs **5238536–5238638** mapping to **"Mongi Zitouni" / "Ludovic Dandine"** (officials/placeholder pattern, cf. W013's "Judge 1/2/3", at larger scale — consistent with a large card's per-slot roster entries). Remaining 21 are genuine scattered absences (e.g. Kerri Rowland 5156789 · Felicia Oh 5199592 · Hadi Mohamed Ali 5222349). All empty payloads returned HTTP 200; **0 fabricated rows.**
- **503-recovered athletes verified persisted (6/6):** 5157180 Grzezolkowski 0-1-0 · 5157184 Stanek 0-1-0 · 5157186 Fadipe 0-1-0 · 5157247 Zecchini 11-5-0 · 5157251 Karomatullo 1-0-0 · 5157252 Neto 0-1-0 — **no data lost to the transient 503s.**
- Sample consistency (record_summary ↔ W/L/D ↔ total_fights all match): Oswaldo Castillo 0-1-0/1 · Daniel Frunza 9-4-0/13 · Fakhreddin Myrzadavlatov 0-0-1/1 · Mashrapjon Sabirov 0-1-0/1 · TJ Welch 0-3-0/3. No fabricated or internally inconsistent rows observed.

## 10. Performance

| Metric | W015 | W016 | W017 | W018 |
|---|---|---|---|---|
| limit | 2,000 | 2,000 | 2,000 | 2,000 |
| profiles fetched | 2,000 | 2,000 | 2,000 | 2,000 (100% resolved) |
| records fetched | 1,995 real | 1,990 real | 1,985 real | **1,897 real** |
| requests | 4,000 | 4,006 | 4,027 | **4,018** (incl. 18 retries) |
| non-200 | 0 | 6×503 | 27×503 | **18×503 (all recovered)** |
| 404 / 429 / 5xx-other / retries-exhausted / breaker | 0 | 0 | 0 | 0 / 0 / 0 / 0 / 0 |
| rate | ~3.0 req/s | ~3.0 req/s | ~3.0 req/s | ~3.0 req/s |
| elapsed | 22.2 min | 22.3 min | 22.4 min | 22.4 min |

Behavior materially identical to W008–W017; the 18 transient 503s (one burst on six `/records`) were handled exactly as designed with full recovery. **The 94.85% yield dip is content-dependent (placeholder band), matching the W013 precedent — not a trend or anomaly.**

## 11. Files created / modified

Created: `PRODUCTION_WINDOW_018_CENSUS_BASELINE.json` · `PRODUCTION_WINDOW_018_CENSUS_AFTER.json` · `PRODUCTION_WINDOW_018_CENSUS_SYNC_LOG.txt` (4,082 lines) · this report · `PRODUCTION_WINDOW_018_CENSUS_POST_AUDIT.md`.
Code: **none modified**. Docs updated: `ESPN_PRODUCTION_JOURNEY.md` (appended §31), `ESPN_HANDOFF_STATE.md`.

## 12. Decision gate: **STOP — no further census window without a new explicit approval**

Window 11 consumed exactly its 2,000-ID budget (registry 34,988 consumed / 3,023 pending). Records backfill remains CLOSED (residual 805 missing untouched). Per the authorization, no further window, no records rerun, no Phase D, no commit/push. Next window (W019, LIMIT=2000 or revised) requires a new decision gate. Next pending ID: **5238639**.

## 13. Git safety

No staged files · no commit · no push. No code drift beyond the documented W007 5-file set. DB writes exclusively the approved bounded census window. `backend/mma_stats.db` verified untouched (0 bytes, unmodified).
