# VERIFICATION — how to independently verify this acceptance package

## Why `CHECKSUM_MANIFEST.json` has no self-hash (intentional design)

`CHECKSUM_MANIFEST.json` deliberately does **not** contain its own SHA-256.
A self-referential SHA-256 is circular: the hash of the file depends on the file's own
contents, so a manifest that contains its own hash can only be verified against the exact
bytes it was generated from — any modification (even to fix the hash) changes the value.
The integrity/version mechanism for the manifest itself is **git history**: once committed,
the manifest's identity is pinned by its git blob SHA. Verifiers should rely on git, not on
a self-embedded hash.

This decision is documented so a future reviewer does not "fix" the manifest by adding a
self-hash.

## What this package verified at creation time (2026-08-10)

| # | Check | Method | Result |
|---|---|---|---|
| 1 | Accepted commit exists | `git cat-file -t cda302c` | PASS |
| 2 | HEAD tree == accepted tree | `git diff b723c71 cda302c` (empty) | PASS |
| 3 | Commit file list (69 files, 24A/45M) | `git show --name-status cda302c` | PASS |
| 4 | Test-def count 457 (= 455 passed + 2 skipped) | `Select-String "def test_" backend/tests/**` | PASS (consistent with report) |
| 5 | Migration 006 applied | live DB `alembic_version = 006` (read-only query) | PASS |
| 6 | Row counts match report §10 | read-only SELECTs on all tables | PASS (table above) |
| 7 | sync_runs state | 2 runs COMPLETED; durations 141,246.289 / 5,252.951 ms | PASS |
| 8 | sync_jobs state | 20 rows (10 jobs × 2 runs), all COMPLETED | PASS |
| 9 | Manifest JSON valid, all listed hashes match files | `python -m json.tool` + `Get-FileHash` comparison | PASS (see below) |
| 10 | No production file modified | `git status` delta limited to new files under `backend/docs/espn_validation/` | PASS |
| 11 | Frozen research untouched | external workspace; read-only access only | PASS |

## Exact commands for a future reviewer

### 1. Verify the accepted commit

```powershell
git cat-file -t cda302cc6f986aeabfad8ce2f790f5a37667a670          # -> commit
git show --stat --format="%H %an %ad %s" cda302c                  # metadata + file stats
git diff --stat b723c71 cda302c                                   # empty -> HEAD tree identical
git show --name-status cda302c                                    # 69 files (24 A, 45 M)
```

### 2. Verify every hash in the manifest

```powershell
# From repo root. Compares every entry of CHECKSUM_MANIFEST.json against the on-disk file.
$m = Get-Content backend/docs/espn_validation/CHECKSUM_MANIFEST.json -Raw | ConvertFrom-Json
$fail = 0
foreach ($f in $m.files) {
  $actual = (Get-FileHash -Algorithm SHA256 -LiteralPath $f.path).Hash.ToLower()
  if ($actual -ne $f.sha256) { Write-Host "MISMATCH: $($f.path)"; $fail++ }
}
Write-Host "Verified $($m.files.Count) files, mismatches: $fail"
```

### 3. Recompute the manifest's own hash independently

```powershell
Get-FileHash -Algorithm SHA256 backend/docs/espn_validation/CHECKSUM_MANIFEST.json
```

The result is intentionally **not** stored inside the manifest (circular — see above).
Record/compare it via git: `git hash-object backend/docs/espn_validation/CHECKSUM_MANIFEST.json`.

### 4. Validate JSON files parse

```powershell
python -m json.tool backend/docs/espn_validation/VALIDATION_RESULTS.json
python -m json.tool backend/docs/espn_validation/CHECKSUM_MANIFEST.json
```

### 5. Re-verify the live DB (read-only)

```powershell
# Requires psycopg2; credentials per backend/.env.example (mma/mma, db mma, localhost:5432)
# Expected: alembic_version=006; counts per ACCEPTANCE_EVIDENCE.md §C.1; sync_runs per §C.2
```

### 6. Re-run the live acceptance (heavy — only if genuinely needed)

```powershell
cd backend
alembic upgrade head          # already at 006 on the acceptance DB
$env:MMA_LIVE_SYNC=1; pytest tests/integration/test_sync_live.py -v -s
$env:MMA_LIVE_SYNC=1; pytest tests/integration/test_espn_live_probes.py -v -s
python scripts/espn_live_benchmark.py
```

> **Policy note:** the full suite (455+2), ruff, mypy and the live runs were executed at the
> 2026-08-09 validation close and recorded in `ESPN_PRODUCTION_VALIDATION_REPORT.md` §14.
> This package did **not** re-run them (lightweight preservation policy — re-running the live
> sync would mutate the DB and re-probe ESPN). Values are marked REPORTED where not re-run.

## Do-not-redo list (frozen research guidance)

- Do not re-run the 38k-athlete census, classification, or original resolver (~10.6h) — final
  artifacts exist (`ATHLETE_CENSUS_FINAL.json`, `RECONCILIATION.json`, `FINAL_NUMBERS.json`).
- Do not re-run endpoint discovery/benchmarks — `PERFORMANCE_BENCH_FINAL.json` etc. exist.
- Do not modify the frozen research workspace; it is read-only by convention (`FROZEN.md`, `DO_NOT_REDO.md`).
- Do not re-apply migration 006 to the acceptance DB (already applied and verified).
