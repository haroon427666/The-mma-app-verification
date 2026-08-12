"""D5 API contract tests — optional `record_fetch` on FighterProfileResponse.

The field is strictly evidence-backed: it is present ONLY when a
fighter_provider_record_status row exists (CONFIRMED_ABSENT / FETCH_FAILED /
PERMANENT_FAILURE). It is `null` when the fighter has a real record
(HAS_RECORD — the `record` field is canonical) or has never been checked
(NOT_CHECKED). No synthetic AVAILABLE state is ever fabricated.
"""

from datetime import UTC, datetime
from types import SimpleNamespace

from src.schemas.fighter import FighterProfileResponse

# ── Helpers ──────────────────────────────────────────────────────────────────

def _fake_fighter(**overrides) -> SimpleNamespace:
    """Minimal Fighter-attribute surface required by `_fighter_to_profile`."""
    base = {
        "id": "f-1", "first_name": "Islam", "last_name": "Makhachev",
        "full_name": "Islam Makhachev", "short_name": None, "nickname": None,
        "slug": None, "weight_kg": None, "height_cm": None, "reach_cm": None,
        "leg_reach_cm": None, "stance": None, "weight_class_name": None,
        "nationality": None, "birth_date": None, "birth_location": None,
        "is_active": True, "debut_date": None, "headshot_url": None,
        "cutout_url": None, "render_url": None, "trains_at": None,
        "fighting_style": None, "biography": None, "instagram_url": None,
        "twitter_url": None, "source_provider": "espn", "synced_at": None,
    }
    base.update(overrides)
    return SimpleNamespace(**base)


def _fake_record_fetch(**overrides) -> SimpleNamespace:
    """Minimal FighterProviderRecordStatus-attribute surface."""
    base = {
        "status": "CONFIRMED_ABSENT", "provider": "espn",
        "last_checked_at": datetime(2026, 8, 12, 8, 47, 45, tzinfo=UTC),
        "last_http_status": 200, "result_detail": "http 200 — no usable record payload",
        "retry_count": 0, "provenance": "FINAL_SWEEP",
    }
    base.update(overrides)
    return SimpleNamespace(**base)


def _fake_record() -> SimpleNamespace:
    return SimpleNamespace(
        wins=28, losses=1, draws=0, no_contests=0, ko_tko_wins=12,
        ko_tko_losses=0, submission_wins=5, submission_losses=0,
        title_wins=4, title_losses=0, title_draws=0, total_fights=29,
        win_percentage=0.9655, finish_rate=0.5862, record_summary="28-1-0",
    )


def _profile(**kwargs) -> FighterProfileResponse:
    from src.api.v1.fighters import _fighter_to_profile

    return _fighter_to_profile(fighter=kwargs.pop("fighter", _fake_fighter()), **kwargs)


# ── Schema contract ──────────────────────────────────────────────────────────

class TestRecordFetchSchema:
    def test_field_is_optional_and_defaults_none(self):
        p = FighterProfileResponse(
            id="abc", first_name="Islam", last_name="Makhachev", is_active=True,
        )
        assert p.record_fetch is None
        assert "record_fetch" not in p.model_dump(exclude_none=True)

    def test_accepts_nested_status_and_roundtrips(self):
        from src.schemas.fighter import FighterRecordFetchStatus

        status = FighterRecordFetchStatus(
            status="CONFIRMED_ABSENT", provider="espn",
            last_checked_at=datetime(2026, 8, 12, 8, 47, 45, tzinfo=UTC),
            last_http_status=200, result_detail="http 200 — no usable record payload",
            retry_count=0, provenance="FINAL_SWEEP",
        )
        p = FighterProfileResponse(
            id="abc", first_name="Islam", last_name="Makhachev",
            is_active=True, record_fetch=status,
        )
        dumped = p.model_dump(mode="json")
        assert dumped["record_fetch"]["status"] == "CONFIRMED_ABSENT"
        assert dumped["record_fetch"]["provider"] == "espn"
        assert dumped["record_fetch"]["last_http_status"] == 200
        assert dumped["record_fetch"]["provenance"] == "FINAL_SWEEP"

    def test_accepts_fetch_failed_status(self):
        from src.schemas.fighter import FighterRecordFetchStatus

        p = FighterProfileResponse(
            id="abc", first_name="A", last_name="B", is_active=True,
            record_fetch=FighterRecordFetchStatus(
                status="FETCH_FAILED", provider="espn", retry_count=2,
                last_http_status=503,
            ),
        )
        assert p.record_fetch is not None
        assert p.record_fetch.status == "FETCH_FAILED"
        assert p.record_fetch.retry_count == 2

    def test_existing_contract_fields_untouched(self):
        """The additive field must not alter the pre-existing profile shape."""
        p = FighterProfileResponse(
            id="abc", first_name="Islam", last_name="Makhachev",
            is_active=True, weight_kg=70.3, height_cm=177.8,
        )
        assert p.weight_kg == 70.3
        assert p.record is None  # unchanged: no record → None
        assert p.record_fetch is None  # additive default


# ── Mapper contract ─────────────────────────────────────────────────────────

class TestProfileMapperRecordFetch:
    def test_no_status_row_omits_field(self):
        p = _profile(record=None, record_fetch=None)
        assert p.record_fetch is None
        assert p.record is None

    def test_status_row_included(self):
        p = _profile(record=None, record_fetch=_fake_record_fetch())
        assert p.record_fetch is not None
        assert p.record_fetch.status == "CONFIRMED_ABSENT"
        assert p.record_fetch.last_http_status == 200
        assert p.record_fetch.provenance == "FINAL_SWEEP"
        assert p.record is None  # absence evidence never fabricates a record

    def test_real_record_means_record_fetch_none(self):
        """HAS_RECORD is canonical — no status row can coexist (deleted on
        record persist), so the profile must show record and no record_fetch."""
        p = _profile(record=_fake_record(), record_fetch=None)
        assert p.record is not None
        assert p.record.record_summary == "28-1-0"
        assert p.record_fetch is None

    def test_source_provider_does_not_leak_into_record_fetch(self):
        """record_fetch only mirrors persisted status rows, never the fighter's
        source_provider."""
        p = _profile(fighter=_fake_fighter(source_provider="octagon"), record_fetch=None)
        assert p.source_provider == "octagon"
        assert p.record_fetch is None
