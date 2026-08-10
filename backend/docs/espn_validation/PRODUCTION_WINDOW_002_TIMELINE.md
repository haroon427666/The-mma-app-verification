# PRODUCTION WINDOW 002 — TIMELINE

**Scope:** chronological reconstruction of the Window 002 production expansion (2026-08-10).
**Author:** live session record (probe scripts + DB run timestamps; run times are DB-anchored).
**Boundaries respected:** no commits, no code changes, no mobile changes, no frozen-research
modification, no unbounded 38k run.

## Session sequence (all times local +05)

| When | Step | What happened | Evidence |
|---|---|---|---|
| Phase 1 | Read all docs | Research tree, evidence package, code (fighter.py, provider.py, client.py, state_store.py, statistics.py, historical_event.py, sync.py), tests | existing docs |
| Phase 2 | Git safety | HEAD `56221cc` on `main`, up to date; commits `cda302c` + `56221cc` verified via `git show --stat`; pre-existing `mobile/` working-tree changes untouched | git log/show |
| Phase 3 | DB preflight | Read-only audit vs Window 001 AFTER — exact match (1000 fighters, 999 records, 368 stats, 24 events, 260 comps, 12 rankings, alembic 006, 0 dupes/orphans/nulls, ID range 2,085,811–2,488,768) | `PRODUCTION_WINDOW_002_PREFLIGHT.json` |
| Phase 4 | Discovery probe | Live read-only enumeration: union = 38,011 IDs (min 2,085,811, max 5,395,233); representative positions computed (Jones 85 … Adesanya 20,451; DJ 2,480 via PFL roster); new band = positions 1000–1999 = IDs 2,488,769–2,502,283; Q1–Q11 analysis written | `PRODUCTION_WINDOW_002_DISCOVERY_PROBE.json` + `PRODUCTION_WINDOW_002_COVERAGE_ANALYSIS.md` |
| Phase 5 | Design | Window 002 = `ESPN_FIGHTER_SYNC_LIMIT=2000`, `ESPN_EVENTLOG_ENABLED=0`, all other envs default (only supported way to advance coverage) | COVERAGE_ANALYSIS Q11 |
| Phase 6 | Representative test | 33 live profile probes (12 band sample + 21 reps): all HTTP 200; band all inactive/obscure; DB↔ESPN names match for synced reps (Jones, GSP, Shamrock, Gracie, Frank Shamrock) | `PRODUCTION_WINDOW_002_REPRESENTATIVE_TEST.json` |
| **16:49:02** | **Window 002 run start** | `sync.py --full`, run `b86436ab-4303-4123-9ccb-2212d961dbac` | `PRODUCTION_WINDOW_002_SYNC_LOG.txt` |
| **17:13:28** | rankings upsert | 18 ranking adds (REPLACE semantics; 17 rows persisted — see report) | log |
| **17:13:36** | **Window 002 run end** | COMPLETED · 1,473,903 ms · 2,060 inserted / 988 updated / 0 errors / 0 HTTP 429 | log + `PRODUCTION_WINDOW_002_AFTER.json` |
| Phase 8 | Post-window audit | fighters 1000→2000, records 999→1998, statistics 368→399, rankings 12→17, competitors 35→47, weight_classes 17→18, external_ids 1349→2350; 0 dupes/orphans/nulls; ID range now to 2,502,283 | `PRODUCTION_WINDOW_002_AFTER.json` |
| Phase 8b | Anomaly checks | Ranking REPLACE semantics confirmed (150 live DTOs: ufc 133, bellator 7, ifc 10; only synced fighters resolve → 17 rows / 13 fighters); "Super Heavyweight" weight class auto-created by fighter parser (id 997) | `PRODUCTION_WINDOW_002_RANKING_VERIFY.json` |
| **17:29:20** | **Rerun start** | Same envs, run `0c8c2567-f696-4ed6-9307-6ef25ce751a1` | `PRODUCTION_WINDOW_002_RERUN_SYNC_LOG.txt` |
| **17:53:34** | **Rerun end** | COMPLETED · 1,474,152 ms · **fighter inserted=0** / updated=1,598 / errors 0 → idempotency proven; rankings stable at 17 | log + final check |
| Phase 10 | Decision gate | A–E classification documented (A=status quo increments, B=one bounded long run LIMIT≈21000, C/D=code changes needing approval, E=stop) | `ESPN_PRODUCTION_JOURNEY.md` §7 |
| Phase 11 | Documentation | `backend/ESPN_PRODUCTION_JOURNEY.md` (A-to-Z) + `PRODUCTION_WINDOW_002_REPORT.md` written | files |
| Phase 12–14 | Naming/verification | All artifacts `PRODUCTION_WINDOW_002_*` / `RERUN_*`; git boundary unchanged (HEAD `56221cc`, nothing staged/committed); companion docs added (this TIMELINE, FILE_MAP, CHECKSUM_MANIFEST) | this package |

## Key numbers

- Runs: 2 (window + rerun), total ≈ 49 min API time, 0 errors, 0 retries, 0 HTTP 429
- Coverage: 1,000 fighters → 2,000 fighters; external IDs 2,085,811–2,502,283
- Representative coverage: 5/21 reps in-window; next rep (Oliveira) at position 2,167
