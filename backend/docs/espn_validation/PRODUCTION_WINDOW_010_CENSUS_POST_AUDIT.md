# POST-AUDIT — PRODUCTION WINDOW 010 (Census Window 3)

**Run:** `746bf41c-4c60-4aa2-abf3-48f890eb979c` · COMPLETED · 2026-08-11 12:17:23 → 12:39:41 UTC · 1,338,777 ms
**Executed:** 2026-08-11 17:17:22 → 17:39:44 local · exit code 0 · log 8,064 lines

---

## 1. Scope
Independent read-only verification of the window-3 census expansion (approved LIMIT=2000). Ran after completion; no production writes. Live DB: `postgresql://mma:mma@localhost:5432/mma`.

## 2. Run record
| field | value |
|---|---|
| id | 746bf41c-4c60-4aa2-abf3-48f890eb979c |
| status | COMPLETED |
| total_inserted | 3,962 |
| total_updated / skipped / errors | 0 / 0 / 0 |
| error | null |
| api_calls | 0 (tracked counter; actual requests = 4,000, verified from log) |

## 3. Log forensics (`PRODUCTION_WINDOW_010_CENSUS_SYNC_LOG.txt`)
- **Profiles fetched: 2,000** — `GET .../v2/sports/mma/athletes/<digits>` lines excluding `/records`
- **Records fetched: 2,000** — all `"/records \"HTTP/1.1 200 OK\""`
- **Non-200 HTTP lines: 0** — zero `HTTP/1.1 (?!200)` matches
- **Errors/retries/breaker/429/5xx: 0** (regex hits were athlete-ID digits, e.g. `4044292`; all INFO-level httpx lines)
- **Discovery: 7/7 "already completed — skipping"** — no discovery requests made
- **End banner:** `✓ fighter inserted=3962 updated=0 skipped=0 errors=0` / `Status: COMPLETED | 1338777ms`
- Rate: 4,000 requests / 1,338.8 s ≈ **3.0 req/s** (inside validated envelope)
- Mode note: `fighter: mode=incremental reason=Recent sync (0h ago)` — heuristic only; fighter job is registry-window-based, mode has no behavioral impact (confirmed in code)

## 4. Database audit (after-state)
All integrity checks **0**; registry total **38,011** unchanged; **consumed 18,988 / pending 19,023**.

| entity | rows |
|---|---|
| fighters | 18,988 |
| fighter_records | 18,473 |
| statistics | 399 |
| rankings | 142 |
| competitors | 47 |
| external_ids | 19,344 |
| events / competitions / promotions | 24 / 260 / 48 |
| weight_classes | 24 |

- duplicate fighters / fighter_records / external_ids / registry: **0 / 0 / 0 / 0**
- orphans (fighter_records, rankings, statistics, competitors, external_ids): **0**
- NULL provider/external_id: **0** · unresolved rankings: **0**
- consumed↔fighter: **18,988 / 18,988 = 100%**
- W3 cohort (created ≥ 12:17:23 UTC): **exactly 2,000 fighters; 1,962 (98.1%) have fighter_records**
- external_ids Δ+2,001 explained: 2,000 fighters + 1 weight_class
- weight_classes Δ+1: "Featherweight - DREAM (65kg)" (external_id 954), created 12:39:40 UTC — inline enrichment for a new DREAM fighter; benign
- checkpoints 3/3 COMPLETED; discovery 7/7 COMPLETED; alembic **008**

## 5. Spot checks
- Representatives (6/6): Makhachev 28-1-0 · Ngannou 19-3-0 · DJ 25-4-1 · Rousey 13-2-0 · Gracie 15-2-2 · Shamrock 29-17-2 — all unchanged, records internally consistent.
- Fresh cohort samples consistent (summary ↔ W/L/D ↔ fights): 4010357 Kurobe 12-6-0/18 · 4010358 Naito 0-1-0/1 · 4010399 Baack 0-3-0/3 · 4010400 Aguiar 0-2-0/2 · 4010402 Silva 0-2-0/2.
- Next-window IDs verified ascending beyond this window.

## 6. Consent / change review
No code, schema, migration, or config change. Only data growth from the approved bounded run plus the two doc files expected to change. Git: HEAD `19a87c7` unchanged; nothing staged; no commit/push.

## 7. Verdict: **PASS** — window 3 fully consistent with W008/W009 behavior; window consumed exactly its budget; no drift, no anomalies, 0 dead-ends, 0 failed requests.
