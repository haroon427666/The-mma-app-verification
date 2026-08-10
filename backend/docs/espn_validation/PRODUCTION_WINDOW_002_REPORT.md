# PRODUCTION WINDOW 002 — RUN REPORT

Status: COMPLETED + VERIFIED (window + idempotency rerun)
Date: 2026-08-10
Runs: b86436ab-4303-4123-9ccb-2212d961dbac (window), 0c8c2567-f696-4ed6-9307-6ef25ce751a1 (rerun)
Companion: PRODUCTION_WINDOW_002_PREFLIGHT.json, PRODUCTION_WINDOW_002_AFTER.json,
PRODUCTION_WINDOW_002_DISCOVERY_PROBE.json, PRODUCTION_WINDOW_002_REPRESENTATIVE_TEST.json,
PRODUCTION_WINDOW_002_RANKING_VERIFY.json, PRODUCTION_WINDOW_002_COVERAGE_ANALYSIS.md,
PRODUCTION_WINDOW_002_SYNC_LOG.txt, PRODUCTION_WINDOW_002_RERUN_SYNC_LOG.txt

## Design

- ESPN_FIGHTER_SYNC_LIMIT=2000 (only supported coverage knob; re-processes prefix 0–999
  idempotently and adds sorted positions 1000–1999)
- ESPN_EVENTLOG_ENABLED=0; all other envs at defaults; sync.py --full (10 jobs)
- New band (live read-only probe): external IDs 2,488,769 – 2,502,283

## Window run (b86436ab)

- Status COMPLETED · 1,473,903 ms (24.6 min) · inserted 2,060 · updated 988 · errors 0 · 0 HTTP 429 · 0 retries
- fighter: inserted 1,999 / updated 988 / skipped 1,011 / errors 0 (duration 1,353,657 ms)
- statistic: inserted 31 / skipped 192 · ranking: inserted 18 · historical_event: inserted 12 / skipped 739
- promotion/venue/weight_class/event/competition/broadcast: no inserts, 0 errors

## DB deltas (preflight → after)

| Table | Before | After | Delta |
|---|---|---|---|
| fighters | 1000 | 2000 | +1000 |
| fighter_records | 999 | 1998 | +999 |
| statistics | 368 | 399 | +31 |
| events | 24 | 24 | 0 |
| competitions | 260 | 260 | 0 |
| competitors | 35 | 47 | +12 |
| rankings | 12 | 17 | +5 |
| promotions | 48 | 48 | 0 |
| weight_classes | 17 | 18 | +1 (Super Heavyweight, auto-created by fighter parser) |
| external_ids | 1349 | 2350 | +1001 |

- Fighter external_id range now 2,085,811 – 2,502,283 (planned band exactly)
- 0 duplicates, 0 orphans, 0 null violations; alembic_version 006

## Representative verification

- 33 live ESPN profile probes: all HTTP 200
- Band sample (12 ids): all valid but inactive/obscure athletes (e.g., Charlie West, Norifumi Yamamoto)
- 21 representative fighters: all live; DB↔ESPN names match perfectly for synced reps
  (Jon Jones, Georges St-Pierre, Ken Shamrock, Royce Gracie, Frank Shamrock)
- Ranking truth: ESPN serves 150 ranking DTOs (ufc 133, bellator 7, ifc 10); only fighters
  already synced resolve into the rankings table (17 rows / 13 fighters, e.g. Aldo, Edgar,
  Overeem, Mousasi, Lima, Cyborg, Masvidal, Rory MacDonald, JDS, Mitrione, Bader,
  Dos Anjos, Assuncao) — the ranking job cannot pull fighters into sync

## Rerun (idempotency proof, 0c8c2567)

- Same envs; COMPLETED · 1,474,152 ms · fighter inserted=0 / updated=1,598 / skipped=2,400 · errors 0
- statistic inserted=0 · historical_event inserted=0 · rankings stable at 17 rows
- (ranking counter prints inserted=18 on both runs while the table stays at 17 — one
  add() deduped at flush; no duplicates, no accumulation)

## Observations

1. Coverage advances ONLY via ESPN_FIGHTER_SYNC_LIMIT; naive increments are O(n²) in API cost.
2. The new band contains no famous fighters — ranked/current athletes sit at sorted
   positions 2,167 (Oliveira) through 20,451 (Adesanya); Demetrious Johnson is now in the
   discovery union (position 2480, via PFL roster).
3. Reaching representative fighters requires EITHER one long bounded run (LIMIT≈21000,
   ~35–45 min) or a code change (checkpoint/offset and/or ranking→fighter injection).
   See ESPN_PRODUCTION_JOURNEY.md Decision Gate.

## Verdict

Window 002 SAFE, BOUNDED, COMPLETE, VERIFIED. Database integrity confirmed after both runs.
Next step requires a user decision (continue without code change vs. code change for
targeted/full coverage).
