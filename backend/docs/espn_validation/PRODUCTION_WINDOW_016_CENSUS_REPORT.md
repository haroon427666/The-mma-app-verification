# PRODUCTION WINDOW 016 — Census Expansion Report (Window 9)

**Date:** 2026-08-11 (UTC) · **Type:** bounded fighter census window (registry-consuming)
**Command:** `ESPN_FIGHTER_SYNC_LIMIT=2000 python sync.py --full --entity fighter` (env: `PYTHONIOENCODING=utf-8` for console capture)
**DB context:** production = PostgreSQL 18 `localhost:5432/mma` (authoritative; `backend/mma_stats.db` is a 0-byte placeholder from the earlier forensic probe — never production, untouched).

---

## 1. Verdict: **PASS**

Window 9 completed cleanly: `COMPLETED, inserted=3990, updated=0, skipped=0, errors=0`, 1,340,414 ms (~22.3 min). **4,006 API requests (2,003 profiles + 2,003 records) — 4,000×HTTP 200, 6×HTTP 503, 0×404, 0×429, 0 other 5xx; all six 503s were transient "Backend fetch failed" responses on TWO athletes, each absorbed by the built-in exponential-backoff retry (3 retries each) and recovered successfully on the final attempt — 0 retries exhausted, 0 dead-ends, breaker never engaged.** All 7 discovery walks skipped (COMPLETED) — 0 discovery requests. All 2,000 window IDs resolved to fighter profiles (100%); **1,990 carried real record payloads (99.5% yield — top band)**; 10 returned empty payloads (content-dependent absences). Registry consumed advanced exactly +2,000; **consumed↔fighter correspondence 100% (30,988 = 30,988)**.

## 2. Target

Ninth bounded census window: next 2,000 **unconsumed** registry IDs in ascending `external_id` order (deterministic — `discovery.next_window`). Prior state: 38,011 discovered IDs, 28,988 consumed, 9,023 pending (window 8 completed `24f66550`). Same fighter-job mechanism (window-based, crash-safe consumption).

## 3. Baseline (window 9)

`PRODUCTION_WINDOW_016_CENSUS_BASELINE.json` (2026-08-11T15:58:17Z) — fighters 28,988 · fighter_records 28,311 · missing 677 · registry 38,011 (28,988 consumed / 9,023 pending) · external_ids 29,345 · weight_classes 25 · alembic 008 · HEAD `19a87c7`. All integrity checks 0. Preflight 9/9: PostgreSQL reachable (service `postgresql-x64-18` Running, port 5432 open), DSN `postgresql://mma:mma@localhost:5432/mma`, live counts matched W015 AFTER exactly (fighters 28,988 · records 28,311 · missing 677 · registry 28,988/9,023/38,011 · next 5007665 · alembic 008 · discovery 7/7 · checkpoints 3/3 · last run `24f66550` COMPLETED), consumed↔fighter 0 gaps, no python sync process running, git main @ `19a87c7` (nothing staged).

## 4. Execution

- **Window:** 2,000 IDs (`5007665…` → `5110553`, ascending — deterministic `next_window` filter)
- **4,006 API requests** — 2,003 athlete profiles + 2,003 `/records` (includes retries; see §5)
- **2,000 fighters inserted** (upsert_batch) · **1,990 fighter_records inserted** · 10 fighters with empty `/records` payloads (never written, never faked)
- **No new weight class** (weight_classes 25 → 25); external_ids delta exactly **+2,000** (2,000 fighters, 0 classes)
- Registry: consumed 28,988 → **30,988 (+2,000)**; pending 9,023 → **7,023 (−2,000)**
- Sync run `398180f2` COMPLETED (1,340,414 ms ≈ 22.3 min ≈ **3.0 req/s** — inside the validated envelope)
- Checkpoints: fighter/ranking/records all COMPLETED (unchanged)
- **Zero dead-ends:** all 2,000 IDs resolved
- Mode note: strategy logged `mode=incremental` (recent-sync heuristic) — no behavioral impact (registry-window-based job ignores mode)

## 5. Transient 503 episodes — fully explained and recovered

Two isolated transient failures occurred; both were absorbed by the client's exponential-backoff retry (1s → 2s → 4s) and **both succeeded on the final attempt. No payload was lost, no dead-end, no breaker trip (breaker_lines = 0), no error count.**

| Athlete | Endpoint | Failures | Recovery |
|---|---|---|---|
| **5100131** (Marcio Candido da Silva) | profile | 3×503 (21:08:05 → 21:08:06 → 21:08:09) | **4th request 21:08:14 → 200**; fighter + records both persisted |
| **5099363** (Adel Atama) | /records | 3×503 (21:19:05 → 21:19:06 → 21:19:09) | **4th request 21:19:14 → 200**; record persisted (0-1-0/1) |

All other 2,000 profiles and 2,000 records: single clean request, HTTP 200. Total request count 4,006 = 4,000 nominal + 6 retries. This is the documented transient-503 pattern (W005/W006 experience) handled entirely by the existing retry logic — no operational gap.

## 6. Post-window audit — all ✓

| Check | Result |
|---|---|
| duplicate fighters / fighter_records / external_ids / registry | **0 / 0 / 0 / 0** |
| orphan fighter_records / rankings / statistics / competitors / external_ids | **0 / 0 / 0 / 0 / 0** |
| NULL provider/external_id | **0** |
| unresolved rankings | **0 (142/142 resolve)** |
| consumed registry IDs with a persisted fighter row | **30,988 / 30,988 (100%)** ✓ |
| registry total | 38,011 — unchanged |
| discovery checkpoints | 7/7 COMPLETED — unchanged |
| checkpoints (fighter/ranking/records) | 3/3 COMPLETED — unchanged |

## 7. Before → after / deltas

| Table | Before | After | Δ |
|---|---|---|---|
| fighters | 28,988 | **30,988** | **+2,000** |
| fighter_records | 28,311 | **30,301** | **+1,990** |
| fighters missing records | 677 | 687 | +10 (new genuine absences; residual untouched) |
| statistics | 399 | 399 | 0 |
| rankings | 142 | 142 | 0 |
| competitors | 47 | 47 | 0 |
| external_ids | 29,345 | **31,345** | **+2,000** (2,000 fighters, 0 weight classes) |
| events | 24 | 24 | 0 |
| competitions | 260 | 260 | 0 |
| promotions | 48 | 48 | 0 |
| weight_classes | 25 | 25 | 0 |
| registry total | 38,011 | 38,011 | 0 |
| registry consumed | 28,988 | **30,988** | **+2,000** |
| registry pending | 9,023 | **7,023** | **−2,000** |

## 8. Representative verification (all 6 PASS — untouched)

| Fighter | ext_id | record_summary | W/L/D | KO/TKO | Subs | Fights |
|---|---|---|---|---|---|---|
| Islam Makhachev | 3332412 | 28-1-0 | 28/1/0 | 5 | 13 | 29 |
| Francis Ngannou | 3933168 | 19-3-0 | 19/3/0 | 14 | 4 | 22 |
| Demetrious Johnson | 2512089 | 25-4-1 | 25/4/1 | 5 | 8 | 30 |
| Ronda Rousey | 2563796 | 13-2-0 | 13/2/0 | 3 | 10 | 15 |
| Royce Gracie | 2335697 | 15-2-2 | 15/2/2 | 2 | 11 | 19 |
| Ken Shamrock | 2335653 | 29-17-2 | 29/17/2 | 4 | 22 | 48 |

## 9. Cohort quality (window-9 cohort, verified live)

- Cohort size: **exactly 2,000 fighters** (created 16:20:52–16:20:55 UTC — bulk-stamp at flush end; identical pattern to W014/W015); **1,990 with fighter_records (99.5%)** — top band (W014 99.55% · W015 99.75% · W016 99.5%).
- Missing-records members (10, all genuine empty payloads — their `/records` returned HTTP 200 with empty body): Larry Folsom 5025548 · Eric Curcio 5058264 · Joel Ojeda 5077133 · Jason Stafin 5077173 · Seth Fuller 5085178 · Aaron Menard 5085202 · Eliot Kelly 5088615 · Tyler Tomlinson 5092412 · Steve Faragher 5092485 · Loic Pora 5098329.
- Sample consistency (record_summary ↔ W/L/D ↔ total_fights all match): Tiago Terra Nova 0-1-0/1 · Auro Silva 0-1-0/1 · Iwanderson da Silva Caldas 0-1-0/1 · Omoyele Gonzalez 3-3-0/6 · Willian Martins 0-1-0/1. No fabricated or internally inconsistent rows observed.

## 10. Performance

| Metric | W013 | W014 | W015 | W016 |
|---|---|---|---|---|
| limit | 2,000 | 2,000 | 2,000 | 2,000 |
| profiles fetched | 2,000 | 2,000 | 2,000 | 2,000 (100% resolved; +3 retries) |
| records fetched | 1,921 real | 1,991 real | 1,995 real | **1,990 real** (+3 retries) |
| requests | 4,000 | 4,000 | 4,000 | **4,006** (incl. 6 retries) |
| non-200 | 0 | 0 | 0 | **6×503 (both recovered)** |
| 404 / 429 / 5xx-other / retries-exhausted / breaker | 0 | 0 | 0 | 0 / 0 / 0 / 0 / 0 |
| rate | ~3.0 req/s | ~3.0 req/s | ~3.0 req/s | ~3.0 req/s |
| elapsed | 22.2 min | 22.2 min | 22.2 min | 22.3 min |

Behavior materially identical to W008–W015; the 6 transient 503s were handled exactly as designed (W005/W006 precedent) with full recovery — no yield impact beyond the genuine empty-payload floor.

## 11. Files created / modified

Created: `PRODUCTION_WINDOW_016_CENSUS_BASELINE.json` · `PRODUCTION_WINDOW_016_CENSUS_AFTER.json` · `PRODUCTION_WINDOW_016_CENSUS_SYNC_LOG.txt` · this report · `PRODUCTION_WINDOW_016_CENSUS_POST_AUDIT.md`.
Code: **none modified**. Docs updated: `ESPN_PRODUCTION_JOURNEY.md` (appended §29), `ESPN_HANDOFF_STATE.md`.

## 12. Decision gate: **STOP — no further census window without a new explicit approval**

Window 9 consumed exactly its 2,000-ID budget (registry 30,988 consumed / 7,023 pending). Records backfill remains CLOSED (residual 687 missing untouched). Per the authorization, no further window, no records rerun, no Phase D, no commit/push. Next window (W017, LIMIT=2000 or revised) requires a new decision gate. Next pending ID: **5110554**.

## 13. Git safety

No staged files · no commit · no push. No code drift beyond the documented W007 5-file set. DB writes exclusively the approved bounded census window. `backend/mma_stats.db` verified untouched (0 bytes, unmodified).
