"""
Integration test fixtures.

Loads all real ESPN payload fixtures and provides mock infrastructure
for testing parsers, pipeline, and failure scenarios without a database.
"""

import json
from pathlib import Path

import pytest

FIXTURES_DIR = Path(__file__).parent / "fixtures" / "espn"


# ═══════════════════════════════════════════════════════════════════════════════
# Fixture Loaders — every real ESPN payload
# ═══════════════════════════════════════════════════════════════════════════════

def _load(name: str) -> dict:
    path = FIXTURES_DIR / name
    if not path.exists():
        raise FileNotFoundError(f"Fixture not found: {path}")
    return json.loads(path.read_text())


@pytest.fixture(scope="session")
def ufc_promotion():
    return _load("ufc_promotion.json")


@pytest.fixture(scope="session")
def jason_reinhardt():
    """Inactive fighter, reach=0.0, empty images[] — edge case."""
    return _load("fighter_jason_reinhardt.json")


@pytest.fixture(scope="session")
def islam_makhachev():
    """Active champion, all fields populated."""
    return _load("fighter_active.json")


@pytest.fixture(scope="session")
def malformed_fighter():
    """Missing fields, null weightClass, 0.0 measurements."""
    return _load("fighter_malformed.json")


@pytest.fixture(scope="session")
def fighter_records():
    return _load("fighter_records.json")


@pytest.fixture(scope="session")
def event_scheduled():
    return _load("event_scheduled.json")


@pytest.fixture(scope="session")
def competition_main_event():
    return _load("competition_main_event.json")


@pytest.fixture(scope="session")
def competition_final():
    return _load("competition_final.json")


@pytest.fixture(scope="session")
def competition_status():
    return _load("competition_status.json")


@pytest.fixture(scope="session")
def rankings_p4p():
    return _load("rankings_p4p.json")


@pytest.fixture(scope="session")
def rankings_heavyweight():
    return _load("rankings_heavyweight.json")


@pytest.fixture(scope="session")
def broadcast_ppv():
    return _load("broadcast_ppv.json")


@pytest.fixture(scope="session")
def venue_belgrade():
    return _load("venue_belgrade.json")


@pytest.fixture(scope="session")
def athlete_list_empty():
    return _load("athlete_list_empty.json")


# ═══════════════════════════════════════════════════════════════════════════════
# Parser Fixtures — import parsers once
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.fixture(scope="session")
def parse_promotion():
    from src.providers.espn.parsers.promotion import parse_promotion
    return parse_promotion


@pytest.fixture(scope="session")
def parse_fighter():
    from src.providers.espn.parsers.fighter import parse_fighter
    return parse_fighter


@pytest.fixture(scope="session")
def parse_fighter_records():
    from src.providers.espn.parsers.fighter import parse_fighter_records
    return parse_fighter_records


@pytest.fixture(scope="session")
def parse_event():
    from src.providers.espn.parsers.event import parse_event
    return parse_event


@pytest.fixture(scope="session")
def parse_competition():
    from src.providers.espn.parsers.competition import parse_competition
    return parse_competition


@pytest.fixture(scope="session")
def parse_competition_status():
    from src.providers.espn.parsers.competition import parse_competition_status
    return parse_competition_status


@pytest.fixture(scope="session")
def parse_ranking_category():
    from src.providers.espn.parsers.ranking import parse_ranking_category
    return parse_ranking_category


@pytest.fixture(scope="session")
def parse_broadcast():
    from src.providers.espn.parsers.broadcast import parse_broadcast
    return parse_broadcast


@pytest.fixture(scope="session")
def parse_venue():
    from src.providers.espn.parsers.venue import parse_venue
    return parse_venue


# ═══════════════════════════════════════════════════════════════════════════════
# ESPNDTO imports
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.fixture(scope="session")
def dto_classes():
    from src.providers.dto import (
        BroadcastDTO,
        CompetitionDTO,
        CompetitorDTO,
        EventDTO,
        FighterDTO,
        PromotionDTO,
        RankingDTO,
        VenueDTO,
    )
    return {
        "PromotionDTO": PromotionDTO,
        "FighterDTO": FighterDTO,
        "EventDTO": EventDTO,
        "CompetitionDTO": CompetitionDTO,
        "CompetitorDTO": CompetitorDTO,
        "RankingDTO": RankingDTO,
        "BroadcastDTO": BroadcastDTO,
        "VenueDTO": VenueDTO,
    }


# ═══════════════════════════════════════════════════════════════════════════════
# Failure Injection Helpers
# ═══════════════════════════════════════════════════════════════════════════════

class FakeHTTPError(Exception):
    """Simulates an HTTP error with status code."""
    def __init__(self, status_code: int, message: str = ""):
        self.status_code = status_code
        super().__init__(message)


class FakeTimeoutError(Exception):
    """Simulates a network timeout."""


@pytest.fixture
def failure_scenarios():
    """Factory for creating simulated provider failures."""
    return {
        "rate_limited": FakeHTTPError(429, "Too Many Requests"),
        "server_error": FakeHTTPError(500, "Internal Server Error"),
        "bad_gateway": FakeHTTPError(502, "Bad Gateway"),
        "service_unavailable": FakeHTTPError(503, "Service Unavailable"),
        "gateway_timeout": FakeHTTPError(504, "Gateway Timeout"),
        "timeout": FakeTimeoutError("Connection timed out"),
        "malformed_json": ValueError("Expecting value: line 1 column 1"),
        "network_error": ConnectionError("Connection refused"),
    }


# ═══════════════════════════════════════════════════════════════════════════════
# Reference Resolver Helpers
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.fixture
def extract_id_from_ref():
    from src.providers.espn.reference import extract_id_from_ref
    return extract_id_from_ref


# ═══════════════════════════════════════════════════════════════════════════════
# Sync Engine Helpers
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.fixture
def failure_classifier():
    from src.sync.failure import FailureClassifier
    return FailureClassifier()


@pytest.fixture
def circuit_breaker():
    from src.sync.failure import CircuitBreaker
    return CircuitBreaker(provider_slug="test", failure_threshold=3, recovery_timeout=0.1)
