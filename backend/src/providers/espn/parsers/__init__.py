"""ESPN Response Parsers — VERIFIED 2026-08-01.

Every parser is a pure function: raw ESPN JSON → provider DTO.
No HTTP calls, no side effects.

NOTE: List endpoints return items as $ref URLs. Individual item parsers
operate on resolved JSON. The ESPNProvider handles $ref resolution.
"""

from src.providers.espn.parsers.promotion import parse_promotion
from src.providers.espn.parsers.fighter import parse_fighter
from src.providers.espn.parsers.records import parse_fighter_records, parse_fighter_records_legacy, FighterRecord
from src.providers.espn.parsers.weight_class import (
    parse_weight_class,
    parse_weight_class_from_athlete,
    parse_weight_class_from_competition,
)
from src.providers.espn.parsers.venue import parse_venue
from src.providers.espn.parsers.event import (
    parse_event,
    extract_competitions_from_event,
    extract_venue_id_from_competition,
)
from src.providers.espn.parsers.competition import (
    parse_competition,
    parse_competition_status,
    extract_weight_class_from_comp,
)
from src.providers.espn.parsers.ranking import parse_ranking_category
from src.providers.espn.parsers.broadcast import parse_broadcast, parse_broadcast_list
from src.providers.espn.parsers.statistics import parse_statistics, FighterStatistics
from src.providers.espn.parsers.records import FighterRecord

__all__ = [
    # Promotion
    "parse_promotion",
    # Fighter
    "parse_fighter",
    "parse_fighter_records",
    "parse_fighter_records_legacy",
    "FighterRecord",
    # Weight Class
    "parse_weight_class",
    "parse_weight_class_from_athlete",
    "parse_weight_class_from_competition",
    # Venue
    "parse_venue",
    # Event
    "parse_event",
    "extract_competitions_from_event",
    "extract_venue_id_from_competition",
    # Competition
    "parse_competition",
    "parse_competition_status",
    "extract_weight_class_from_comp",
    # Ranking
    "parse_ranking_category",
    # Broadcast
    "parse_broadcast",
    "parse_broadcast_list",
    # Statistics
    "parse_statistics",
    "FighterStatistics",
]
