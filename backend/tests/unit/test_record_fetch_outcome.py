"""Unit tests — Phase D tri-state records fetch outcome (provider layer).

Classifies a single /athletes/{id}/records fetch as AVAILABLE / EMPTY /
FAILED so absence evidence is never confused with transient failure:
- empty 200 body            → EMPTY
- content-dependent 404     → EMPTY (NORMAL provider behavior)
- 429/5xx/network/breaker   → FAILED (retryable, NEVER absence evidence)
- real payload              → AVAILABLE
"""

import httpx
import pytest

from src.sync.types import RecordFetchOutcome

REAL_PAYLOAD = {
    "count": 1,
    "pageIndex": 1,
    "pageCount": 1,
    "items": [
        {
            "name": "overall",
            "summary": "21-5-0",
            "displayValue": "21-5-0",
            "stats": [
                {"name": "wins", "value": 21.0},
                {"name": "losses", "value": 5.0},
            ],
        }
    ],
}


class StubClient:
    """ESPNClient stand-in: _http non-None so _ensure_started skips start()."""

    _http = object()

    def __init__(self, behavior):
        self._behavior = behavior  # payload dict OR exception to raise

    async def get_json(self, path, params=None):
        if isinstance(self._behavior, Exception):
            raise self._behavior
        return self._behavior


def _make_provider(behavior) -> tuple:
    from src.providers.espn.provider import ESPNProvider

    provider = ESPNProvider()
    provider._client = StubClient(behavior)
    provider._resolver = object()  # not exercised by the records path
    return provider


def _http_error(status: int) -> httpx.HTTPStatusError:
    req = httpx.Request("GET", "https://sports.core.api.espn.com/records")
    resp = httpx.Response(status_code=status, request=req)
    return httpx.HTTPStatusError(f"http {status}", request=req, response=resp)


class TestRecordFetchOutcome:
    @pytest.mark.asyncio
    async def test_empty_200_body_is_empty_outcome(self):
        provider = _make_provider({"items": []})
        record, outcome, status = await provider.fetch_fighter_record_with_outcome("1")
        assert record is None
        assert outcome == RecordFetchOutcome.EMPTY
        assert status == 200

    @pytest.mark.asyncio
    async def test_real_payload_is_available(self):
        provider = _make_provider(REAL_PAYLOAD)
        record, outcome, status = await provider.fetch_fighter_record_with_outcome("1")
        assert outcome == RecordFetchOutcome.AVAILABLE
        assert status == 200
        assert record is not None
        assert record.record_summary == "21-5-0"
        assert record.wins == 21

    @pytest.mark.asyncio
    async def test_content_404_is_empty_not_failed(self):
        provider = _make_provider(_http_error(404))
        record, outcome, status = await provider.fetch_fighter_record_with_outcome("1")
        assert record is None
        assert outcome == RecordFetchOutcome.EMPTY
        assert status == 404

    @pytest.mark.asyncio
    async def test_503_is_failed_not_absence(self):
        provider = _make_provider(_http_error(503))
        record, outcome, status = await provider.fetch_fighter_record_with_outcome("1")
        assert record is None
        assert outcome == RecordFetchOutcome.FAILED
        assert status == 503

    @pytest.mark.asyncio
    async def test_network_error_is_failed(self):
        provider = _make_provider(httpx.ConnectError("connection refused"))
        record, outcome, status = await provider.fetch_fighter_record_with_outcome("1")
        assert record is None
        assert outcome == RecordFetchOutcome.FAILED
        assert status is None

    @pytest.mark.asyncio
    async def test_fetch_fighter_record_backward_compatible(self):
        """fetch_fighter_record keeps its FighterRecord | None contract."""
        provider = _make_provider({"items": []})
        assert await provider.fetch_fighter_record("1") is None

        provider = _make_provider(REAL_PAYLOAD)
        record = await provider.fetch_fighter_record("1")
        assert record is not None
        assert record.record_summary == "21-5-0"
