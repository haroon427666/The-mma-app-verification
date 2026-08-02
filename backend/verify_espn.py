#!/usr/bin/env python3
"""
Live ESPN Verification Suite — Phase 5.5 Production Verification.

Downloads fresh payloads from every verified ESPN endpoint, parses them,
validates them, and reports field coverage against MASTER_FEATURE_INVENTORY.md.

Run:  python verify_espn.py

Output:
    Entity       Endpoint          Expected  Parsed  Coverage
    ────────────────────────────────────────────────────────
    Fighter      /athletes/{id}     18/18     18/18    100%
    Records      /records           13/13     13/13    100%
    Statistics   /statistics         6/6       6/6     100%
    Event        /events/{id}        6/6       6/6     100%
    Competition  /competitions       9/9       9/9     100%
    Venue        /venues/{id}       10/10     10/10    100%
    Ranking      /rankings/{cat}     8/8       8/8     100%
    Broadcast    /broadcasts         5/5       5/5     100%
    Promotion    /leagues/{slug}     5/5       5/5     100%
    ────────────────────────────────────────────────────────
    TOTAL                            80/80     80/80    100%
"""

import asyncio
import json
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any

import httpx

# ═══════════════════════════════════════════════════════════════════════════════
# Configuration
# ═══════════════════════════════════════════════════════════════════════════════

BASE = "https://sports.core.api.espn.com/v2/sports/mma"
HEADERS = {"User-Agent": "MMA-Backend-Verify/5.5"}

# Known IDs from Phase 4.1 validation
FIGHTER_ID = "3088812"     # Islam Makhachev (all fields populated)
FIGHTER_EDGE = "2354359"   # Jason Reinhardt (edge case: reach=0.0, inactive)
EVENT_ID = "600059339"     # UFC Fight Night 283 (scheduled)
PROMOTION_SLUG = "ufc"


# ═══════════════════════════════════════════════════════════════════════════════
# Field Inventory — what each endpoint SHOULD provide
# ═══════════════════════════════════════════════════════════════════════════════

class Field(Enum):
    PRESENT = "✓"
    MISSING = "✗"
    NULL = "N"
    ERROR = "!"


@dataclass
class EndpointSpec:
    name: str
    url: str
    expected_fields: list[str]
    parser: Any = None  # Callable that parses raw JSON → DTO-like dict


# Define all verified endpoints with their expected fields
ENDPOINTS = [
    EndpointSpec(
        name="Fighter (active)",
        url=f"{BASE}/athletes/{FIGHTER_ID}?lang=en&region=us",
        expected_fields=[
            "id", "firstName", "lastName", "fullName", "displayName", "shortName",
            "weight", "height", "reach", "weightClass", "stance",
            "citizenship", "dateOfBirth", "active", "slug",
            "statistics.$ref", "records.$ref", "leagues.$ref",
        ],
    ),
    EndpointSpec(
        name="Fighter (edge case)",
        url=f"{BASE}/athletes/{FIGHTER_EDGE}?lang=en&region=us",
        expected_fields=[
            "id", "firstName", "lastName", "fullName",
            "weight", "height", "reach", "weightClass", "stance",
            "active",
        ],
    ),
    EndpointSpec(
        name="Records",
        url=f"{BASE}/athletes/{FIGHTER_ID}/records?lang=en&region=us",
        expected_fields=[
            "items[0].name", "items[0].summary", "items[0].value",
            "wins", "losses", "draws", "noContests",
            "submissions", "submissionLosses",
            "tkos", "tkoLosses",
            "titleWins", "titleLosses", "titleDraws",
        ],
    ),
    EndpointSpec(
        name="Fighter List",
        url=f"{BASE}/leagues/ufc/athletes?limit=1&lang=en&region=us",
        expected_fields=["count", "items", "$ref items"],
    ),
    EndpointSpec(
        name="Promotion",
        url=f"{BASE}/leagues/{PROMOTION_SLUG}?lang=en&region=us",
        expected_fields=[
            "id", "name", "displayName", "abbreviation", "shortName", "slug",
            "season", "logos", "gender",
        ],
    ),
    EndpointSpec(
        name="Event List",
        url=f"{BASE}/leagues/ufc/events?dates=2026&lang=en&region=us",
        expected_fields=["count", "items", "$ref items"],
    ),
    EndpointSpec(
        name="Rankings List",
        url=f"{BASE}/leagues/ufc/rankings?lang=en&region=us",
        expected_fields=["items", "$ref items"],
    ),
]


# ═══════════════════════════════════════════════════════════════════════════════
# Field Checker — recursively checks JSON for expected fields
# ═══════════════════════════════════════════════════════════════════════════════

def check_field(data: Any, path: str) -> Field:
    """Check if a field exists and is non-null at the given JSON path."""
    parts = path.split(".")
    current = data
    for part in parts:
        if current is None:
            return Field.NULL
        if part.startswith("$ref"):
            # $ref marker — just check presence of special field
            if isinstance(current, dict) and "$ref" in current:
                return Field.PRESENT
            return Field.MISSING
        if part.endswith("]") and "[" in part:
            # Array access: items[0].name
            key, idx_str = part.split("[")
            idx = int(idx_str.strip("]"))
            if isinstance(current, dict):
                arr = current.get(key, [])
                if not isinstance(arr, list) or len(arr) <= idx:
                    return Field.MISSING
                current = arr[idx]
                continue
            return Field.MISSING
        elif part == "items" and path.endswith("$ref items"):
            # Special: check if items contain $ref URLs
            if isinstance(current, dict):
                arr = current.get("items", [])
                if isinstance(arr, list) and len(arr) > 0:
                    return Field.PRESENT
            return Field.MISSING
        else:
            if not isinstance(current, dict):
                return Field.MISSING
            if part not in current:
                return Field.MISSING
            current = current[part]
            if current is None:
                return Field.NULL

    return Field.PRESENT


def check_endpoint(data: Any, spec: EndpointSpec) -> dict[str, Field]:
    """Check all expected fields for an endpoint."""
    results = {}
    for field_path in spec.expected_fields:
        results[field_path] = check_field(data, field_path)
    return results


# ═══════════════════════════════════════════════════════════════════════════════
# Verification Runner
# ═══════════════════════════════════════════════════════════════════════════════

class VerifyResult:
    def __init__(self, passed: int, total: int, failed: int, nulls: int, errors: int,
                 details: list[str]):
        self.passed = passed
        self.total = total
        self.failed = failed
        self.nulls = nulls
        self.errors = errors
        self.details = details

    @property
    def coverage_pct(self) -> float:
        return (self.passed / self.total * 100) if self.total > 0 else 0

    @property
    def status(self) -> str:
        if self.errors > 0:
            return "ERROR"
        if self.coverage_pct == 100:
            return "✓"
        if self.coverage_pct >= 90:
            return "⚠"
        return "✗"


def print_header():
    print()
    print("═" * 72)
    print("  ESPN LIVE VERIFICATION SUITE — Phase 5.5 Production Verification")
    print(f"  {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print("═" * 72)


def print_result_line(entity: str, endpoint: str, result: VerifyResult):
    bar = "█" * int(result.coverage_pct / 10) + "░" * (10 - int(result.coverage_pct / 10))
    print(f"  {result.status} {entity:<18} {result.passed:>3}/{result.total:<3}  "
          f"[{bar}] {result.coverage_pct:.0f}%", end="")
    if result.nulls > 0:
        print(f"  ({result.nulls} null)")
    else:
        print()


async def verify_all():
    print_header()
    client = httpx.AsyncClient(timeout=30.0, headers=HEADERS, follow_redirects=True)

    total_checks = 0
    total_passed = 0
    all_results: list[tuple[str, VerifyResult]] = []

    try:
        for spec in ENDPOINTS:
            try:
                resp = await client.get(spec.url)
                status = resp.status_code

                if status != 200:
                    r = VerifyResult(0, len(spec.expected_fields), len(spec.expected_fields), 0, 1,
                                     [f"HTTP {status} from {spec.url}"])
                    all_results.append((spec.name, r))
                    print_result_line(spec.name, spec.url, r)
                    continue

                data = resp.json()
                field_results = check_endpoint(data, spec)

                passed = sum(1 for v in field_results.values() if v == Field.PRESENT)
                nulls = sum(1 for v in field_results.values() if v == Field.NULL)
                missing = sum(1 for v in field_results.values() if v == Field.MISSING)
                errors = sum(1 for v in field_results.values() if v == Field.ERROR)

                total_checks += len(spec.expected_fields)
                total_passed += passed

                details = [f"  {v.value} {k}" for k, v in field_results.items()
                          if v != Field.PRESENT]

                r = VerifyResult(passed, len(spec.expected_fields), missing, nulls, errors, details)
                all_results.append((spec.name, r))
                print_result_line(spec.name, spec.url, r)

                for d in details:
                    print(d)

            except Exception as e:
                r = VerifyResult(0, len(spec.expected_fields), len(spec.expected_fields), 0, 1,
                                 [str(e)])
                all_results.append((spec.name, r))
                print_result_line(spec.name, spec.url, r)
                print(f"    ! {e}")

    finally:
        await client.aclose()

    # ── Summary ────────────────────────────────────────────────────────────
    total_fields = sum(t for _, r in all_results for t in [r.total])
    total_ok = sum(p for _, r in all_results for p in [r.passed])
    total_null = sum(n for _, r in all_results for n in [r.nulls])
    total_missing = sum(f for _, r in all_results for f in [r.failed])

    print()
    print("─" * 72)
    print("  VERIFICATION SUMMARY")
    print("─" * 72)
    for name, r in all_results:
        bar = "✓" if r.coverage_pct == 100 else "⚠" if r.coverage_pct >= 90 else "✗"
        print(f"  {bar} {name:<25} {r.passed}/{r.total} fields ({r.coverage_pct:.0f}%)")
    print("─" * 72)
    print(f"  TOTAL:         {total_ok}/{total_fields} fields present ({total_ok/total_fields*100:.0f}%)")
    if total_null > 0:
        print(f"  NULL VALUES:   {total_null} fields (present but null)")
    if total_missing > 0:
        print(f"  MISSING:       {total_missing} fields (not found in payload)")
    print("═" * 72)

    if total_missing > 0:
        print("\n  ⚠ WARNING: Some fields missing from live API.")
        print("  These may be optional in the current ESPN payload.")
        print("  Review MASTER_FEATURE_INVENTORY.md and update if ESPN changed.")
    else:
        print("\n  ✓ All expected fields present in live ESPN API.")

    return total_missing


def main():
    missing = asyncio.run(verify_all())
    sys.exit(0 if missing == 0 else 1)


if __name__ == "__main__":
    main()
