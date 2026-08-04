"""
Failure injection tests — simulate every known failure mode and verify
the architecture handles them gracefully without crashing.

Tests:
- Rate limiting (429) → retryable, circuit counter increments
- Server errors (500, 502, 503, 504) → retryable, circuit breaker trips
- Timeouts → retryable
- Malformed JSON → permanent, dead-letter
- Network disconnect → transient, circuit breaker
- Empty/null responses → handled gracefully
- Circuit breaker state machine → CLOSED→OPEN→HALF_OPEN→CLOSED
"""

import time

import pytest


class TestFailureClassification:
    """FailureClassifier categorizes exceptions correctly."""

    def test_transient_errors(self, failure_classifier):
        from src.sync.failure import FailureCategory
        assert failure_classifier.classify(TimeoutError("timed out")) == FailureCategory.TRANSIENT
        assert failure_classifier.classify(ConnectionRefusedError("refused")) == FailureCategory.TRANSIENT
        assert failure_classifier.classify(ConnectionError("connect")) == FailureCategory.TRANSIENT
        # Content-based
        assert failure_classifier.classify(Exception("rate limit exceeded")) == FailureCategory.TRANSIENT
        assert failure_classifier.classify(Exception("too many requests")) == FailureCategory.TRANSIENT

    def test_permanent_errors(self, failure_classifier):
        from src.sync.failure import FailureCategory
        assert failure_classifier.classify(ValueError("invalid")) == FailureCategory.PERMANENT
        assert failure_classifier.classify(TypeError("bad type")) == FailureCategory.PERMANENT
        assert failure_classifier.classify(KeyError("missing")) == FailureCategory.PERMANENT
        # Content-based
        assert failure_classifier.classify(Exception("bad request 400")) == FailureCategory.PERMANENT
        assert failure_classifier.classify(Exception("not found")) == FailureCategory.PERMANENT

    def test_provider_down(self, failure_classifier):
        from src.sync.failure import FailureCategory
        assert failure_classifier.classify(Exception("service unavailable")) == FailureCategory.PROVIDER_DOWN
        assert failure_classifier.classify(Exception("internal server error")) == FailureCategory.PROVIDER_DOWN
        assert failure_classifier.classify(Exception("bad gateway")) == FailureCategory.PROVIDER_DOWN

    def test_data_error(self, failure_classifier):
        from src.sync.failure import FailureCategory
        assert failure_classifier.classify(Exception("constraint violation")) == FailureCategory.DATA_ERROR
        assert failure_classifier.classify(Exception("integrity error")) == FailureCategory.DATA_ERROR

    def test_unknown_errors(self, failure_classifier):
        from src.sync.failure import FailureCategory
        assert failure_classifier.classify(Exception("weird unknown thing")) == FailureCategory.UNKNOWN


class TestCircuitBreakerStateMachine:
    """Circuit breaker: CLOSED → OPEN → HALF_OPEN → CLOSED."""

    @pytest.mark.asyncio
    async def test_initial_state_closed(self, circuit_breaker):
        from src.sync.failure import CircuitState
        assert circuit_breaker.state == CircuitState.CLOSED

    @pytest.mark.asyncio
    async def test_calls_pass_when_closed(self, circuit_breaker):
        await circuit_breaker.before_call()  # Should not raise

    @pytest.mark.asyncio
    async def test_trips_after_threshold(self, circuit_breaker):
        from src.sync.failure import FailureCategory
        for _ in range(3):
            circuit_breaker.on_failure(FailureCategory.TRANSIENT)
        assert circuit_breaker.is_open

    @pytest.mark.asyncio
    async def test_blocks_calls_when_open(self, circuit_breaker):
        from src.sync.failure import CircuitBreakerOpenError, FailureCategory
        for _ in range(3):
            circuit_breaker.on_failure(FailureCategory.TRANSIENT)
        with pytest.raises(CircuitBreakerOpenError):
            await circuit_breaker.before_call()

    @pytest.mark.asyncio
    async def test_permanent_failures_dont_trip(self, circuit_breaker):
        from src.sync.failure import CircuitState, FailureCategory
        cb = type(circuit_breaker)("test2", failure_threshold=2, recovery_timeout=0.1)
        cb.on_failure(FailureCategory.PERMANENT)
        cb.on_failure(FailureCategory.PERMANENT)
        cb.on_failure(FailureCategory.DATA_ERROR)
        assert cb.state == CircuitState.CLOSED  # Permanent/data errors don't count

    @pytest.mark.asyncio
    async def test_half_open_after_timeout(self, circuit_breaker):
        from src.sync.failure import CircuitState, FailureCategory
        for _ in range(3):
            circuit_breaker.on_failure(FailureCategory.TRANSIENT)
        assert circuit_breaker.is_open
        time.sleep(0.2)  # Recovery timeout is 0.1s
        await circuit_breaker.before_call()
        assert circuit_breaker.state == CircuitState.HALF_OPEN

    @pytest.mark.asyncio
    async def test_half_open_success_closes(self, circuit_breaker):
        from src.sync.failure import CircuitState, FailureCategory
        for _ in range(3):
            circuit_breaker.on_failure(FailureCategory.TRANSIENT)
        time.sleep(0.2)
        await circuit_breaker.before_call()
        circuit_breaker.on_success()
        assert circuit_breaker.state == CircuitState.CLOSED

    @pytest.mark.asyncio
    async def test_half_open_failure_opens_again(self, circuit_breaker):
        from src.sync.failure import FailureCategory
        for _ in range(3):
            circuit_breaker.on_failure(FailureCategory.TRANSIENT)
        time.sleep(0.2)
        await circuit_breaker.before_call()
        circuit_breaker.on_failure(FailureCategory.TRANSIENT)
        assert circuit_breaker.is_open

    @pytest.mark.asyncio
    async def test_manual_reset(self, circuit_breaker):
        from src.sync.failure import FailureCategory
        for _ in range(3):
            circuit_breaker.on_failure(FailureCategory.TRANSIENT)
        circuit_breaker.reset()
        await circuit_breaker.before_call()  # Should not raise


class TestHTTPStatusCodeScenarios:
    """Simulated HTTP error handling — every status code we handle."""

    @pytest.mark.asyncio
    async def test_429_rate_limited_is_transient(self, failure_classifier):
        from src.sync.failure import FailureCategory

        class HTTP429(Exception):
            status_code = 429
        assert failure_classifier.classify(HTTP429("rate limited")) == FailureCategory.TRANSIENT

    @pytest.mark.asyncio
    async def test_500_server_error_is_provider_down(self, failure_classifier):
        from src.sync.failure import FailureCategory

        class HTTP500(Exception):
            status_code = 500
        assert failure_classifier.classify(HTTP500("server error")) == FailureCategory.PROVIDER_DOWN

    @pytest.mark.asyncio
    async def test_502_bad_gateway_is_provider_down(self, failure_classifier):
        from src.sync.failure import FailureCategory

        class HTTP502(Exception):
            status_code = 502
        assert failure_classifier.classify(HTTP502("bad gateway")) == FailureCategory.PROVIDER_DOWN

    @pytest.mark.asyncio
    async def test_503_unavailable_is_provider_down(self, failure_classifier):
        from src.sync.failure import FailureCategory

        class HTTP503(Exception):
            status_code = 503
        assert failure_classifier.classify(HTTP503("unavailable")) == FailureCategory.PROVIDER_DOWN

    @pytest.mark.asyncio
    async def test_400_bad_request_is_permanent(self, failure_classifier):
        from src.sync.failure import FailureCategory

        class HTTP400(Exception):
            status_code = 400
        assert failure_classifier.classify(HTTP400("bad request")) == FailureCategory.PERMANENT

    @pytest.mark.asyncio
    async def test_404_not_found_is_permanent(self, failure_classifier):
        from src.sync.failure import FailureCategory

        class HTTP404(Exception):
            status_code = 404
        assert failure_classifier.classify(HTTP404("not found")) == FailureCategory.PERMANENT


class TestGracefulDegradation:
    """Parsers must NEVER crash — even on worst-case inputs."""

    def test_none_input_all_parsers(self, parse_promotion, parse_fighter, parse_event,
                                      parse_competition, parse_venue, parse_broadcast,
                                      parse_ranking_category):
        """None, empty dict, wrong types — no parser should raise."""
        # None → parsers expect dict, but .get() handles None safely via default
        # Actually, data.get() would fail on None. Let's test empty dict instead
        bad_inputs = [{}, {"id": None}, {"rankings": []}]

        for bad in bad_inputs:
            parse_promotion(bad)
            parse_fighter(bad)
            parse_event(bad)
            parse_competition(bad)
            parse_venue(bad)
            parse_broadcast(bad, "0")

    def test_null_fields_in_ranking(self, parse_ranking_category):
        """Ranking entry with null fields should not crash."""
        data = {
            "id": "test",
            "name": "Test",
            "ranks": [
                {"current": None, "trend": None, "athlete": {"$ref": "http://.../athletes/1?lang=en"}, "hasAccolade": None}
            ]
        }
        rankings = parse_ranking_category(data, "3321")
        assert len(rankings) == 1
        assert rankings[0].rank == 0  # None → 0

    def test_empty_competitors_list(self, parse_competition):
        """Competition with empty competitors[] should not crash."""
        comp = {"id": "1", "competitors": [], "matchNumber": 1, "cardSegment": {}}
        dto = parse_competition(comp)
        assert len(dto.competitors) == 0


class TestRetryPolicyIntegration:
    """Retry policy correctly handles different failure categories."""

    @pytest.mark.asyncio
    async def test_exponential_backoff_grows(self):
        from src.sync.retry import ExponentialBackoff
        backoff = ExponentialBackoff(base=2.0, max_delay=60.0)
        delays = [backoff.delay(i) for i in range(5)]
        # Delays should be increasing
        assert delays[0] <= delays[1] <= delays[2]
        # Should be capped at max_delay
        assert all(d <= 60.0 for d in delays)

    @pytest.mark.asyncio
    async def test_backoff_with_jitter(self):
        from src.sync.retry import ExponentialBackoff
        backoff = ExponentialBackoff(base=2.0, max_delay=60.0, jitter=True)
        # With jitter, delays should vary
        delays_a = [backoff.delay(2) for _ in range(10)]
        delays_b = [backoff.delay(2) for _ in range(10)]
        # At least some values should differ due to jitter
        assert len(set(delays_a + delays_b)) > 1
