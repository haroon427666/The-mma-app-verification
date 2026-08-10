# PRODUCTION_WINDOW_002 — COVERAGE ANALYSIS

Status: WORKING ANALYSIS (Phase 4)
Date: 2026-08-10
Companion evidence: PRODUCTION_WINDOW_002_DISCOVERY_PROBE.json (live read-only probe, ~40 ESPN requests)

## Q1. What does the production discovery pipeline actually fetch today?

`ESPNProvider.fetch_athlete_ids()` returns the union of:
1. The global athletes flat listing (`/athletes` pages of 1000, capped at 200 pages → no truncation for 38k ids)
2. Six league rosters: ufc, bellator, pfl, ksw, ifc, ofc (ONE Championship slug)

`FighterSyncJob.run()` then does `ids = sorted(discovered)` and slices
`ids[state.last_offset : state.last_offset + limit]` with `start = 0` on a fresh
process (MemorySyncStateStore is per-process; nothing is persisted across CLI runs).

## Q2. Why does every fresh CLI run re-start at the beginning of the sorted list?

`SyncStateStore` is an in-memory store by default. `DatabaseSyncStateStore` and
`RedisSyncStateStore` are declared but not wired to the CLI / scheduler. Therefore
`last_offset` is always 0 and the fighter job always processes the lowest 1000 ids
(`ESPN_FIGHTER_SYNC_LIMIT` default 1000 in production).

## Q3. How does coverage advance between runs then?

Only by increasing `ESPN_FIGHTER_SYNC_LIMIT`. `LIMIT=2000` → `ids[0:2000]` =
the 1000 ids already synced (idempotent update path) + the next 1000 new ids.
There is no offset/order knob and no checkpointing — this is the ONLY supported way
to grow coverage without a code change.

## Q4. Live probe results (2026-08-10)

- Union today: 38,011 ids (frozen research census: 38,014; net drift −3 over time —
  ESPN's flat listing shifts membership between runs; upsert semantics make this safe).
- Min id 2,085,811, max id 5,395,233. All ids are 7-digit → string sort == numeric sort.
- Window 001 (id sorted positions 0–999) = external ids 2,085,811–2,488,768.
- **Window 002 new band (positions 1000–1999) = external ids 2,488,769–2,502,283.**

## Q5. Representative fighter positions (sorted union, 0-indexed)

| Fighter | ESPN id | Sorted position | Window reachable |
|---|---|---|---|
| Jones | 2335639 | 85 | W001 (already synced) |
| Shamrock | 2335653 | 99 | W001 (already synced) |
| GSP | 2335659 | 105 | W001 (already synced) |
| Gracie | 2335697 | 143 | W001 (already synced) |
| Frank Shamrock | 2431343 | 754 | W001 (already synced) |
| Oliveira | 2504169 | 2167 | LIMIT ≥ 2168 |
| Miocic | 2504951 | 2296 | LIMIT ≥ 2297 |
| Blachowicz | 2506250 | 2345 | LIMIT ≥ 2346 |
| Poirier | 2506549 | 2363 | LIMIT ≥ 2364 |
| Cormier | 2509290 | 2380 | LIMIT ≥ 2381 |
| Demetrious Johnson | 2512089 | 2480 | LIMIT ≥ 2481 |
| Nunes | 2516131 | 2608 | LIMIT ≥ 2609 |
| Rousey | 2563796 | 4780 | LIMIT ≥ 4781 |
| Khabib | 2611557 | 5321 | LIMIT ≥ 5322 |
| McGregor | 3022677 | 7735 | LIMIT ≥ 7736 |
| Cejudo | 3023388 | 7760 | LIMIT ≥ 7761 |
| Usman | 3088812 | 10623 | LIMIT ≥ 10624 |
| Ngannou | 3933168 | 15820 | LIMIT ≥ 15821 |
| Volkanovski | 3949584 | 16094 | LIMIT ≥ 16095 |
| Figueiredo | 4189320 | 18846 | LIMIT ≥ 18847 |
| Adesanya | 4285679 | 20451 | LIMIT ≥ 20452 |

NOTE: Demetrious Johnson is now present in the discovery union (position 2480,
via the PFL roster) — the frozen-research note "rankings only path to DJ" applied to
the flat listing at research time; roster membership has since moved.

## Q6. What will Window 002 actually add?

1000 brand-new external ids in the band 2,488,769–2,502,283, re-validating the
idempotent update path on the already-synced first 1000. **Zero** of the 21
representative fighters fall in the new band — the band is expected to be dominated
by "other league" (non-UFC) profiles per the census classification (27,286 other ids),
some of which may 404 or be non-MMA. Skips are handled gracefully (logged warnings).

## Q7. Can we prioritize ranked/current fighters without a code change?

No. The 12 ESPN P4P/division rankings are processed by the `ranking` job but the
resulting fighter refs are NOT injected into fighter discovery (historical_event.py
only follows rankings → winningFight → events → competitions → competitors for
EVENT data, and skips fighters not already synced). Reaching Adesanya (position
20,451) requires `ESPN_FIGHTER_SYNC_LIMIT` ≥ 20,452 → ~20.5k profile fetches
(≈ 35–45 min at production rate limits, one long run) — technically possible
without code change but far beyond "one next safe window".

## Q8. Idempotency guarantee

Fighter upsert uses `(provider, external_id)` unique constraint; a rerun with the
same LIMIT inserts 0 and updates existing rows. Window 001 evidence already proved
this (run 2: 0 inserted / 100 updated / 100 skipped for the 200-fighter limit;
window rerun at LIMIT=200: 0 inserted / 100 updated / 100 skipped).

## Q9. Checkpointing status

`sync_checkpoints` table exists (empty, 0 rows) and `CheckpointManager` is
implemented but not wired to the CLI. A DB-backed fighter checkpoint (persisted
offset) is REQUIRED before any full 38k-census execution can resume across runs —
out of scope for Window 002 (would be a code change).

## Q10. Drift behavior

Union membership shifts between runs (38,014 → 38,011). Sorted slicing may include
a few ids that were not in the previous run's window and vice versa. Upsert
semantics absorb this; no duplication, no orphans (unique constraints verified).

## Q11. Verdict for Window 002

SAFE and BOUNDED: `ESPN_FIGHTER_SYNC_LIMIT=2000`, eventlog disabled, all other
envs at defaults. Expected deltas: +1000 fighters, +~990 fighter_records,
+statistics for the 200-sample, minimal new events/competitions. Runtime ≈ 15–25
min. Second run at the same LIMIT verifies idempotency (0 inserts expected).
