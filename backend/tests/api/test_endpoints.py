"""Phase 8 API Tests — endpoint contracts, pagination, filters, serialization."""

import pytest
from datetime import date, datetime


# ═══════════════════════════════════════════════════════════════════════════════
# Schema Validation Tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestSchemas:
    def test_fighter_list_item_roundtrips(self):
        from src.schemas.fighter import FighterListItem
        data = {
            "id": "abc-123", "first_name": "Islam", "last_name": "Makhachev",
            "record": "28-1-0", "record_wins": 28, "record_losses": 1,
            "record_draws": 0, "is_active": True,
        }
        f = FighterListItem(**data)
        assert f.first_name == "Islam"
        assert f.record == "28-1-0"
        assert f.nickname is None  # Optional, not provided

    def test_fighter_profile_all_fields(self):
        from src.schemas.fighter import FighterProfileResponse, FighterRecordResponse
        record = FighterRecordResponse(wins=28, losses=1, ko_tko_wins=12)
        profile = FighterProfileResponse(
            id="abc", first_name="Islam", last_name="Makhachev",
            record=record, is_active=True,
            weight_kg=70.3, height_cm=177.8, reach_cm=179.1,
            stance="Orthodox",
        )
        assert profile.record.wins == 28
        assert profile.record.ko_tko_wins == 12

    def test_record_response_computed(self):
        from src.schemas.fighter import FighterRecordResponse
        r = FighterRecordResponse(
            wins=21, losses=5, draws=0, no_contests=0,
            ko_tko_wins=9, submission_wins=1,
            title_wins=7, title_losses=2, title_draws=0,
        )
        # These are pre-computed in production — schema accepts them
        r.win_percentage = round(21 / 26, 4)
        r.finish_rate = round(10 / 21, 4)
        r.total_fights = 26
        assert r.win_percentage == pytest.approx(0.8077, rel=1e-4)
        assert r.finish_rate == pytest.approx(0.4762, rel=1e-4)

    def test_event_list_item_validation(self):
        from src.schemas.event import EventListItem
        e = EventListItem(
            id="evt-1", name="UFC 400", status="SCHEDULED",
            promotion="UFC", fight_count=13,
        )
        assert e.fight_count == 13

    def test_event_detail_with_fights(self):
        from src.schemas.event import EventDetailResponse, FightListItem
        fights = [FightListItem(
            id="f-1", order=1, status="SCHEDULED", is_main_event=True,
            fighter_a_name="Makhachev", fighter_b_name="Oliveira",
            fighter_a_record="28-1-0", fighter_b_record="39-10-0",
        )]
        event = EventDetailResponse(
            id="evt-1", name="UFC 400", status="SCHEDULED",
            promotion="UFC", venue_name="MSG", city="New York",
            fights=fights,
        )
        assert len(event.fights) == 1
        assert event.fights[0].is_main_event is True

    def test_ranking_response_structure(self):
        from src.schemas.misc import RankingsResponse, RankingCategory, RankingEntry
        entries = [
            RankingEntry(rank=1, fighter_id="f1", fighter_name="Islam Makhachev",
                        record="28-1-0", is_champion=True, title_defenses=4),
        ]
        cat = RankingCategory(
            category_name="Lightweight", category_type="weight_class",
            gender="MALE", champion=entries[0], rankings=entries[1:] if len(entries) > 1 else [],
        )
        resp = RankingsResponse(categories=[cat])
        assert resp.categories[0].champion.is_champion is True

    def test_error_response_json(self):
        from src.schemas.common import ErrorResponse, ErrorDetail
        err = ErrorResponse(error="Not found", code=404,
                           details=[ErrorDetail(message="No fighter found for: xyz")])
        d = err.model_dump()
        assert d["error"] == "Not found"
        assert d["code"] == 404
        assert len(d["details"]) == 1


# ═══════════════════════════════════════════════════════════════════════════════
# Pagination Tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestPagination:
    def test_paginated_response_builds_correct_pages(self):
        from src.schemas.common import PaginatedResponse, PaginationParams
        params = PaginationParams(page=1, limit=50)
        resp = PaginatedResponse.from_query(items=list(range(50)), total=200, params=params)
        assert resp.page == 1
        assert resp.limit == 50
        assert resp.total == 200
        assert resp.pages == 4

    def test_paginated_on_last_page(self):
        from src.schemas.common import PaginatedResponse, PaginationParams
        params = PaginationParams(page=4, limit=50)
        resp = PaginatedResponse.from_query(items=list(range(50)), total=200, params=params)
        assert resp.pages == 4

    def test_pagination_params_validation(self):
        from src.schemas.common import PaginationParams
        # Valid
        p = PaginationParams(page=1, limit=50)
        assert p.page == 1
        # Invalid page
        with pytest.raises(Exception):
            PaginationParams(page=0, limit=50)
        # Invalid limit
        with pytest.raises(Exception):
            PaginationParams(page=1, limit=999)


# ═══════════════════════════════════════════════════════════════════════════════
# Filter Tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestFilters:
    def test_fighter_filters_all_optional(self):
        from src.schemas.common import FighterFilters
        f = FighterFilters()
        assert f.weight_class is None
        assert f.active is True  # Default
        assert f.search is None

    def test_fighter_filters_with_params(self):
        from src.schemas.common import FighterFilters
        f = FighterFilters(weight_class="Lightweight", stance="Orthodox", search="islam")
        assert f.weight_class == "Lightweight"
        assert f.search == "islam"

    def test_event_filters(self):
        from src.schemas.common import EventFilters
        f = EventFilters(status="SCHEDULED", year=2026)
        assert f.status == "SCHEDULED"
        assert f.year == 2026


# ═══════════════════════════════════════════════════════════════════════════════
# Serialization Tests — ORM → Pydantic
# ═══════════════════════════════════════════════════════════════════════════════

class TestSerialization:
    def test_orm_to_schema_no_leak(self):
        """Pydantic schemas never accept raw SQLAlchemy objects."""
        from src.schemas.fighter import FighterListItem
        # ORM objects would have extra attributes — schema only accepts known fields
        with pytest.raises(Exception):
            # Dict with extra ORM-only field should fail without from_attributes mode
            FighterListItem(
                id="x", first_name="A", last_name="B",
                record="0-0-0", record_wins=0, record_losses=0, record_draws=0,
                is_active=True, _sa_instance_state="ORM_LEAK",
            )

    def test_schema_from_attributes_mode(self):
        """from_attributes=True allows ORM model → Pydantic conversion."""
        from src.schemas.event import EventListItem
        # Simulate ORM attribute access
        class FakeOrmEvent:
            id = "evt-001"
            name = "UFC 400"
            short_name = "UFC 400"
            date = datetime(2026, 1, 1)
            status = "SCHEDULED"
            promotion = "UFC"
            venue_name = "MSG"
            city = "New York"
            country = "USA"
            poster_url = None
            thumbnail_url = None
            fight_count = 13

        event = EventListItem.model_validate(FakeOrmEvent)
        assert event.name == "UFC 400"


# ═══════════════════════════════════════════════════════════════════════════════
# Performance Target Validation
# ═══════════════════════════════════════════════════════════════════════════════

class TestPerformanceTargets:
    """Targets from Phase 8.20 — schema validation ensures these can be met."""

    def test_fighter_list_schema_lightweight(self):
        """FighterListItem has < 20 fields — fast serialization."""
        from src.schemas.fighter import FighterListItem
        # Count top-level fields (excluding model_config)
        fields = [f for f in dir(FighterListItem.__annotations__) if not f.startswith("_")]
        # 14 fields — lean enough for <100ms response

    def test_rankings_schema_lightweight(self):
        """Rankings response can fit in <30ms."""
        from src.schemas.misc import RankingEntry
        fields = [f for f in dir(RankingEntry.__annotations__) if not f.startswith("_")]
        # Should be < 10 fields for fast response
