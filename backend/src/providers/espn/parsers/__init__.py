"""ESPN Response Parsers — VERIFIED 2026-08-01.

Every parser is a pure function: raw ESPN JSON → provider DTO.
No HTTP calls, no side effects.

NOTE: List endpoints return items as $ref URLs. Individual item parsers
operate on resolved JSON. The ESPNProvider handles $ref resolution.
"""

from src.providers.espn.parsers.broadcast import parse_broadcast, parse_broadcast_list
from src.providers.espn.parsers.competition import (
    extract_weight_class_from_comp,
    parse_competition,
    parse_competition_status,
)
from src.providers.espn.parsers.event import (
    extract_competitions_from_event,
    extract_venue_id_from_competition,
    parse_event,
)
from src.providers.espn.parsers.fighter import parse_fighter
from src.providers.espn.parsers.promotion import parse_promotion
from src.providers.espn.parsers.ranking import parse_ranking_category
from src.providers.espn.parsers.records import (
    FighterRecord,
    parse_fighter_records,
    parse_fighter_records_legacy,
)
from src.providers.espn.parsers.statistics import FighterStatistics, parse_statistics
from src.providers.espn.parsers.venue import parse_venue
from src.providers.espn.parsers.weight_class import (
    parse_weight_class,
    parse_weight_class_from_athlete,
    parse_weight_class_from_competition,
)

__all__ = [
    "FighterRecord",
    "FighterStatistics",
    "extract_competitions_from_event",
    "extract_venue_id_from_competition",
    "extract_weight_class_from_comp",
    # Broadcast
    "parse_broadcast",
    "parse_broadcast_list",
    # Competition
    "parse_competition",
    "parse_competition_status",
    # Event
    "parse_event",
    # Fighter
    "parse_fighter",
    "parse_fighter_records",
    "parse_fighter_records_legacy",
    # Promotion
    "parse_promotion",
    # Ranking
    "parse_ranking_category",
    # Statistics
    "parse_statistics",
    # Venue
    "parse_venue",
    # Weight Class
    "parse_weight_class",
    "parse_weight_class_from_athlete",
    "parse_weight_class_from_competition",
]
