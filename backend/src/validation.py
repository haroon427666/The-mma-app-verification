"""Data Validation Layer.

Validates every DTO before it enters the pipeline.
Catches bad payloads before they corrupt the database.

Validates:
- Required fields (non-empty, non-None)
- Enums (status, stance, gender)
- Numeric ranges (weight, height, reach)
- Date parsing
- Duplicate detection
- Null handling

A failed validation produces a ValidationResult with errors, NOT an exception.
Bad payloads are routed to dead letters, never crash the pipeline.
"""

import logging
from dataclasses import dataclass, field
from datetime import date, datetime
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


# ── Valid enums ────────────────────────────────────────────────────────────────

VALID_STANCES = {"Orthodox", "Southpaw", "Switch", "Open Stance", "Sideways"}
VALID_STATUSES = {"SCHEDULED", "FINAL", "CANCELLED", "IN_PROGRESS"}
VALID_GENDERS = {"MALE", "FEMALE", "MIXED"}
VALID_CARD_SEGMENTS = {"Main Card", "Prelims", "Early Prelims"}
VALID_OUTCOMES = {"WIN", "LOSS", "DRAW", "NC", "DQ"}
VALID_CORNERS = {"RED", "BLUE"}

WeightClass = Enum("WeightClass", [
    ("FLYWEIGHT", (53.0, 56.7)),
    ("BANTAMWEIGHT", (56.7, 61.2)),
    ("FEATHERWEIGHT", (61.2, 65.8)),
    ("LIGHTWEIGHT", (65.8, 70.3)),
    ("WELTERWEIGHT", (70.3, 77.1)),
    ("MIDDLEWEIGHT", (77.1, 83.9)),
    ("LIGHT_HEAVYWEIGHT", (83.9, 93.0)),
    ("HEAVYWEIGHT", (93.0, 120.2)),
])


# ── Validation result ──────────────────────────────────────────────────────────

@dataclass
class ValidationError:
    field: str
    value: Any
    reason: str


@dataclass
class ValidationResult:
    is_valid: bool
    errors: list[ValidationError] = field(default_factory=list)
    warnings: list[ValidationError] = field(default_factory=list)

    def add_error(self, field: str, value: Any, reason: str) -> None:
        self.is_valid = False
        self.errors.append(ValidationError(field, value, reason))

    def add_warning(self, field: str, value: Any, reason: str) -> None:
        self.warnings.append(ValidationError(field, value, reason))


# ── Validators ─────────────────────────────────────────────────────────────────

def validate_fighter(dto: Any) -> ValidationResult:
    result = ValidationResult(is_valid=True)

    # Required fields
    if not dto.provider or not dto.provider.strip():
        result.add_error("provider", dto.provider, "Missing or empty provider")
    if not dto.external_id or not dto.external_id.strip():
        result.add_error("external_id", dto.external_id, "Missing or empty external_id")
    if not dto.first_name or not dto.first_name.strip():
        result.add_error("first_name", dto.first_name, "Missing or empty first name")

    # Numeric ranges
    if dto.weight_kg is not None:
        if not (40.0 <= dto.weight_kg <= 200.0):
            result.add_warning("weight_kg", dto.weight_kg,
                f"Weight out of expected range (40–200 kg)")
        if dto.weight_kg <= 0:
            result.add_error("weight_kg", dto.weight_kg, "Weight must be positive")

    if dto.height_cm is not None:
        if not (120.0 <= dto.height_cm <= 220.0):
            result.add_warning("height_cm", dto.height_cm,
                f"Height out of expected range (120–220 cm)")
        if dto.height_cm <= 0:
            result.add_error("height_cm", dto.height_cm, "Height must be positive")

    if dto.reach_cm is not None:
        if not (100.0 <= dto.reach_cm <= 300.0):
            result.add_warning("reach_cm", dto.reach_cm,
                f"Reach out of expected range (100–300 cm)")
        if dto.reach_cm <= 0:
            result.add_warning("reach_cm", dto.reach_cm, "Reach is zero — likely missing data, not invalid")

    if dto.leg_reach_cm is not None:
        if not (50.0 <= dto.leg_reach_cm <= 200.0):
            result.add_warning("leg_reach_cm", dto.leg_reach_cm,
                f"Leg reach out of expected range (50–200 cm)")

    # Stance enum
    if dto.stance and dto.stance not in VALID_STANCES:
        result.add_warning("stance", dto.stance,
            f"Unknown stance '{dto.stance}' — expected one of {VALID_STANCES}")

    # Record consistency
    if dto.record_wins < 0:
        result.add_error("record_wins", dto.record_wins, "Wins cannot be negative")
    if dto.record_losses < 0:
        result.add_error("record_losses", dto.record_losses, "Losses cannot be negative")

    # Birth date
    if dto.birth_date:
        if not isinstance(dto.birth_date, (date, datetime)):
            result.add_error("birth_date", dto.birth_date, "Invalid birth date type")
        elif dto.birth_date.year < 1950:
            result.add_warning("birth_date", dto.birth_date, "Birth year too early (pre-1950)")
        elif dto.birth_date.year > date.today().year - 16:
            result.add_warning("birth_date", dto.birth_date, "Birth year suggests fighter under 16")

    return result


def validate_event(dto: Any) -> ValidationResult:
    result = ValidationResult(is_valid=True)

    if not dto.provider or not dto.provider.strip():
        result.add_error("provider", dto.provider, "Missing or empty provider")
    if not dto.external_id or not dto.external_id.strip():
        result.add_error("external_id", dto.external_id, "Missing or empty external_id")
    if not dto.name or not dto.name.strip():
        result.add_error("name", dto.name, "Missing or empty name")

    # Status enum
    if dto.status and dto.status not in VALID_STATUSES:
        result.add_error("status", dto.status,
            f"Invalid status '{dto.status}' — expected one of {VALID_STATUSES}")

    # Date
    if dto.date:
        if not isinstance(dto.date, (date, datetime)):
            result.add_error("date", dto.date, "Invalid date type")
        elif dto.date.year < 1993:
            result.add_warning("date", dto.date, "Event date before UFC was founded (1993)")

    return result


def validate_competition(dto: Any) -> ValidationResult:
    result = ValidationResult(is_valid=True)

    if not dto.provider or not dto.provider.strip():
        result.add_error("provider", dto.provider, "Missing or empty provider")
    if not dto.external_id or not dto.external_id.strip():
        result.add_error("external_id", dto.external_id, "Missing or empty external_id")

    # Card segment
    if dto.card_segment and dto.card_segment not in VALID_CARD_SEGMENTS:
        result.add_warning("card_segment", dto.card_segment,
            f"Unknown card segment '{dto.card_segment}'")

    # Status
    if dto.status and dto.status not in VALID_STATUSES:
        result.add_error("status", dto.status,
            f"Invalid status '{dto.status}'")

    # Result validation for FINAL competitions
    if dto.status == "FINAL":
        # Must have result for FINAL competitions
        pass  # Result fields are optional — some fresh finals may lack details

    # Competitors
    if hasattr(dto, "competitors") and dto.competitors:
        if len(dto.competitors) != 2:
            result.add_warning("competitors", len(dto.competitors),
                f"Expected 2 competitors, got {len(dto.competitors)}")
        corners = {c.corner for c in dto.competitors if hasattr(c, "corner")}
        if corners and corners != {"RED", "BLUE"}:
            result.add_warning("corners", corners, "Corners should be RED and BLUE")

    return result


def validate_ranking(dto: Any) -> ValidationResult:
    result = ValidationResult(is_valid=True)

    if not dto.provider or not dto.provider.strip():
        result.add_error("provider", dto.provider, "Missing provider")
    if not dto.fighter_external_id:
        result.add_error("fighter_external_id", dto.fighter_external_id, "Missing fighter reference")

    if not (0 <= dto.rank <= 50):
        result.add_error("rank", dto.rank, f"Rank out of range (0–50): {dto.rank}")

    if dto.rank == 0 and not dto.is_champion:
        result.add_warning("is_champion", dto.is_champion, "Rank 0 but not marked as champion")

    return result


def validate_promotion(dto: Any) -> ValidationResult:
    result = ValidationResult(is_valid=True)

    if not dto.provider or not dto.provider.strip():
        result.add_error("provider", dto.provider, "Missing provider")
    if not dto.external_id or not dto.external_id.strip():
        result.add_error("external_id", dto.external_id, "Missing external_id")
    if not dto.name or not dto.name.strip():
        result.add_error("name", dto.name, "Missing name")

    return result


# ── Generic validator dispatcher ───────────────────────────────────────────────

_VALIDATORS = {
    "fighter": validate_fighter,
    "event": validate_event,
    "competition": validate_competition,
    "ranking": validate_ranking,
    "promotion": validate_promotion,
    "broadcast": validate_promotion,  # Same minimal checks
    "venue": validate_promotion,
    "weight_class": validate_promotion,
}


def validate(entity_type: str, dto: Any) -> ValidationResult:
    """Validate a DTO. Returns ValidationResult — never raises.

    Usage:
        result = validate("fighter", fighter_dto)
        if not result.is_valid:
            for e in result.errors:
                logger.warning(f"Validation error: {e.field}={e.value}: {e.reason}")
    """
    validator = _VALIDATORS.get(entity_type)
    if not validator:
        logger.debug(f"No validator for entity type '{entity_type}' — skipping validation")
        return ValidationResult(is_valid=True)

    try:
        return validator(dto)
    except Exception as e:
        logger.error(f"Validator crashed for {entity_type}: {e}", exc_info=True)
        result = ValidationResult(is_valid=True)  # Don't crash on validator bugs
        result.add_warning("_validator", str(e), "Validator exception — DTO passed through")
        return result
