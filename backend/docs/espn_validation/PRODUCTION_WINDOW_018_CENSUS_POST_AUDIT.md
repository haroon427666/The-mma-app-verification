# POST-AUDIT — PRODUCTION WINDOW 018 (Census Window 11)

**Run:** `7caf5f7b-8879-4538-a775-e4241b3d08c1` · COMPLETED · 2026-08-11 17:17:40 → 17:40:02 UTC · 1,342,109 ms
**Executed:** 2026-08-11 23:17:40 → 23:40:02 local · exit code 0 · log 4,082 lines

---

## 1. Scope
Independent read-only verification of the window-11 census expansion (approved LIMIT=2000). Ran after completion; no production writes. Live DB: `postgresql://mma:mma@localhost:5432/mma` (PostgreSQL 18, service running). `backend/mma_stats.db` is a 0-byte forensic-probe placeholder — verified untouched (size 0, unmodified).

## 2. Run record
| field | value |
|---|---|
| id | 7caf5f7b-8879-4538-a775-e4241b3d08c1 |
| status | COMPLETED |
| total_inserted | 3,897 (2,000 fighters + 1,897 records) |
| total_updated / skipped / errors | 0 / 0 / 0 |
| error | null |
| api_calls | 0 (tracked counter; actual requests = 4,018, verified from log) |

## 3. Log forensics (`PRODUCTION_WINDOW_018_CENSUS_SYNC_LOG.txt`, UTF-8)
- **HTTP 200 OK lines: 4,000** — 2,000 athlete-profile GETs + 2,000 `/records` GETs
- **HTTP 503 lines: 18** — transient "Backend fetch failed" on **SIX athletes' /records** during one burst (22:29:01–22:29:06 local / 17:29 UTC): 5157180, 5157184, 5157186, 5157247, 5157251, 5157252
  - 18 `Retrying` warnings = retry attempts (1s → 2s → 4s backoff); every athlete recovered on a final attempt (all 2,000 records ultimately HTTP 200)
- **HTTP 404: 0 · HTTP 429: 0 · other 5xx: 0**
- **Retries exhausted: 0 · breaker/circuit lines: 0 · Traceback: 0 · [ERROR] lines: 0**
- **Discovery: 7/7 "already completed — skipping"** (14 skip lines incl. fighter-job repeats) — no discovery requests made
- **End banner:** `✓ fighter inserted=3897 updated=0 skipped=0 errors=0` / `Status: COMPLETED | 1342109ms` / `Total: 3897 inserted, 0 updated, 0 errors` / `Sync engine shutdown complete`
- Total requests 4,018 = 4,000 nominal + 18 retries; rate = 4,018 / 1,342.1 s ≈ **3.0 req/s** (inside validated envelope)
- Mode note: `fighter: mode=incremental` (recent-sync heuristic) — registry-window job ignores mode (confirmed in code)

## 4. Database audit (after-state)
All integrity checks **0**; registry total **38,011** unchanged; **consumed 34,988 / pending 3,023**.

| entity | rows |
|---|---|
| fighters | 34,988 |
| fighter_records | 34,183 |
| statistics | 399 |
| rankings | 142 |
| competitors | 47 |
| external_ids | 35,345 |
| events / competitions / promotions | 24 / 260 / 48 |
| weight_classes | 25 |

- duplicate fighters / fighter_records / external_ids / registry: **0 / 0 / 0 / 0**
- orphans (fighter_records, rankings, statistics, competitors, external_ids): **0**
- NULL provider/external_id: **0** · unresolved rankings: **0** (142/142 resolve)
- consumed↔fighter: **34,988 / 34,988 = 100%** (consumed_no_fighter = 0; fighter_not_in_registry = 0)
- W11 cohort (created 17:40:00–17:40:02 UTC): **exactly 2,000 fighters; 1,897 (94.85%) have fighter_records**. **Yield dip EXPLAINED (benign):** 82 of the 103 missing are one placeholder band — consecutive roster IDs **5238536–5238638** mapping to **"Mongi Zitouni" / "Ludovic Dandine"** (officials/placeholder pattern, cf. W013 "Judge 1/2/3", at larger scale; consistent with a large card's per-slot roster entries). Remaining 21 genuine scattered absences (e.g. Kerri Rowland 5156789 · Felicia Oh 5199592 · Hadi Mohamed Ali 5222349). All empty payloads were HTTP 200; **0 fabricated rows**.
- external_ids Δ+2,000 explained: exactly 2,000 fighters, **0 weight classes** (weight_classes unchanged 25)
- checkpoints 3/3 COMPLETED; discovery 7/7 COMPLETED; alembic **008**; sync_runs 30 COMPLETED + 2 stale RUNNING (pre-existing, cosmetic)
- created_at bulk-stamp pattern matches W014–W017 (all cohort rows stamped 17:40:00–17:40:02) — normal flush behavior, not an anomaly

## 5. Spot checks
- **Recovered athletes verified in DB (all 6):** 5157180 Mateusz Grzezolkowski 0-1-0 · 5157184 Lukasz Stanek 0-1-0 · 5157186 Henry Fadipe 0-1-0 · 5157247 Manolo Zecchini 11-5-0 · 5157251 Sufiev Karomatullo 1-0-0 · 5157252 Guilherme Neto 0-1-0 — **no data lost to the transient 503s.**
- Representatives (6/6): Makhachev 28-1-0 · Ngannou 19-3-0 · DJ 25-4-1 · Rousey 13-2-0 · Gracie 15-2-2 · Shamrock 29-17-2 — all unchanged, records internally consistent.
- Fresh cohort samples consistent (summary ↔ W/L/D ↔ fights): 5153044 Oswaldo Castillo 0-1-0/1 · 5153082 Daniel Frunza 9-4-0/13 · 5153227 Fakhreddin Myrzadavlatov 0-0-1/1 · 5153229 Mashrapjon Sabirov 0-1-0/1 · 5153231 TJ Welch 0-3-0/3.
- Next-window IDs verified ascending beyond this window (5238639…); window band consumed = exactly 5153044 → 5238638 (2,000 IDs).

## 6. Consent / change review
No code, schema, migration, or config change. Only data growth from the approved bounded run plus the two doc files expected to change. Git: HEAD `19a87c7` unchanged; nothing staged; no commit/push. `backend/mma_stats.db` untouched (0 bytes).

## 7. Verdict: **PASS** — window 11 fully consistent with W008–W017 behavior; window consumed exactly its budget; no drift, no anomalies, 0 dead-ends, 0 lost payloads (the 18 transient 503s on six athletes' /records recovered by the built-in retry logic — all six records verified persisted); record yield 94.85% with the dip fully explained by the placeholder band (W013 precedent); no side effects.
