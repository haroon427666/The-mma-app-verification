# PRODUCTION WINDOW 017 — Census Expansion Report (Window 10)

**Date:** 2026-08-11 (UTC) · **Type:** bounded fighter census window (registry-consuming)
**Command:** `ESPN_FIGHTER_SYNC_LIMIT=2000 python sync.py --full --entity fighter` (env: `PYTHONIOENCODING=utf-8 PYTHONUTF8=1` for console capture)
**DB context:** production = PostgreSQL 18 `localhost:5432/mma` (authoritative; `backend/mma_stats.db` is a 0-byte placeholder from the earlier forensic probe — never production, untouched).

---

## 1. Verdict: **PASS**

Window 10 completed cleanly: `COMPLETED, inserted=3985, updated=0, skipped=0, errors=0`, 1,346,405 ms (~22.4 min). **4,027 API requests (2,000 profiles + 2,027 records) — 4,000×HTTP 200, 27×HTTP 503, 0×404, 0×429, 0 other 5xx; all 27 503s were transient "Backend fetch failed" responses on FIVE athletes' `/records`, each absorbed by the built-in exponential-backoff retry and recovered on the final attempt — 0 retries exhausted, 0 dead-ends, breaker never engaged.** All 7 discovery walks skipped (COMPLETED) — 0 discovery requests. All 2,000 window IDs resolved to fighter profiles (100%); **1,985 carried real record payloads (99.25% yield)**; 15 returned empty payloads (content-dependent absences). Registry consumed advanced exactly +2,000; **consumed↔fighter correspondence 100% (32,988 = 32,988)**.

## 2. Target

Tenth bounded census window: next 2,000 **unconsumed** registry IDs in ascending `external_id` order (deterministic — `discovery.next_window`). Prior state: 38,011 discovered IDs, 30,988 consumed, 7,023 pending (window 9 completed `398180f2`). Same fighter-job mechanism (window-based, crash-safe consumption).

## 3. Baseline (window 10)

`PRODUCTION_WINDOW_017_CENSUS_BASELINE.json` (2026-08-11T16:49:06Z) — fighters 30,988 · fighter_records 30,301 · missing 687 · registry 38,011 (30,988 consumed / 7,023 pending) · external_ids 31,345 · weight_classes 25 · alembic 008 · HEAD `19a87c7`. All integrity checks 0. Preflight 17/17: PostgreSQL reachable (service running, port 5432), live counts matched W016 AFTER exactly (fighters 30,988 · records 30,301 · missing 687 · registry 30,988/7,023/38,011 · next 5110554 · alembic 008 · discovery 7/7 · checkpoints 3/3 · last run `398180f2` COMPLETED · reps 6/6), consumed↔fighter 0 gaps, **no python sync process running**, git main @ `19a87c7` (nothing staged).

## 4. Execution

- **Window:** 2,000 IDs (`5110554…` → `5153043`, ascending — deterministic `next_window` filter)
- **4,027 API requests** — 2,000 athlete profiles + 2,027 `/records` (includes 27 retries; see §5)
- **2,000 fighters inserted** (upsert_batch) · **1,985 fighter_records inserted** · 15 fighters with empty `/records` payloads (never written, never faked)
- **No new weight class** (weight_classes 25 → 25); external_ids delta exactly **+2,000** (2,000 fighters, 0 classes)
- Registry: consumed 30,988 → **32,988 (+2,000)**; pending 7,023 → **5,023 (−2,000)**
- Sync run `e408afbb` COMPLETED (1,346,405 ms ≈ 22.4 min ≈ **3.0 req/s** — inside the validated envelope)
- Checkpoints: fighter/ranking/records all COMPLETED (unchanged)
- **Zero dead-ends:** all 2,000 IDs resolved
- Mode note: strategy logged `mode=incremental` (recent-sync heuristic) — no behavioral impact (registry-window-based job ignores mode)

## 5. Transient 503 episode — fully explained and recovered

A single transient failure burst occurred at 22:01:52–22:01:59 local (17:01 UTC) on **five athletes' `/records` requests**; all were absorbed by the client's exponential-backoff retry and **all succeeded on the final attempt. No payload was lost, no dead-end, no breaker trip (breaker_lines = 0), no error count.**

| Athlete | Endpoint | Failures | Recovery |
|---|---|---|---|
| **5122171** (Mona Ftouhi) | /records | 503s | final attempt → 200; record persisted (0-1-0) |
| **5121866** (Greg Velasco) | /records | 503s | final attempt → 200; record persisted (6-2-0) |
| **5122172** (Martina Gemrani) | /records | 503s | final attempt → 200; record persisted (0-1-0) |
| **5122173** (Antonia Prifti) | /records | 503s | final attempt → 200; record persisted (1-0-0) |
| **5122174** (Oliwia Zaluska) | /records | 503s | final attempt → 200; record persisted (0-1-0) |

All other 2,000 profiles and 1,995 other records: single clean request, HTTP 200. Total request count 4,027 = 4,000 nominal + 27 retries. Same documented transient-503 pattern (W005/W006/W016 experience) handled entirely by the existing retry logic — no operational gap. All five affected records verified persisted in the live DB (see §9).

## 6. Post-window audit — all ✓

| Check | Result |
|---|---|
| duplicate fighters / fighter_records / external_ids / registry | **0 / 0 / 0 / 0** |
| orphan fighter_records / rankings / statistics / competitors / external_ids | **0 / 0 / 0 / 0 / 0** |
| NULL provider/external_id | **0** |
| unresolved rankings | **0 (142/142 resolve)** |
| consumed registry IDs with a persisted fighter row | **32,988 / 32,988 (100%)** ✓ |
| registry total | 38,011 — unchanged |
| discovery checkpoints | 7/7 COMPLETED — unchanged |
| checkpoints (fighter/ranking/records) | 3/3 COMPLETED — unchanged |

## 7. Before → after / deltas

| Table | Before | After | Δ |
|---|---|---|---|
| fighters | 30,988 | **32,988** | **+2,000** |
| fighter_records | 30,301 | **32,286** | **+1,985** |
| fighters missing records | 687 | 702 | +15 (new genuine absences; residual untouched) |
| statistics | 399 | 399 | 0 |
| rankings | 142 | 142 | 0 |
| competitors | 47 | 47 | 0 |
| external_ids | 31,345 | **33,345** | **+2,000** (2,000 fighters, 0 weight classes) |
| events | 24 | 24 | 0 |
| competitions | 260 | 260 | 0 |
| promotions | 48 | 48 | 0 |
| weight_classes | 25 | 25 | 0 |
| registry total | 38,011 | 38,011 | 0 |
| registry consumed | 30,988 | **32,988** | **+2,000** |
| registry pending | 7,023 | **5,023** | **−2,000** |

## 8. Representative verification (all 6 PASS — untouched)

| Fighter | ext_id | record_summary | W/L/D |
|---|---|---|---|
| Islam Makhachev | 3332412 | 28-1-0 | 28/1/0 |
| Francis Ngannou | 3933168 | 19-3-0 | 19/3/0 |
| Demetrious Johnson | 2512089 | 25-4-1 | 25/4/1 |
| Ronda Rousey | 2563796 | 13-2-0 | 13/2/0 |
| Royce Gracie | 2335697 | 15-2-2 | 15/2/2 |
| Ken Shamrock | 2335653 | 29-17-2 | 29/17/2 |

## 9. Cohort quality (window-10 cohort, verified live)

- Cohort size: **exactly 2,000 fighters** (created 17:11:48–17:11:50 UTC — bulk-stamp at flush end; identical pattern to W014–W016); **1,985 with fighter_records (99.25%)** (W016 99.5% · W017 99.25% — still top band, content-dependent).
- Missing-records members (15, all genuine empty payloads — `/records` returned HTTP 200 with empty body): Michael Tate 5120132 · David Tirelli 5120133 · Rafael Ferreira 5124795 · Matt Wynne 5127381 · Mick Maney 5127420 · Dwayne Bess 5141978 · Ross Swanberg 5142168 · David Huyette 5142169 · Larry Carter 5144958 · Bobby Harris 5144969 · Mitch Cadlick 5146910 · Sal Ram 5146911 · Phil Koldyk 5146912 · Jake Maxim 5146925 · Sal Ram 5146929.
- **503-recovered athletes verified persisted:** Greg Velasco 5121866 6-2-0 · Mona Ftouhi 5122171 0-1-0 · Martina Gemrani 5122172 0-1-0 · Antonia Prifti 5122173 1-0-0 · Oliwia Zaluska 5122174 0-1-0 — **no data lost to the transient 503s.**
- Sample consistency (record_summary ↔ W/L/D ↔ total_fights all match): Jairo Pacheco 7-2-0/9 · Maria Laura Alves Fontoura 0-1-0/1 · Anastasiya Svetkivska 1-2-0/3 · A.J. Weber 0-1-0/1 · Zachary Vaci 1-0-0/1. No fabricated or internally inconsistent rows observed.

## 10. Performance

| Metric | W014 | W015 | W016 | W017 |
|---|---|---|---|---|
| limit | 2,000 | 2,000 | 2,000 | 2,000 |
| profiles fetched | 2,000 | 2,000 | 2,000 | 2,000 (100% resolved) |
| records fetched | 1,991 real | 1,995 real | 1,990 real | **1,985 real** |
| requests | 4,000 | 4,000 | 4,006 | **4,027** (incl. 27 retries) |
| non-200 | 0 | 0 | 6×503 | **27×503 (all recovered)** |
| 404 / 429 / 5xx-other / retries-exhausted / breaker | 0 | 0 | 0 | 0 / 0 / 0 / 0 / 0 |
| rate | ~3.0 req/s | ~3.0 req/s | ~3.0 req/s | ~3.0 req/s |
| elapsed | 22.2 min | 22.2 min | 22.3 min | 22.4 min |

Behavior materially identical to W008–W016; the 27 transient 503s (one burst on five `/records`) were handled exactly as designed (W005/W006/W016 precedent) with full recovery — no yield impact beyond the genuine empty-payload floor.

## 11. Files created / modified

Created: `PRODUCTION_WINDOW_017_CENSUS_BASELINE.json` · `PRODUCTION_WINDOW_017_CENSUS_AFTER.json` · `PRODUCTION_WINDOW_017_CENSUS_SYNC_LOG.txt` (4,100 lines) · this report · `PRODUCTION_WINDOW_017_CENSUS_POST_AUDIT.md`.
Code: **none modified**. Docs updated: `ESPN_PRODUCTION_JOURNEY.md` (appended §30), `ESPN_HANDOFF_STATE.md`.

## 12. Decision gate: **STOP — no further census window without a new explicit approval**

Window 10 consumed exactly its 2,000-ID budget (registry 32,988 consumed / 5,023 pending). Records backfill remains CLOSED (residual 702 missing untouched). Per the authorization, no further window, no records rerun, no Phase D, no commit/push. Next window (W018, LIMIT=2000 or revised) requires a new decision gate. Next pending ID: **5153044**.

## 13. Git safety

No staged files · no commit · no push. No code drift beyond the documented W007 5-file set. DB writes exclusively the approved bounded census window. `backend/mma_stats.db` verified untouched (0 bytes, unmodified).
