"""Bounded live ESPN throughput benchmark (acceptance validation).

Respects the frozen-research envelope (2-5 req/s sustained, 4-8 workers).
Total request budget: ~160 requests max — a smoke benchmark, NOT a census.

Measures, per worker count (1/2/4/8) on a FRESH slice of athlete IDs:
- effective requests/sec (rate-limiter enforcement)
- failures (unresolved profiles)

Plus dedicated checks:
- in-flight dedup: two concurrent identical fetches share one HTTP call
- cache reuse: a repeat fetch of cached IDs adds zero new HTTP calls

Usage:
    python scripts/espn_live_benchmark.py
"""

import asyncio
import os
import time

# Research-verified hidden-profile IDs (frozen research) — never guessed
SAMPLE_IDS = ["2512089", "2563797", "2335697", "2335653"]  # DJ, Rousey, Gracie, Shamrock


async def _discover_ids(provider, n: int) -> list[str]:
    """Build a pool from the live listing + research-verified sample IDs."""
    ids = await provider.fetch_athlete_ids(
        league_slugs=["ufc"], include_global=True, limit=1000
    )
    pool = list(ids)[: max(0, n - len(SAMPLE_IDS))] + SAMPLE_IDS
    return pool[:n]


def _delta(metrics_before: dict[str, int], metrics_after: dict[str, int]) -> dict[str, int]:
    return {k: metrics_after.get(k, 0) - metrics_before.get(k, 0) for k in metrics_after}


async def _bench_worker_count(provider, ids: list[str], workers: int) -> dict:
    client = provider._client
    before = dict(client.metrics)
    start = time.monotonic()
    fighters = await provider.fetch_fighters_by_ids(ids, max_concurrency=workers)
    elapsed = time.monotonic() - start
    delta = _delta(before, dict(client.metrics))
    return {
        "workers": workers,
        "resolved": len(fighters),
        "elapsed_s": round(elapsed, 2),
        "http_calls": delta["cache_misses"],  # first fetch of fresh IDs = all misses
        "retries": delta["retries"],
        "failures": len(ids) - len(fighters),
        "effective_rps": round(delta["cache_misses"] / elapsed, 2) if elapsed else 0.0,
    }


async def _bench_dedup(provider, ids: list[str]) -> int:
    """Two concurrent identical fetches of FRESH ids must share HTTP calls."""
    before = dict(provider._client.metrics)
    await asyncio.gather(
        provider.fetch_fighters_by_ids(ids, max_concurrency=8),
        provider.fetch_fighters_by_ids(ids, max_concurrency=8),
    )
    delta = _delta(before, dict(provider._client.metrics))
    return delta["deduped"], delta["cache_misses"]


async def main() -> None:
    from src.providers.espn.config import ESPNClientConfig
    from src.providers.espn.provider import ESPNProvider

    n = int(os.environ.get("ESPN_BENCH_LIMIT", "100"))
    config = ESPNClientConfig()  # production defaults: 3.0 rps, burst 6, cache on

    print(f"config: rate={config.rate_limit_per_second} rps burst={config.burst_size} "
          f"concurrency_cap={config.max_concurrency} cache_ttl={config.cache_ttl_seconds}s")
    print(f"pool size: {n} athlete IDs (bounded benchmark, not a census)\n")

    provider = ESPNProvider(config)
    await provider._ensure_started()
    try:
        ids = await _discover_ids(provider, n)
        print(f"pool: {len(ids)} IDs (4 research-verified + {len(ids) - 4} from live listing)")

        SLICE = 20
        results = []
        for idx, workers in enumerate((1, 2, 4, 8)):
            slice_ids = ids[idx * SLICE : (idx + 1) * SLICE]
            row = await _bench_worker_count(provider, slice_ids, workers)
            results.append(row)
            print(
                f"workers={row['workers']:>2}  resolved={row['resolved']:>2}/{len(slice_ids)}  "
                f"http_calls={row['http_calls']:>3}  retries={row['retries']}  "
                f"failures={row['failures']:>2}  elapsed={row['elapsed_s']:>6.2f}s  "
                f"rps={row['effective_rps']:>5.2f}"
            )

        # In-flight dedup on a fresh slice
        fresh = ids[4 * SLICE : 4 * SLICE + SLICE]
        deduped, misses = await _bench_dedup(provider, fresh)
        # Deduped requests are ALSO counted as cache misses (they weren't in
        # the cache yet) — real HTTP calls = misses - deduped.
        actual_http = misses - deduped
        print(f"\ndedup test ({len(fresh)} fresh ids, 2 concurrent fetches): "
              f"deduped={deduped} actual_http_calls={actual_http} (misses incl. deduped={misses})")

        # Cache reuse: re-fetch an already-cached slice → zero new HTTP calls
        before = dict(provider._client.metrics)
        await provider.fetch_fighters_by_ids(ids[:SLICE], max_concurrency=4)
        delta = _delta(before, dict(provider._client.metrics))
        print(f"cache reuse (re-fetch {SLICE} cached ids): new_http_calls={delta['cache_misses']}")

        print("\nNOTE: aggregate throughput is rate-limited by design (3.0 rps token bucket)."
              " The benchmark verifies the envelope is enforced and cache/dedup eliminate"
              " redundant HTTP calls — it does NOT measure raw ESPN throughput.")

        # ── Gates ─────────────────────────────────────────────────────────
        peak = max(r["effective_rps"] for r in results)
        assert peak <= 6.0, f"effective rps {peak} exceeds the researched envelope"
        for r in results:
            assert r["resolved"] > 0, f"{r['workers']} workers resolved 0 profiles"
        assert deduped == len(fresh), f"dedup expected {len(fresh)}, got {deduped}"
        assert actual_http == len(fresh), f"each id should be fetched once, got {actual_http} calls"
        assert delta["cache_misses"] == 0, "cache reuse produced new HTTP calls"
        print("benchmark gates PASSED")
    finally:
        await provider.close()


if __name__ == "__main__":
    asyncio.run(main())
