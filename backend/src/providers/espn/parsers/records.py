"""ESPN Fighter Records Parser — PRODUCTION v2.

Extracts ALL fields from the /athletes/{id}/records endpoint.
Previously only extracted W/L/D/NC. Now extracts:
- KO/TKO wins & losses
- Submission wins & losses
- Title fight wins, losses, draws
- Win percentage
- Record summary string

Real payload shape (verified 2026-08-01):
{
  "count":1, "pageIndex":1, "pageSize":25, "pageCount":1,
  "items":[{
    "name":"overall", "summary":"21-5-0", "displayValue":"21-5-0",
    "value":0.8076923076923077,
    "stats":[
      {"name":"wins","value":21.0,"displayValue":"21"},
      {"name":"losses","value":5.0,"displayValue":"5"},
      {"name":"draws","value":0.0,"displayValue":"0"},
      {"name":"noContests","value":0.0,"displayValue":"0"},
      {"name":"submissions","value":1.0,"displayValue":"1"},
      {"name":"submissionLosses","value":1.0,"displayValue":"1"},
      {"name":"tkos","value":9.0,"displayValue":"9"},
      {"name":"tkoLosses","value":1.0,"displayValue":"1"},
      {"name":"titleWins","value":7.0,"displayValue":"7"},
      {"name":"titleLosses","value":2.0,"displayValue":"2"},
      {"name":"titleDraws","value":0.0,"displayValue":"0"}
    ]
  }]
}
"""

import logging
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class FighterRecord:
    """Complete fighter record with all available breakdowns."""

    # Basic record
    wins: int = 0
    losses: int = 0
    draws: int = 0
    no_contests: int = 0

    # Method breakdown
    ko_tko_wins: int = 0
    ko_tko_losses: int = 0
    submission_wins: int = 0
    submission_losses: int = 0

    # Title fights
    title_wins: int = 0
    title_losses: int = 0
    title_draws: int = 0

    # Computed
    total_fights: int = 0
    win_percentage: float = 0.0
    finish_rate: float = 0.0  # % of wins by finish (KO/TKO + Submission)

    # Display
    record_summary: str = ""
    record_display: str = ""

    # Raw data for debugging
    _raw_stats: dict[str, float] = field(default_factory=dict, repr=False)


def parse_fighter_records(records_data: dict[str, Any]) -> FighterRecord:
    """Parse ALL available fields from ESPN /records endpoint.

    Args:
        records_data: Raw JSON from /athletes/{id}/records

    Returns:
        FighterRecord with all available breakdowns.
    """
    record = FighterRecord()

    items = records_data.get("items", [])
    if not items:
        return record

    for item in items:
        if not isinstance(item, dict):
            continue
        if item.get("name") != "overall":
            continue

        # ── Item-level fields ──────────────────────────────────────────
        record.record_summary = item.get("summary", "") or ""
        record.record_display = item.get("displayValue", "") or ""

        win_pct = item.get("value")
        if win_pct is not None:
            record.win_percentage = round(float(win_pct), 4)

        # ── Stats array ─────────────────────────────────────────────────
        stats_list = item.get("stats", [])
        raw_stats: dict[str, float] = {}

        for stat in stats_list:
            if not isinstance(stat, dict):
                continue
            name = stat.get("name", "").strip()
            value = stat.get("value", 0)
            if isinstance(value, (int, float)):
                raw_stats[name] = float(value)
            elif isinstance(value, str):
                try:
                    raw_stats[name] = float(value)
                except ValueError:
                    continue

        record._raw_stats = raw_stats

        # ── Extract known fields ────────────────────────────────────────
        record.wins = int(raw_stats.get("wins", 0))
        record.losses = int(raw_stats.get("losses", 0))
        record.draws = int(raw_stats.get("draws", 0))
        record.no_contests = int(raw_stats.get("noContests", 0))

        # ESPN calls these "submissions" = submission wins, "tkos" = KO/TKO wins
        record.submission_wins = int(raw_stats.get("submissions", 0))
        record.submission_losses = int(raw_stats.get("submissionLosses", 0))
        record.ko_tko_wins = int(raw_stats.get("tkos", 0))
        record.ko_tko_losses = int(raw_stats.get("tkoLosses", 0))

        record.title_wins = int(raw_stats.get("titleWins", 0))
        record.title_losses = int(raw_stats.get("titleLosses", 0))
        record.title_draws = int(raw_stats.get("titleDraws", 0))

        # ── Computed fields ─────────────────────────────────────────────
        record.total_fights = record.wins + record.losses + record.draws + record.no_contests

        # Win percentage (use ESPN's computed value if available, or compute)
        if record.win_percentage == 0.0 and record.total_fights > 0:
            record.win_percentage = round(record.wins / record.total_fights, 4)

        # Finish rate: % of wins that came by KO/TKO or submission
        if record.wins > 0:
            record.finish_rate = round(
                (record.ko_tko_wins + record.submission_wins) / record.wins, 4
            )
        else:
            record.finish_rate = 0.0

    return record


# ── Backward-compatible adapter ────────────────────────────────────────────────

def parse_fighter_records_legacy(records_data: dict[str, Any]) -> dict[str, int]:
    """Backward-compatible wrapper. Returns {wins, losses, draws, no_contests}.

    Use parse_fighter_records() for the full FighterRecord dataclass.
    """
    record = parse_fighter_records(records_data)
    return {
        "wins": record.wins,
        "losses": record.losses,
        "draws": record.draws,
        "no_contests": record.no_contests,
    }
