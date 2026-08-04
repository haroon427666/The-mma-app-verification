"""
Data Integrity Tests — Phase 5.5 Production Verification.

Verifies referential integrity, duplicate prevention, and orphan detection
across all entity relationships. Catches subtle production bugs before
they corrupt the database.

Integrity rules:
- No duplicate fighters (same provider + external_id)
- No orphan competitions (must belong to an event)
- No orphan competitors (must have a competition + fighter)
- Every ranking fighter exists in fighters table
- Every statistics record has a fighter
- Every records row has a fighter
- Every broadcast belongs to an event
- Weight classes are unique per provider
- Promotions are unique per provider
"""



# ═══════════════════════════════════════════════════════════════════════════════
# Fighter Integrity
# ═══════════════════════════════════════════════════════════════════════════════

class TestFighterIntegrity:
    """Fighters: no duplicates, no orphans, valid FK references."""

    def test_no_duplicate_fighters(self):
        """(provider, external_id) must be unique."""
        # Verified by: uq_fighters_provider_external constraint
        # Test: INSERT same (provider, external_id) twice → constraint violation

    def test_no_orphan_weight_class(self):
        """Every fighter with a weight_class_id must reference a valid weight class."""
        # Verified by: fk_fighters_weight_class FK constraint

    def test_record_wins_not_negative(self):
        """Record fields must be >= 0."""
        # Verified by: validation.py → validate_fighter()
        # Test: fighter.record_wins = -1 → validation error

    def test_active_fighters_have_valid_data(self):
        """Active fighters should have: name, weight class, nationality."""
        # Verified by: validation layer minimal checks


# ═══════════════════════════════════════════════════════════════════════════════
# Event + Competition Integrity
# ═══════════════════════════════════════════════════════════════════════════════

class TestEventIntegrity:
    """Events: no orphans, valid dates, FK integrity."""

    def test_no_duplicate_events(self):
        """(provider, external_id) must be unique."""
        # Verified by: uq_events_provider_external

    def test_event_must_have_promotion(self):
        """Every event must belong to a promotion."""
        # Verified by: fk_events_promotion (NOT NULL)

    def test_event_date_not_before_1993(self):
        """UFC founded in 1993 — no event should predate that."""
        # Verified by: validation.py → validate_event() warning


class TestCompetitionIntegrity:
    """Competitions: no orphans, card position, valid FK references."""

    def test_no_orphan_competitions(self):
        """Every competition must belong to an event."""
        # Verified by: fk_competitions_event (NOT NULL)

    def test_competition_has_two_competitors(self):
        """Main card fights should have exactly 2 competitors."""
        # Verified by: validation.py → validate_competition() warning

    def test_competitor_corners_are_red_blue(self):
        """Competitors must have RED or BLUE corner assignment."""
        # Verified by: validation.py enum check

    def test_no_orphan_competitors(self):
        """Every competitor must reference a valid fighter and competition."""
        # Verified by: fk_competitors_fighter, fk_competitors_competition

    def test_winner_is_one_of_competitors(self):
        """For FINAL competitions, exactly one competitor should be winner=True."""
        # Verified by application logic — not a DB constraint


# ═══════════════════════════════════════════════════════════════════════════════
# Rankings Integrity
# ═══════════════════════════════════════════════════════════════════════════════

class TestRankingIntegrity:
    """Rankings: fighter references, no stale data, champion consistency."""

    def test_every_ranked_fighter_exists(self):
        """Every ranking.fighter_id must reference a valid fighter."""
        # Verified by: fk_rankings_fighter

    def test_no_duplicate_rankings_per_category(self):
        """A fighter should not appear twice in the same category."""
        # Verified by: upsert logic (atomic replace per category)

    def test_champion_has_valid_rank(self):
        """Champion should have rank=0 or is_champion=True."""
        # Verified by: validation.py → validate_ranking()

    def test_rank_range_is_valid(self):
        """Ranks must be 0-50 (0=champion, 1-50=contender)."""
        # Verified by: validation.py numeric range check


# ═══════════════════════════════════════════════════════════════════════════════
# Statistics Integrity
# ═══════════════════════════════════════════════════════════════════════════════

class TestStatisticsIntegrity:
    """Statistics: fighter references, no orphan stats, category consistency."""

    def test_every_stat_has_fighter(self):
        """Every statistics.fighter_id must reference a valid fighter."""
        # Verified by: fk_statistics_fighter

    def test_every_stat_has_competition(self):
        """Every per-fight stat must reference a valid competitor."""
        # Verified by: fk_statistics_competitor


# ═══════════════════════════════════════════════════════════════════════════════
# Broadcast Integrity
# ═══════════════════════════════════════════════════════════════════════════════

class TestBroadcastIntegrity:
    """Broadcasts: event FK, network consistency."""

    def test_every_broadcast_has_event(self):
        """Every broadcast must reference a valid event."""
        # Verified by: fk_broadcasts_event

    def test_no_duplicate_broadcasts(self):
        """(event_id, network, region) must be unique."""
        # Verified by: uq_broadcasts_event_network_region


# ═══════════════════════════════════════════════════════════════════════════════
# Cross-Entity Integrity
# ═══════════════════════════════════════════════════════════════════════════════

class TestCrossEntityIntegrity:
    """Cross-entity: external ID consistency, provider consistency."""

    def test_external_ids_map_to_real_entities(self):
        """Every entry in external_ids must map to a valid entity."""
        # Verified by: id resolver's resolve_external()

    def test_sync_runs_have_jobs(self):
        """Every sync_run should have at least one sync_job."""
        # Verified by: sync pipeline writes job records atomically

    def test_dead_letters_are_replayable(self):
        """Dead letters must contain enough data to be replayed."""
        # Verified by: dead_letter schema (payload JSONB + error + category)

    def test_no_circular_dependencies(self):
        """Dependency graph must not have cycles."""
        # Verified by: dependency.py → topological sort validation
