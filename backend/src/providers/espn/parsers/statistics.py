"""ESPN Statistics Parser — PRODUCTION v2.

Extracts ALL career statistics from /athletes/{id}/statistics with normalization.
Maps ESPN naming conventions to standardized labels.

Categories available (verified from ESPN payloads):
- GENERAL: knockdowns, avgFightTime, sigStrikesByPosition, sigStrikesByTarget
- STRIKING: sigStrikesLandedPerMin, sigStrikesAccuracy, sigStrikesAbsorbedPerMin, sigStrikesDefense
- GRAPPLING: takedownAvgPer15Min, takedownAccuracy, takedownDefense, submissionAvgPer15Min
"""

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from src.providers.dto import StatisticDTO

logger = logging.getLogger(__name__)


# ── Normalization maps ─────────────────────────────────────────────────────────

class StatCategory(Enum):
    GENERAL = "General"
    STRIKING = "Striking"
    GRAPPLING = "Grappling"


# ESPN raw stat name → standardized label, unit, category
STAT_NORMALIZATION: dict[str, dict[str, str]] = {
    # — Striking —
    "sigStrikesLandedPerMin":    {"label": "Sig. Strikes Landed/Min",       "unit": "/min",       "category": "Striking"},
    "sigStrikesAbsorbedPerMin":  {"label": "Sig. Strikes Absorbed/Min",     "unit": "/min",       "category": "Striking"},
    "sigStrikesAccuracy":        {"label": "Sig. Strike Accuracy",           "unit": "%",          "category": "Striking"},
    "sigStrikesDefense":         {"label": "Sig. Strike Defense",            "unit": "%",          "category": "Striking"},
    "sigStrikesLanded":          {"label": "Sig. Strikes Landed",            "unit": "",           "category": "Striking"},
    "sigStrikesAttempted":       {"label": "Sig. Strikes Attempted",         "unit": "",           "category": "Striking"},
    # — Grappling —
    "takedownAvgPer15Min":       {"label": "Takedowns Avg/15 Min",           "unit": "/15min",     "category": "Grappling"},
    "takedownAccuracy":          {"label": "Takedown Accuracy",              "unit": "%",          "category": "Grappling"},
    "takedownDefense":           {"label": "Takedown Defense",                "unit": "%",          "category": "Grappling"},
    "takedownsLanded":           {"label": "Takedowns Landed",               "unit": "",           "category": "Grappling"},
    "takedownsAttempted":        {"label": "Takedowns Attempted",            "unit": "",           "category": "Grappling"},
    "submissionAvgPer15Min":     {"label": "Submission Attempts/15 Min",     "unit": "/15min",     "category": "Grappling"},
    "submissionsAttempted":      {"label": "Submission Attempts",            "unit": "",           "category": "Grappling"},
    "reversals":                 {"label": "Reversals",                      "unit": "",           "category": "Grappling"},
    # — General —
    "knockdowns":                {"label": "Knockdowns",                     "unit": "",           "category": "General"},
    "knockdownsLanded":          {"label": "Knockdowns Landed",              "unit": "",           "category": "General"},
    "avgFightTime":              {"label": "Average Fight Time",             "unit": "sec",        "category": "General"},
    "totalFights":               {"label": "Total Fights",                   "unit": "",           "category": "General"},
    "controlTime":               {"label": "Control Time",                   "unit": "sec",        "category": "General"},
    "ctrlTime":                  {"label": "Control Time",                   "unit": "sec",        "category": "General"},
}


def normalize_stat_name(raw_name: str) -> dict[str, str] | None:
    """Map raw ESPN stat name → standardized label + unit + category."""
    return STAT_NORMALIZATION.get(raw_name)


@dataclass
class FighterStatistics:
    """Complete fighter statistics, organized by category."""

    fighter_external_id: str = ""
    competition_external_id: str = ""  # Empty for career stats

    # Striking
    sig_strikes_landed_per_min: float | None = None
    sig_strikes_accuracy: float | None = None
    sig_strikes_absorbed_per_min: float | None = None
    sig_strikes_defense: float | None = None

    # Grappling
    takedown_avg_per_15min: float | None = None
    takedown_accuracy: float | None = None
    takedown_defense: float | None = None
    submission_avg_per_15min: float | None = None

    # General
    knockdowns: float | None = None
    avg_fight_time_sec: float | None = None
    control_time_sec: float | None = None

    # Raw DTOs for storage
    raw_dtos: list[StatisticDTO] = field(default_factory=list)


def parse_statistics(
    data: dict[str, Any],
    fighter_external_id: str,
    competition_external_id: str = "",
) -> FighterStatistics:
    """Parse ESPN statistics → structured FighterStatistics with normalization.

    Args:
        data: Raw JSON from /athletes/{id}/statistics
        fighter_external_id: ESPN athlete ID
        competition_external_id: Optional competition ID (for per-fight stats)

    Returns:
        FighterStatistics with all extracted and normalized values.
    """
    result = FighterStatistics(
        fighter_external_id=fighter_external_id,
        competition_external_id=competition_external_id,
    )

    splits = data.get("splits", {}) or {}
    categories = splits.get("categories", []) or []
    if not categories:
        return result

    raw_stats: dict[str, float] = {}

    for category in categories:
        if not isinstance(category, dict):
            continue
        category_name = category.get("displayName") or category.get("name", "")

        stats_list = category.get("stats", []) or []
        for stat in stats_list:
            if not isinstance(stat, dict):
                continue

            raw_name = stat.get("name", "")
            value = stat.get("value", 0) or 0
            display_value = stat.get("displayValue") or str(value)

            # Collect raw value
            raw_stats[raw_name] = float(value)

            # Create DTO
            norm = normalize_stat_name(raw_name)
            label = norm["label"] if norm else (stat.get("displayName") or raw_name)
            cat = norm["category"] if norm else category_name
            norm["unit"] if norm else ""

            result.raw_dtos.append(StatisticDTO(
                fighter_external_id=fighter_external_id,
                competition_external_id=competition_external_id,
                category=cat,
                label=label,
                value=float(value),
                display_value=str(display_value),
            ))

    # ── Populate typed fields ────────────────────────────────────────────
    result.sig_strikes_landed_per_min = raw_stats.get("sigStrikesLandedPerMin")
    result.sig_strikes_accuracy = raw_stats.get("sigStrikesAccuracy")
    result.sig_strikes_absorbed_per_min = raw_stats.get("sigStrikesAbsorbedPerMin")
    result.sig_strikes_defense = raw_stats.get("sigStrikesDefense")
    result.takedown_avg_per_15min = raw_stats.get("takedownAvgPer15Min")
    result.takedown_accuracy = raw_stats.get("takedownAccuracy")
    result.takedown_defense = raw_stats.get("takedownDefense")
    result.submission_avg_per_15min = raw_stats.get("submissionAvgPer15Min")
    result.knockdowns = raw_stats.get("knockdowns")
    result.avg_fight_time_sec = raw_stats.get("avgFightTime")
    result.control_time_sec = raw_stats.get("ctrlTime") or raw_stats.get("controlTime")

    return result


def parse_statistics_legacy(
    data: dict[str, Any],
    fighter_external_id: str,
    competition_external_id: str = "",
) -> list[StatisticDTO]:
    """Backward-compatible wrapper returning raw DTO list."""
    return parse_statistics(data, fighter_external_id, competition_external_id).raw_dtos
