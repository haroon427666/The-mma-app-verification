"""Unit tests — athlete discovery, client cache/dedup, rate envelope, parsers.

Covers the frozen-research-driven ESPN integration:
- Rate config sits inside the measured safe envelope (2–5 rps)
- ofc slug replaces one-championship
- Client response cache + in-flight dedup + canonicalization
- winningFight ref parsing (historical hook)
- eventlog parsing (probe-verified payload shape)
- Eventlog/winningFight jobs parse refs across league slugs
"""

import pytest

# ── Rate envelope + league slugs ──────────────────────────────────────────────


class TestRateEnvelope:
    def test_rate_within_research_envelope(self):
        from src.providers.espn.config import ESPNClientConfig

        cfg = ESPNClientConfig()
        # Research: 2–5 req/sec sustained; 4–8 workers
        assert 2.0 <= cfg.rate_limit_per_second <= 5.0
        assert 1 <= cfg.max_concurrency <= 8

    def test_burst_is_bounded(self):
        from src.providers.espn.config import ESPNClientConfig

        cfg = ESPNClientConfig()
        assert cfg.burst_size >= 1
        assert cfg.burst_size <= cfg.rate_limit_per_second * 4

    def test_ofc_slug_replaces_one_championship(self):
        from src.providers.espn.config import ESPN_LEAGUE_SLUGS

        assert "ofc" in ESPN_LEAGUE_SLUGS
        assert "one-championship" not in ESPN_LEAGUE_SLUGS

    def test_default_sync_leagues_are_active_majors(self):
        from src.providers.espn.config import DEFAULT_SYNC_LEAGUES

        assert "ufc" in DEFAULT_SYNC_LEAGUES
        assert "ofc" in DEFAULT_SYNC_LEAGUES

    def test_sync_league_slugs_env_override(self, monkeypatch):
        from src.providers.espn.config import sync_league_slugs

        monkeypatch.setenv("ESPN_SYNC_LEAGUES", "ufc,bellator")
        assert sync_league_slugs() == ("ufc", "bellator")

        monkeypatch.delenv("ESPN_SYNC_LEAGUES")
        assert "ufc" in sync_league_slugs()


# ── Client response cache + dedup ─────────────────────────────────────────────


class TestResponseCache:
    def test_canonicalize_sorts_params(self):
        from src.providers.espn.client import canonicalize

        assert canonicalize("/athletes", {"limit": 100, "page": 1}) == (
            canonicalize("/athletes", {"page": 1, "limit": 100})
        )
        assert canonicalize("/athletes") == "/athletes"

    @pytest.mark.asyncio
    async def test_cache_hit_and_miss_metrics(self):
        from src.providers.espn.client import ESPNClient
        from src.providers.espn.config import ESPNClientConfig

        calls: list[str] = []

        class FakeHTTP:
            is_success = True
            status_code = 200

            def json(self):
                return {"ok": True}

            async def request(self, method, path, **kwargs):
                calls.append(path)
                return self

            async def aclose(self):
                pass

        client = ESPNClient(ESPNClientConfig(cache_enabled=True))
        client._http = FakeHTTP()

        first = await client.get_json("/leagues/ufc", params={"limit": 25})
        second = await client.get_json("/leagues/ufc", params={"limit": 25})
        assert first == second
        assert len(calls) == 1  # second call served from cache
        assert client.metrics["cache_hits"] == 1
        assert client.metrics["cache_misses"] == 1

    @pytest.mark.asyncio
    async def test_in_flight_dedup(self):
        import asyncio

        from src.providers.espn.client import ESPNClient
        from src.providers.espn.config import ESPNClientConfig

        calls: list[str] = []

        class FakeHTTP:
            is_success = True
            status_code = 200

            def json(self):
                return {"ok": True}

            async def request(self, method, path, **kwargs):
                calls.append(path)
                await asyncio.sleep(0.01)
                return self

            async def aclose(self):
                pass

        client = ESPNClient(ESPNClientConfig(cache_enabled=True))
        client._http = FakeHTTP()

        results = await asyncio.gather(
            client.get_json("/athletes/123"),
            client.get_json("/athletes/123"),
            client.get_json("/athletes/123"),
        )
        assert len(results) == 3
        assert len(calls) == 1  # three concurrent identical → one HTTP call
        assert client.metrics["deduped"] == 2

    @pytest.mark.asyncio
    async def test_cache_disabled_no_caching(self):
        from src.providers.espn.client import ESPNClient
        from src.providers.espn.config import ESPNClientConfig

        calls: list[str] = []

        class FakeHTTP:
            is_success = True
            status_code = 200

            def json(self):
                return {"ok": True}

            async def request(self, method, path, **kwargs):
                calls.append(path)
                return self

            async def aclose(self):
                pass

        client = ESPNClient(ESPNClientConfig(cache_enabled=False))
        client._http = FakeHTTP()

        await client.get_json("/leagues/ufc")
        await client.get_json("/leagues/ufc")
        assert len(calls) == 2
        assert client.metrics["cache_hits"] == 0


# ── Athlete ID extraction ────────────────────────────────────────────────────


class TestAthleteIdExtraction:
    def test_item_id_from_ref(self):
        from src.providers.espn.provider import ESPNProvider

        item = {"$ref": "http://sports.core.api.espn.com/v2/sports/mma/athletes/2335697"}
        assert ESPNProvider._item_id(item) == "2335697"

    def test_item_id_from_inline(self):
        from src.providers.espn.provider import ESPNProvider

        assert ESPNProvider._item_id({"id": "3933168"}) == "3933168"
        assert ESPNProvider._item_id({"name": "no id"}) is None
        assert ESPNProvider._item_id("not-a-dict") is None


# ── winningFight ref parsing ─────────────────────────────────────────────────


class TestWinningFightRefs:
    def test_parse_competition_ref(self):
        from src.providers.espn.parsers.ranking import parse_winning_fight_ref

        ref = (
            "http://sports.core.api.espn.com/v2/sports/mma/leagues/ufc/"
            "events/600060621/competitions/401905693?lang=en&region=us"
        )
        parsed = parse_winning_fight_ref(ref)
        assert parsed == {
            "league": "ufc",
            "event_id": "600060621",
            "competition_id": "401905693",
        }

    def test_parse_non_competition_ref_returns_none(self):
        from src.providers.espn.parsers.ranking import parse_winning_fight_ref

        assert parse_winning_fight_ref("") is None
        assert (
            parse_winning_fight_ref("http://.../athletes/12345") is None
        )

    def test_extract_winning_fight_refs_deduplicates(self):
        from src.providers.espn.parsers.ranking import extract_winning_fight_refs

        payload = {
            "ranks": [
                {
                    "current": 1,
                    "athlete": {"$ref": ".../athletes/1"},
                    "winningFight": {
                        "$ref": (
                            "http://sports.core.api.espn.com/v2/sports/mma/leagues/"
                            "ufc/events/400901159/competitions/229783"
                        )
                    },
                },
                {
                    "current": 2,
                    "athlete": {"$ref": ".../athletes/2"},
                    "winningFight": {
                        "$ref": (
                            "http://sports.core.api.espn.com/v2/sports/mma/leagues/"
                            "ufc/events/400901159/competitions/229783"
                        )
                    },
                },
            ]
        }
        refs = extract_winning_fight_refs(payload)
        assert len(refs) == 1

    def test_parse_ranking_ignores_missing_winning_fight(self):
        from src.providers.espn.parsers.ranking import parse_ranking_category

        # Existing fixture-like payload WITHOUT winningFight must still parse
        payload = {
            "name": "Men's Pound for Pound Rankings",
            "type": "pound-for-pound",
            "ranks": [
                {
                    "current": 1,
                    "trend": "-",
                    "athlete": {"$ref": ".../athletes/3088812"},
                    "hasAccolade": True,
                }
            ],
        }
        dtos = parse_ranking_category(payload, "ufc")
        assert len(dtos) == 1
        assert dtos[0].rank == 1
        assert dtos[0].is_champion is True


# ── Eventlog parsing (probe-verified shape) ─────────────────────────────────


class TestEventlogParsing:
    def _payload(self) -> dict:
        return {
            "$ref": "http://.../athletes/2563796/eventlog",
            "events": {
                "count": 2,
                "pageIndex": 1,
                "pageSize": 25,
                "pageCount": 1,
                "items": [
                    {
                        "event": {
                            "$ref": (
                                "http://sports.core.api.espn.com/v2/sports/mma/"
                                "leagues/mvp/events/600059009"
                            )
                        },
                        "competition": {
                            "$ref": (
                                "http://sports.core.api.espn.com/v2/sports/mma/"
                                "leagues/mvp/events/600059009/competitions/401865245"
                            )
                        },
                        "competitor": {"$ref": ".../competitors/2563796"},
                        "played": True,
                    },
                    {
                        "event": {
                            "$ref": (
                                "http://sports.core.api.espn.com/v2/sports/mma/"
                                "leagues/ufc/events/400901159"
                            )
                        },
                        "competition": {
                            "$ref": (
                                "http://sports.core.api.espn.com/v2/sports/mma/"
                                "leagues/ufc/events/400901159/competitions/229783"
                            )
                        },
                        "played": True,
                    },
                ],
            },
        }

    def test_parse_eventlog_refs(self):
        from src.providers.espn.parsers.eventlog import parse_eventlog_refs

        refs = parse_eventlog_refs(self._payload())
        assert len(refs) == 2
        assert refs[0] == {"league": "mvp", "event_id": "600059009"}
        assert refs[1]["league"] == "ufc"
        assert refs[1]["event_id"] == "400901159"

    def test_parse_eventlog_empty(self):
        from src.providers.espn.parsers.eventlog import parse_eventlog_refs

        assert parse_eventlog_refs({}) == []
        assert parse_eventlog_refs({"events": {"items": []}}) == []

    def test_parse_eventlog_event_ids_dedup(self):
        from src.providers.espn.parsers.eventlog import parse_eventlog_event_ids

        ids = parse_eventlog_event_ids(self._payload())
        assert ids == ["600059009", "400901159"]
        # duplicate event ids collapse
        payload = self._payload()
        payload["events"]["items"].append(payload["events"]["items"][0])
        assert parse_eventlog_event_ids(payload) == ids


# ── Token-bucket pacing (live finding: 8 workers leaked to ~8.4 rps) ───────


class TestTokenBucketPacing:
    @pytest.mark.asyncio
    async def test_aggregate_rate_enforced_under_concurrency(self):
        import asyncio
        import time

        from src.providers.espn.client import TokenBucket

        # 30 acquires with burst 2 at 20 rps → 28 must be paced: ≥ 1.4s
        bucket = TokenBucket(rate=20.0, burst_size=2)
        start = time.monotonic()
        await asyncio.gather(*(bucket.acquire() for _ in range(30)))
        elapsed = time.monotonic() - start
        assert elapsed >= 1.1, (
            f"rate not enforced under concurrency: 30 acquires in {elapsed:.3f}s"
        )


# ── Eventlog pagination (live-verified: DJ 30 fights → 2 pages) ─────────────


class TestEventlogPagination:
    @pytest.mark.asyncio
    async def test_fetch_eventlog_hooks_paginates(self):
        from src.providers.espn.provider import ESPNProvider

        page1 = {"events": {"count": 30, "pageCount": 2, "items": [
            {"event": {"$ref": "http://x/leagues/ufc/events/1"}}
        ]}}
        page2 = {"events": {"count": 30, "pageCount": 2, "items": [
            {"event": {"$ref": "http://x/leagues/ufc/events/2"}}
        ]}}

        class FakeClient:
            _http = object()  # pretend started

            def __init__(self) -> None:
                self.pages: list[int] = []

            async def get_json(self, path, params=None):
                page = (params or {}).get("page", 1)
                self.pages.append(page)
                return page1 if page == 1 else page2

        provider = ESPNProvider()
        provider._client = FakeClient()  # type: ignore[assignment]

        payloads = await provider.fetch_eventlog_hooks(["2512089"])
        assert len(payloads) == 1
        items = payloads[0]["events"]["items"]
        assert len(items) == 2, "second page not merged"
        assert provider._client.pages == [1, 2]


# ── Circuit-breaker semantics (404 must NOT trip; 5xx must) ──────────────────


class TestCircuitBreakerSemantics:
    """Content-dependent 404s are normal ESPN responses — they must not open
    the circuit breaker (5 consecutive 404s used to poison entire sync runs).
    System-level 5xx failures must still trip it."""

    @pytest.mark.asyncio
    async def test_404s_do_not_trip_circuit_breaker(self):
        import httpx

        from src.providers.espn.client import CircuitState, ESPNClient
        from src.providers.espn.config import ESPNClientConfig

        req = httpx.Request("GET", "http://x/leagues/ufc/rankings")

        class FakeHTTP:
            is_success = False
            status_code = 404

            def json(self):
                return {}

            async def request(self, method, path, **kwargs):
                return self

            async def aclose(self):
                pass

            def raise_for_status(self):
                raise httpx.HTTPStatusError(
                    "404", request=req, response=httpx.Response(404, request=req)
                )

        client = ESPNClient(ESPNClientConfig(cache_enabled=False, max_retries=0))
        client._http = FakeHTTP()

        for _ in range(6):  # past the failure threshold (5)
            with pytest.raises(httpx.HTTPStatusError):
                await client.get("/leagues/ufc/rankings")

        assert client._circuit_breaker.state == CircuitState.CLOSED
        assert client.metrics["client_errors_4xx"] == 6

    @pytest.mark.asyncio
    async def test_5xx_still_trip_circuit_breaker(self):
        import httpx

        from src.providers.espn.client import CircuitState, ESPNClient
        from src.providers.espn.config import ESPNClientConfig

        req = httpx.Request("GET", "http://x/leagues/ufc/rankings")

        class FakeHTTP:
            is_success = False
            status_code = 500

            def json(self):
                return {}

            async def request(self, method, path, **kwargs):
                return self

            async def aclose(self):
                pass

            def raise_for_status(self):
                raise httpx.HTTPStatusError(
                    "500", request=req, response=httpx.Response(500, request=req)
                )

        client = ESPNClient(ESPNClientConfig(cache_enabled=False, max_retries=0))
        client._http = FakeHTTP()

        for _ in range(5):
            with pytest.raises(httpx.HTTPStatusError):
                await client.get("/leagues/ufc/rankings")

        assert client._circuit_breaker.state == CircuitState.OPEN


# ── Plan wiring (new entity in dependency graph) ─────────────────────────────


class TestPlanWiring:
    def test_full_sync_plan_includes_historical_events(self):
        from src.sync.plan import FullSyncPlan
        from src.sync.types import EntityType

        assert EntityType.HISTORICAL_EVENT in FullSyncPlan().order

    def test_plans_validate_against_dependency_graph(self):
        from src.sync.dependency import DEPENDENCY_MAP, DependencyGraph
        from src.sync.plan import FullSyncPlan, HistoricalEventsPlan

        graph = DependencyGraph.from_map(DEPENDENCY_MAP)
        for plan in (FullSyncPlan(), HistoricalEventsPlan()):
            valid, message = graph.validate_plan(plan)
            assert valid, message
        assert not graph.has_cycle()


# ── Fighter records (full breakdown parser) ─────────────────────────────────


class TestFighterRecordsParser:
    def test_full_record_parse(self):
        from src.providers.espn.parsers.records import parse_fighter_records

        payload = {
            "count": 1,
            "items": [
                {
                    "name": "overall",
                    "summary": "21-5-0",
                    "value": 0.8076923076923077,
                    "stats": [
                        {"name": "wins", "value": 21.0},
                        {"name": "losses", "value": 5.0},
                        {"name": "draws", "value": 0.0},
                        {"name": "noContests", "value": 0.0},
                        {"name": "submissions", "value": 1.0},
                        {"name": "submissionLosses", "value": 1.0},
                        {"name": "tkos", "value": 9.0},
                        {"name": "tkoLosses", "value": 1.0},
                        {"name": "titleWins", "value": 7.0},
                        {"name": "titleLosses", "value": 2.0},
                        {"name": "titleDraws", "value": 0.0},
                    ],
                }
            ],
        }
        rec = parse_fighter_records(payload)
        assert rec.wins == 21
        assert rec.losses == 5
        assert rec.ko_tko_wins == 9
        assert rec.submission_wins == 1
        assert rec.title_wins == 7
        assert rec.record_summary == "21-5-0"
        assert rec.finish_rate == round(10 / 21, 4)

    def test_empty_records(self):
        from src.providers.espn.parsers.records import parse_fighter_records

        rec = parse_fighter_records({"items": []})
        assert rec.wins == 0
        assert rec.total_fights == 0
        assert rec.record_summary == ""
