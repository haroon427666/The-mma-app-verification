# POST-AUDIT — PRODUCTION WINDOW 013 (Census Window 6)

**Run:** `37e7c153-4663-449a-9c53-afd9b2ba5120` · COMPLETED · 2026-08-11 13:52:09 → 14:14:23 UTC · 1,333,871 ms
**Executed:** 2026-08-11 18:52:08 → 19:14:25 local · exit code 0 · log 8,062 lines

---

## 1. Scope
Independent read-only verification of the window-6 census expansion (approved LIMIT=2000). Ran after completion; no production writes. Live DB: `postgresql://mma:mma@localhost:5432/mma`.

## 2. Run record
| field | value |
|---|---|
| id | 37e7c153-4663-449a-9c53-afd9b2ba5120 |
| status | COMPLETED |
| total_inserted | 3,921 |
| total_updated / skipped / errors | 0 / 0 / 0 |
| error | null |
| api_calls | 0 (tracked counter; actual requests = 4,000, verified from log) |

## 3. Log forensics (`PRODUCTION_WINDOW_013_CENSUS_SYNC_LOG.txt`)
- **Profiles fetched: 2,000** — `GET .../v2/sports/mma/athletes/<digits>` lines excluding `/records`
- **Records fetched: 2,000** — all `"/records \"HTTP/1.1 200 OK\""`
- **Non-200 HTTP lines: 0** — zero `HTTP/1.1 (?!200)` matches
- **Error lines / Traceback / breaker: 0**
- **Discovery: 7/7 "already completed — skipping"** (14 skip lines incl. fighter-job repeats) — no discovery requests made
- **End banner:** `✓ fighter inserted=3921 updated=0 skipped=0 errors=0` / `Status: COMPLETED | 1333871ms`
- Rate: 4,000 requests / 1,333.9 s ≈ **3.0 req/s** (inside validated envelope)
- Mode note: `fighter: mode=incremental reason=Recent sync (0h ago)` — heuristic only; fighter job is registry-window-based, mode has no behavioral impact (confirmed in code)

## 4. Database audit (after-state)
All integrity checks **0**; registry total **38,011** unchanged; **consumed 24,988 / pending 13,023**.

| entity | rows |
|---|---|
| fighters | 24,988 |
| fighter_records | 24,325 |
| statistics | 399 |
| rankings | 142 |
| competitors | 47 |
| external_ids | 25,345 |
| events / competitions / promotions | 24 / 260 / 48 |
| weight_classes | 25 |

- duplicate fighters / fighter_records / external_ids / registry: **0 / 0 / 0 / 0**
- orphans (fighter_records, rankings, statistics, competitors, external_ids): **0**
- NULL provider/external_id: **0** · unresolved rankings: **0** (142/142 resolve)
- consumed↔fighter: **24,988 / 24,988 = 100%**
- W6 cohort (created ≥ 13:52:09 UTC): **exactly 2,000 fighters; 1,921 (96.05%) have fighter_records**
- external_ids Δ+2,000 explained: exactly 2,000 fighters, **0 weight classes** (weight_classes unchanged 25)
- **Yield dip root cause (verified, benign):** cohort contains 3 official/placeholder rows — `Judge 1/2/3` (external_ids 4410607–09) — persisted as fighters with NULL record payloads (no fighter_records, no summary). Matches the documented low-ID officials/placeholders pattern (handoff note 3d). No HTTP/operational cause (4,000×200, 0 errors). Remaining +76 absences are genuine empty ESPN payloads.
- checkpoints 3/3 COMPLETED; discovery 7/7 COMPLETED; alembic **008**; sync_runs 25 COMPLETED + 2 stale RUNNING

## 5. Spot checks
- Representatives (6/6): Makhachev 28-1-0 · Ngannou 19-3-0 · DJ 25-4-1 · Rousey 13-2-0 · Gracie 15-2-2 · Shamrock 29-17-2 — all unchanged, records internally consistent.
- Fresh cohort samples consistent (summary ↔ W/L/D ↔ fights): 4410531 Kovalev 0-1-0/1 · 4410698 Tokkos 11-6-0/17 · 4410700 Takizawa 13-11-0/24 · 4683551 Wojcik 12-6-0/18 · 4683546 Haolan 0-6-0/6.
- Next-window IDs verified ascending beyond this window (4683575…).

## 6. Consent / change review
No code, schema, migration, or config change. Only data growth from the approved bounded run plus the two doc files expected to change. Git: HEAD `19a87c7` unchanged; nothing staged; no commit/push.

## 7. Verdict: **PASS** — window 6 fully consistent with W008–W012 behavior; window consumed exactly its budget; no drift, no anomalies, 0 dead-ends, 0 failed requests; the record-yield dip is a genuine content-dependent absence pattern, not an operational issue.
