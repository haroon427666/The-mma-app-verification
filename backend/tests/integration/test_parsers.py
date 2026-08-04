"""
Parser integration tests — every ESPN parser tested against real payloads.

Tests validate:
- Correct field extraction (every DTO field)
- Unit conversions (lbs→kg, in→cm)
- Edge cases (reach=0.0, empty images, missing fields)
- $ref ID extraction with query params
- No crashes on malformed data
"""



class TestPromotionParser:
    """Promotion parser against real UFC payload."""

    def test_ufc_fields(self, ufc_promotion, parse_promotion):
        dto = parse_promotion(ufc_promotion)
        assert dto.provider == "espn"
        assert dto.external_id == "3321"
        assert dto.name == "Ultimate Fighting Championship"
        assert dto.slug == "ufc"
        assert dto.season_year == 2026
        assert dto.logo_url is not None
        assert "espncdn.com" in dto.logo_url

    def test_empty_dict_no_crash(self, parse_promotion):
        dto = parse_promotion({})
        assert dto.name == ""
        assert dto.external_id == ""


class TestFighterParser:
    """Fighter parser tested against active and inactive fighters."""

    def test_inactive_fighter_edge_cases(self, jason_reinhardt, parse_fighter):
        """Jason Reinhardt: inactive, reach=0.0, empty images, no dateOfBirth."""
        dto = parse_fighter(jason_reinhardt)
        assert dto.external_id == "2354359"
        assert dto.first_name == "Jason"
        assert dto.last_name == "Reinhardt"
        assert dto.weight_kg == 65.8   # 145 lbs → kg
        assert dto.height_cm == 167.6  # 66 in → cm
        assert dto.reach_cm == 0.0     # BUG WAS HERE: 0.0 treated as falsy
        assert dto.stance == "Orthodox"
        assert dto.weight_class_external_id == "970"
        assert dto.headshot_url is None  # Empty images[]
        assert dto.is_active is False

    def test_active_champion(self, islam_makhachev, parse_fighter):
        """Islam Makhachev: active champion with all fields."""
        dto = parse_fighter(islam_makhachev)
        assert dto.external_id == "3088812"
        assert dto.first_name == "Islam"
        assert dto.last_name == "Makhachev"
        assert dto.weight_kg == 70.3   # 155 lbs → kg
        assert dto.height_cm == 177.8  # 70 in → cm
        assert dto.reach_cm == 179.1   # 70.5 in → cm
        assert dto.stance == "Orthodox"
        assert dto.nationality == "Russia"
        assert dto.birth_date is not None
        assert dto.birth_date.year == 1991
        assert dto.birth_date.month == 10
        assert dto.is_active is True
        assert dto.weight_class_external_id == "986"

    def test_malformed_no_crash(self, malformed_fighter, parse_fighter):
        """Malformed fighter: missing fields, null weightClass, 0.0 values."""
        dto = parse_fighter(malformed_fighter)
        assert dto.external_id == "9999999"
        assert dto.first_name == ""
        assert dto.weight_kg == 0.0
        assert dto.reach_cm == 0.0
        assert dto.stance is None
        assert dto.headshot_url is None

    def test_empty_dict_no_crash(self, parse_fighter):
        dto = parse_fighter({})
        assert dto.first_name == ""
        assert dto.external_id == ""


class TestFighterRecordsParser:
    """Fighter records parser against real /records endpoint data."""

    def test_makhachev_record(self, fighter_records, parse_fighter_records):
        rec = parse_fighter_records(fighter_records)
        assert rec["wins"] == 21
        assert rec["losses"] == 5
        assert rec["draws"] == 0
        assert rec["no_contests"] == 0

    def test_empty_records(self, parse_fighter_records):
        rec = parse_fighter_records({"items": []})
        assert rec["wins"] == 0
        assert rec["losses"] == 0


class TestEventParser:
    """Event parser against real scheduled event."""

    def test_scheduled_event(self, event_scheduled, parse_event):
        dto = parse_event(event_scheduled)
        assert dto.external_id == "600059339"
        assert "UFC Fight Night" in dto.name
        assert dto.status == "SCHEDULED"
        assert dto.date is not None
        assert dto.date.year == 2026


class TestCompetitionParser:
    """Competition parser — SCHEDULED and FINAL."""

    def test_main_event(self, competition_main_event, parse_competition):
        dto = parse_competition(competition_main_event)
        assert dto.external_id == "401870843"
        assert dto.card_segment == "Main Card"
        assert dto.is_main_event is True
        assert dto.weight_class_external_id == "969"
        assert len(dto.competitors) == 2
        assert dto.competitors[0].corner == "BLUE"
        assert dto.competitors[1].corner == "RED"

    def test_final_competition(self, competition_final, parse_competition):
        dto = parse_competition(competition_final)
        assert dto.status == "FINAL"
        assert dto.competitors[0].outcome == "WIN"
        assert dto.competitors[1].outcome == "LOSS"

    def test_competition_status_enrichment(self, competition_final, competition_status, parse_competition, parse_competition_status):
        """Parse competition, then enrich with status endpoint data."""
        dto = parse_competition(competition_final)
        dto = parse_competition_status(competition_status, dto)
        assert dto.result_method == "Submission"
        assert dto.result_detail == "D'Arce Choke"
        assert dto.result_round == 3
        assert dto.result_time == "4:05"


class TestRankingParser:
    """Ranking parser against P4P and heavyweight categories."""

    def test_p4p_rankings(self, rankings_p4p, parse_ranking_category):
        rankings = parse_ranking_category(rankings_p4p, "3321")
        assert len(rankings) == 2
        assert rankings[0].rank == 1
        assert rankings[0].is_champion is True

    def test_heavyweight_with_trend(self, rankings_heavyweight, parse_ranking_category):
        rankings = parse_ranking_category(rankings_heavyweight, "3321")
        assert len(rankings) == 3
        assert rankings[2].rank == 3
        assert rankings[2].trend == "+2"


class TestBroadcastParser:
    def test_ppv_broadcast(self, broadcast_ppv, parse_broadcast):
        dto = parse_broadcast(broadcast_ppv, "600059339")
        assert dto.network == "PPV"
        assert dto.region == "National"
        assert dto.language == "en"
        assert dto.broadcast_type == "PPV"
        assert dto.event_external_id == "600059339"


class TestVenueParser:
    def test_belgrade_arena(self, venue_belgrade, parse_venue):
        dto = parse_venue(venue_belgrade)
        assert dto.external_id == "3115"
        assert dto.name == "Belgrade Arena"
        assert dto.city == "Belgrade"
        assert dto.country == "Serbia"


class TestRefResolver:
    """$ref URL ID extraction — verifies the query-param bug fix."""

    def test_extract_with_query_params(self, extract_id_from_ref):
        assert extract_id_from_ref(
            "http://sports.core.api.espn.com/v2/sports/mma/athletes/3088812?lang=en&region=us"
        ) == "3088812"

    def test_extract_without_query_params(self, extract_id_from_ref):
        assert extract_id_from_ref(
            "http://sports.core.api.espn.com/v2/sports/mma/leagues/ufc"
        ) == "ufc"

    def test_extract_venue_with_params(self, extract_id_from_ref):
        assert extract_id_from_ref(
            "http://sports.core.api.espn.com/v2/sports/mma/leagues/ufc/venues/3115?lang=en&region=us"
        ) == "3115"


class TestDTOConstruction:
    """DTOs are valid dataclasses that accept parser output."""

    def test_fighter_dto_from_parser(self, islam_makhachev, parse_fighter):
        dto = parse_fighter(islam_makhachev)
        # Verify it's a valid dataclass with all expected attributes
        assert hasattr(dto, "provider")
        assert hasattr(dto, "external_id")
        assert hasattr(dto, "first_name")
        assert hasattr(dto, "last_name")
        assert hasattr(dto, "nickname")
        assert hasattr(dto, "weight_kg")
        assert hasattr(dto, "height_cm")
        assert hasattr(dto, "reach_cm")
        assert hasattr(dto, "stance")
        assert hasattr(dto, "is_active")
        assert hasattr(dto, "record_wins")
        assert hasattr(dto, "record_losses")
        assert hasattr(dto, "record_draws")
        assert hasattr(dto, "record_no_contests")


class TestEmptyListResponses:
    """Empty paginated responses should not crash."""

    def test_empty_athlete_list(self, athlete_list_empty):
        items = athlete_list_empty.get("items", [])
        assert items == []
        assert athlete_list_empty["count"] == 0
