# PRODUCTION WINDOW 002 — FILE MAP

**Scope:** file-by-file map of the Window 002 production evidence (2026-08-10).
**Location:** `backend/docs/espn_validation/` unless noted; paths relative to repo root.
**Boundaries:** no modification of the committed acceptance evidence (hash-anchored in
`CHECKSUM_MANIFEST.json`); all Window 002 files are new/untracked additions.

## Overview files

| File | Role |
|---|---|
| `backend/ESPN_PRODUCTION_JOURNEY.md` | A-to-Z record: research → code → validation → windows 001/002 → coverage findings → decision gate (A–E) |
| `PRODUCTION_WINDOW_002_REPORT.md` | Window 002 run report (design, results, deltas, observations, verdict) |
| `PRODUCTION_WINDOW_002_TIMELINE.md` | Chronological reconstruction of the session (this package) |
| `PRODUCTION_WINDOW_002_FILE_MAP.md` | This file |
| `PRODUCTION_WINDOW_002_CHECKSUM_MANIFEST.json` | SHA-256 integrity record for all Window 002 artifacts (written last, no self-hash) |

## Pre-run analysis (read-only, no DB writes)

| File | Role |
|---|---|
| `PRODUCTION_WINDOW_002_PREFLIGHT.json` | Read-only DB baseline vs Window 001 AFTER (exact match; alembic 006; 0 dupes/orphans/nulls) |
| `PRODUCTION_WINDOW_002_DISCOVERY_PROBE.json` | Live read-only discovery enumeration: union 38,011; sorted positions of 21 representative fighters; Window 002 band IDs 2,488,769–2,502,283 |
| `PRODUCTION_WINDOW_002_COVERAGE_ANALYSIS.md` | Q1–Q11 analysis (discovery mechanics, window advancement, drift, idempotency, checkpoint gap) |
| `PRODUCTION_WINDOW_002_REPRESENTATIVE_TEST.json` | 33 live ESPN profile probes (12 band sample + 21 reps): HTTP status, name, active flag, DB↔ESPN name match |
| `PRODUCTION_WINDOW_002_RANKING_VERIFY.json` | Live ranking DTO census (150 DTOs: ufc 133, bellator 7, ifc 10) |

## Run evidence (produced by the sync engine)

| File | Role |
|---|---|
| `PRODUCTION_WINDOW_002_SYNC_LOG.txt` | Full log of run `b86436ab-4303-4123-9ccb-2212d961dbac` (COMPLETED, 1,473,903 ms, 2,060 inserted / 988 updated / 0 errors) |
| `PRODUCTION_WINDOW_002_AFTER.json` | Read-only post-run DB audit (row counts, dupes, orphans, nulls, sync_runs, sync_jobs) |
| `PRODUCTION_WINDOW_002_RERUN_SYNC_LOG.txt` | Full log of run `0c8c2567-f696-4ed6-9307-6ef25ce751a1` (COMPLETED, 1,474,152 ms, fighter inserted=0 → idempotency proof) |

## Integrity policy

- `PRODUCTION_WINDOW_002_CHECKSUM_MANIFEST.json` is written **once, last**, after all other
  files are final, and intentionally contains no self-hash (a self-referential hash is circular).
- It covers every file listed above; recompute with:
  `Get-FileHash -Algorithm SHA256 <path>` (Windows) or `sha256sum <path>` (Unix).
- The committed acceptance manifest (`CHECKSUM_MANIFEST.json`) is NOT modified — its hashes
  remain valid for the committed evidence package.
