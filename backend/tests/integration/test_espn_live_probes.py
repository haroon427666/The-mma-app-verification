"""Live ESPN surface probes — env-gated (MMA_LIVE_SYNC=1).

Bounded representative probes against the real ESPN API. Each probe is
classified:
  OK      — endpoint responded and returned content
  EMPTY   — endpoint responded but returned no content (content-dependent:
            a legitimate result, NOT a failure)
  FAILED  — endpoint/transport failure (5xx, network, or a 4xx on a surface
            that is NOT content-dependent)

Provider methods (fetch_fighter / fetch_fighter_record /
fetch_fighter_statistics) SWALLOW exceptions and return None/empty, so
classification uses the client's request-metrics deltas around each call:
a 4xx delta on a content-dependent surface (records/statistics) = legitimate
"no content"; a 4xx on a profile probe = a real failure (the research
claims these hidden profiles resolve); 5xx/network/429 deltas = FAILED.

Research-verified athlete IDs (frozen research, espn_hidden_profiles/
final_report.md): hidden-profile fighters absent from the original listing
but reachable via ranking/event refs — exactly the discovery the production
integration must handle.

Run: MMA_LIVE_SYNC=1 python -m pytest tests/integration/test_espn_live_probes.py -v -s
"""

import os

import pytest

RUN_LIVE = os.environ.get("MMA_LIVE_SYNC") == "1"

pytestmark = pytest.mark.skipif(
    not RUN_LIVE,
    reason="set MMA_LIVE_SYNC=1 to run the live ESPN surface probes",
)

HIDDEN_IDS: dict[str, str] = {
    "demetrious_johnson": "2512089",  # reachable via rankings:ufc ref
    "ronda_rousey": "2563797",        # reachable via league:ufc ref (research: cross-ID collision risk)
    "royce_gracie": "2335697",        # reachable via league:bellator ref
    "ken_shamrock": "2335653",        # reachable via league:bellator ref
}


def _metrics_snapshot(client) -> tuple:
    m = client.metrics
    return (m["client_errors_4xx"], m["server_errors_5xx"],
            m["network_errors"], m["rate_limited_429"])


async def _classify_provider(coro, client, content_dependent: bool) -> tuple[str, object]:
    """Classify a provider-method probe using client metrics deltas.

    Provider methods swallow exceptions, so transport failures only show up
    in the client metrics. content_dependent=True means a 4xx is a legitimate
    empty result (records/statistics); content_dependent=False means any 4xx
    is a real failure (profiles must resolve).
    """
    before = _metrics_snapshot(client)
    try:
        value = await coro
    except Exception as e:
        return "FAILED", f"{type(e).__name__}: {e}"
    m = client.metrics
    d4xx = m["client_errors_4xx"] - before[0]
    d5xx = m["server_errors_5xx"] - before[1]
    dnet = m["network_errors"] - before[2]
    d429 = m["rate_limited_429"] - before[3]
    if d5xx or dnet or d429:
        return "FAILED", f"http_error (5xx={d5xx}, net={dnet}, 429={d429})"
    if d4xx and not content_dependent:
        return "FAILED", f"http_error (4xx={d4xx})"
    if value is None or value == [] or value == {} or value == "":
        suffix = " (content-dependent 404)" if d4xx else ""
        return "EMPTY", f"no_content{suffix}"
    return "OK", value


async def _classify_get(client, path: str) -> tuple[str, object]:
    """Client-level probe — HTTP status is the classification signal."""
    try:
        response = await client.get(path)
    except Exception as e:
        status = getattr(e, "response", None)
        code = getattr(status, "status_code", None)
        return "FAILED", f"{type(e).__name__} (http {code})"
    if response.status_code == 200:
        return "OK", response.json()
    if response.status_code == 404:
        return "EMPTY", "http 404 (content-dependent)"
    return "FAILED", f"http {response.status_code}"


@pytest.mark.asyncio
async def test_representative_surface_probes():
    from src.providers.espn.config import ENDPOINTS
    from src.providers.espn.parsers.ranking import parse_winning_fight_ref
    from src.providers.espn.provider import ESPNProvider

    provider = ESPNProvider()
    await provider._ensure_started()
    client = provider._client
    results: dict[str, str] = {}
    try:
        # ── 1. Hidden historical fighter profiles resolve (NOT content-dependent) ─
        for name, aid in HIDDEN_IDS.items():
            status, fighter = await _classify_provider(
                provider.fetch_fighter(aid), client, content_dependent=False
            )
            detail = getattr(fighter, "first_name", None)
            results[f"profile:{name}"] = f"{status} ({detail})"
            assert status != "FAILED", f"profile probe failed for {name}"

        # ── 2. Records (content-dependent) ────────────────────────────────
        for name in ("ken_shamrock", "royce_gracie"):
            status, rec = await _classify_provider(
                provider.fetch_fighter_record(HIDDEN_IDS[name]), client,
                content_dependent=True,
            )
            summary = getattr(rec, "record_summary", None)
            results[f"records:{name}"] = f"{status} (summary={summary})"

        # ── 3. Career statistics (content-dependent) ──────────────────────
        for name in ("demetrious_johnson", "ken_shamrock"):
            status, stats = await _classify_provider(
                provider.fetch_fighter_statistics(HIDDEN_IDS[name]), client,
                content_dependent=True,
            )
            n_dtos = len(getattr(stats, "raw_dtos", []) or [])
            if n_dtos == 0 and status == "OK":
                status = "EMPTY"
            results[f"stats:{name}"] = f"{status} ({n_dtos} stats)"

        # ── 4. Eventlog (client-level; pagination metadata) ───────────────
        for name in ("royce_gracie", "demetrious_johnson"):
            aid = HIDDEN_IDS[name]
            status, data = await _classify_get(
                client, ENDPOINTS["athlete_eventlog"].format(athlete_id=aid)
            )
            if status == "OK":
                events = data.get("events", {}) or {}
                results[f"eventlog:{name}"] = (
                    f"OK (count={events.get('count', 0)}, pages={events.get('pageCount', 1)})"
                )
            else:
                results[f"eventlog:{name}"] = status

        # ── 5. Active UFC fighter (from rankings, never guessed) ──────────
        status, rankings = await _classify_provider(
            provider.fetch_rankings("ufc"), client, content_dependent=False
        )
        if status == "OK" and rankings:
            active_id = rankings[0].fighter_external_id
            results["rankings:ufc"] = f"OK ({len(rankings)} ranks)"
            fstatus, fighter = await _classify_provider(
                provider.fetch_fighter(active_id), client, content_dependent=False
            )
            results[f"profile:ufc_ranked#{rankings[0].rank}"] = (
                f"{fstatus} (active={getattr(fighter, 'is_active', None)})"
            )
        else:
            results["rankings:ufc"] = status

        # ── 6. Historical event chain: winningFight refs → event → comps ──
        status, refs = await _classify_provider(
            provider.fetch_winning_fight_refs("ufc"), client, content_dependent=False
        )
        n_refs = len(refs) if isinstance(refs, list) else 0
        results["winningfight_refs:ufc"] = f"{status} ({n_refs} refs)"
        if status == "OK" and refs:
            for ref in list(refs)[:2]:
                parsed = parse_winning_fight_ref(ref)
                if parsed is None:
                    continue
                estatus, _ = await _classify_provider(
                    provider.fetch_event(parsed["event_id"], league_slug=parsed["league"]),
                    client, content_dependent=False,
                )
                cstatus, comps = await _classify_provider(
                    provider.fetch_competitions(parsed["event_id"], league_slug=parsed["league"]),
                    client, content_dependent=False,
                )
                n_comp = len(comps) if isinstance(comps, list) else 0
                n_compets = (
                    sum(len(getattr(c, "competitors", [])) for c in comps)
                    if isinstance(comps, list) else 0
                )
                results[f"historical:{parsed['league']}/{parsed['event_id']}"] = (
                    f"event={estatus} comps={cstatus} ({n_comp} comps, {n_compets} competitors)"
                )

        # ── 7. Non-UFC promotion (ofc — ONE Championship) ──────────────────
        status, roster = await _classify_provider(
            provider.fetch_fighters("ofc", limit=3), client, content_dependent=False
        )
        results["roster:ofc"] = f"{status} ({len(roster)} fighters)" if status == "OK" else status

        # ── 8. Retired-vs-active status field presence ────────────────────
        for name, aid in (("rousey", HIDDEN_IDS["ronda_rousey"]),
                          ("gracie", HIDDEN_IDS["royce_gracie"])):
            status, fighter = await _classify_provider(
                provider.fetch_fighter(aid), client, content_dependent=False
            )
            results[f"status:{name}"] = f"{status} (is_active={getattr(fighter, 'is_active', None)})"
    finally:
        await provider.close()

    for key in sorted(results):
        print(f"  {key:<28} {results[key]}")

    # Hard gates: hidden profiles must resolve (P0) and the historical chain
    # must be reachable; everything else is recorded as evidence, not asserted.
    assert all(v.split(" ")[0] != "FAILED" for k, v in results.items() if k.startswith("profile:")), (
        "a hidden-profile probe failed"
    )
    assert any(k.startswith("historical:") for k in results), "no historical event probed"
