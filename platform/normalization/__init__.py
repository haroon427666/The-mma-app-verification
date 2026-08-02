"""
Normalization Engine — maps every data source into the canonical MMA data model.

Canonical entities:
    Promotion, Event, Fight, Fighter, Ranking, Venue, Location,
    Country, WeightClass, Official, Statistic, Round, Judging

Each source has a Mapper that transforms source-specific fields → canonical schema.
"""

import logging
from dataclasses import dataclass, field
from datetime import date, datetime
from enum import Enum
from typing import Any, Optional

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════
# Canonical Data Model — the single source of truth schema
# ═══════════════════════════════════════════════════════════════════════════

class Gender(str, Enum):
    MALE = "MALE"
    FEMALE = "FEMALE"
    OTHER = "OTHER"


class FightResult(str, Enum):
    WIN = "WIN"
    LOSS = "LOSS"
    DRAW = "DRAW"
    NO_CONTEST = "NO_CONTEST"
    DISQUALIFICATION = "DQ"


class FightMethod(str, Enum):
    KO_TKO = "KO/TKO"
    SUBMISSION = "Submission"
    DECISION_UNANIMOUS = "Decision - Unanimous"
    DECISION_SPLIT = "Decision - Split"
    DECISION_MAJORITY = "Decision - Majority"
    DQ = "DQ"
    NO_CONTEST = "No Contest"


class Stance(str, Enum):
    ORTHODOX = "Orthodox"
    SOUTHPAW = "Southpaw"
    SWITCH = "Switch"
    OPEN_STANCE = "Open Stance"


class CardSegment(str, Enum):
    MAIN_CARD = "Main Card"
    PRELIMS = "Prelims"
    EARLY_PRELIMS = "Early Prelims"


@dataclass
class CanonicalFighter:
    """Canonical fighter — all sources map into this."""
    canonical_id: str = ""
    source_ids: dict[str, str] = field(default_factory=dict)

    first_name: str = ""
    last_name: str = ""
    full_name: str = ""
    nickname: str = ""
    slug: str = ""

    birth_date: Optional[date] = None
    birth_location: str = ""
    nationality: str = ""
    country: str = ""

    height_cm: Optional[float] = None
    weight_kg: Optional[float] = None
    reach_cm: Optional[float] = None
    leg_reach_cm: Optional[float] = None
    stance: Optional[Stance] = None

    weight_class: str = ""
    gender: Gender = Gender.MALE
    is_active: bool = True

    wins: int = 0
    losses: int = 0
    draws: int = 0
    no_contests: int = 0
    ko_tko_wins: int = 0
    submission_wins: int = 0
    decision_wins: int = 0

    gym: str = ""
    fighting_style: str = ""
    biography: str = ""
    debut_date: Optional[date] = None

    images: dict[str, str] = field(default_factory=dict)
    social_links: dict[str, str] = field(default_factory=dict)

    quality_score: float = 0.0
    source_count: int = 0
    last_updated: Optional[datetime] = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "canonical_id": self.canonical_id,
            "source_ids": self.source_ids,
            "first_name": self.first_name, "last_name": self.last_name,
            "full_name": self.full_name, "nickname": self.nickname,
            "nationality": self.nationality, "height_cm": self.height_cm,
            "weight_kg": self.weight_kg, "reach_cm": self.reach_cm,
            "leg_reach_cm": self.leg_reach_cm,
            "stance": self.stance.value if self.stance else None,
            "wins": self.wins, "losses": self.losses, "draws": self.draws,
            "gym": self.gym, "fighting_style": self.fighting_style,
            "quality_score": self.quality_score,
        }


@dataclass
class CanonicalEvent:
    canonical_id: str = ""
    source_ids: dict[str, str] = field(default_factory=dict)
    name: str = ""
    short_name: str = ""
    date_utc: Optional[datetime] = None
    status: str = "SCHEDULED"
    promotion: str = ""
    venue: str = ""
    city: str = ""
    country: str = ""
    fight_count: int = 0
    quality_score: float = 0.0
    source_count: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {k: v for k, v in self.__dict__.items()}


@dataclass
class CanonicalFight:
    canonical_id: str = ""
    source_ids: dict[str, str] = field(default_factory=dict)
    event_id: str = ""
    fighter_a_id: str = ""
    fighter_b_id: str = ""
    weight_class: str = ""
    card_segment: Optional[CardSegment] = None
    is_title_fight: bool = False
    is_main_event: bool = False
    result: Optional[FightResult] = None
    method: Optional[FightMethod] = None
    method_detail: str = ""
    round: Optional[int] = None
    time: str = ""
    quality_score: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {k: v for k, v in self.__dict__.items()}


@dataclass
class CanonicalRanking:
    fighter_id: str = ""
    promotion: str = ""
    category: str = ""
    rank: int = 0
    is_champion: bool = False
    trend: str = ""
    quality_score: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {k: v for k, v in self.__dict__.items()}


# ═══════════════════════════════════════════════════════════════════════════
# Unit Conversion Utilities
# ═══════════════════════════════════════════════════════════════════════════

def lbs_to_kg(lbs: float) -> float:
    return round(lbs * 0.453592, 1)

def inches_to_cm(inches: float) -> float:
    return round(inches * 2.54, 1)

def feet_inches_to_cm(feet: int, inches: int) -> float:
    return round((feet * 12 + inches) * 2.54, 1)


# ═══════════════════════════════════════════════════════════════════════════
# Schema Validator — ensure canonical entities are well-formed
# ═══════════════════════════════════════════════════════════════════════════

class SchemaValidator:
    """Validate canonical entities before persistence."""

    @staticmethod
    def validate_fighter(f: CanonicalFighter) -> list[str]:
        errors = []
        if not f.first_name and not f.last_name:
            errors.append("Missing name")
        if f.height_cm and (f.height_cm < 120 or f.height_cm > 220):
            errors.append(f"Height out of range: {f.height_cm}cm")
        if f.weight_kg and (f.weight_kg < 45 or f.weight_kg > 150):
            errors.append(f"Weight out of range: {f.weight_kg}kg")
        if f.reach_cm and (f.reach_cm < 100 or f.reach_cm > 230):
            errors.append(f"Reach out of range: {f.reach_cm}cm")
        if f.wins < 0 or f.losses < 0:
            errors.append("Negative record counts")
        return errors

    @staticmethod
    def validate_event(e: CanonicalEvent) -> list[str]:
        errors = []
        if not e.name:
            errors.append("Missing event name")
        if not e.date_utc:
            errors.append("Missing event date")
        return errors

    @staticmethod
    def validate_fight(f: CanonicalFight) -> list[str]:
        errors = []
        if not f.fighter_a_id or not f.fighter_b_id:
            errors.append("Missing fighter IDs")
        if f.fighter_a_id == f.fighter_b_id:
            errors.append("Fighter cannot fight themselves")
        return errors


# ═══════════════════════════════════════════════════════════════════════════
# Normalization Engine — orchestrate mapping from any source to canonical
# ═══════════════════════════════════════════════════════════════════════════

class NormalizationEngine:
    """Orchestrates normalization: raw source → canonical entity → validated output."""

    def __init__(self):
        self._mappers: dict[str, dict[str, callable]] = {}
        self._validator = SchemaValidator()
        self._metrics: dict[str, int] = {"total_processed": 0, "valid": 0, "invalid": 0}

    def register_mapper(
        self, source: str, entity_type: str, mapper_fn: callable,
    ):
        """Register a mapping function for a source+entity combination."""
        self._mappers.setdefault(source, {})[entity_type] = mapper_fn

    def normalize(
        self, source: str, entity_type: str, raw_data: list[dict],
    ) -> tuple[list[dict], list[dict], list[str]]:
        """Normalize raw data from a source into canonical entities.

        Returns: (valid_entities, invalid_entities, errors)
        """
        mapper = self._mappers.get(source, {}).get(entity_type)
        if mapper is None:
            raise ValueError(f"No mapper for {source}/{entity_type}")

        valid = []
        invalid = []
        all_errors = []

        for item in raw_data:
            try:
                canonical = mapper(item)
                errors = self._validate(entity_type, canonical)
                if errors:
                    invalid.append(canonical.to_dict() if hasattr(canonical, 'to_dict') else {})
                    all_errors.extend(errors)
                else:
                    valid.append(
                        canonical.to_dict() if hasattr(canonical, 'to_dict') else canonical
                    )
            except Exception as e:
                invalid.append({"error": str(e), "raw": str(item)[:200]})
                all_errors.append(str(e))

        self._metrics["total_processed"] += len(raw_data)
        self._metrics["valid"] += len(valid)
        self._metrics["invalid"] += len(invalid)

        logger.info(
            f"Normalized {source}/{entity_type}: "
            f"{len(valid)} valid, {len(invalid)} invalid"
        )
        return valid, invalid, all_errors

    def _validate(self, entity_type: str, entity: Any) -> list[str]:
        if entity_type == "fighter":
            return self._validator.validate_fighter(entity)
        elif entity_type == "event":
            return self._validator.validate_event(entity)
        elif entity_type == "fight":
            return self._validator.validate_fight(entity)
        return []

    def get_metrics(self) -> dict:
        return dict(self._metrics)
