"""Phase 8 performance indices — hot FK/query columns.

Adds indexes backing the most frequent API and sync queries:
- events.promotion_id            (event list by promotion)
- competitions.event_id          (event detail fights)
- competitors.competition_id     (fights detail)
- competitors.fighter_id         (fighter recent fights)
- rankings.fighter_id            (fighter detail rankings)
- rankings.category_name         (rankings by category)
- statistics.fighter_id          (fighter stats)
- statistics.competitor_id       (competition stats)
- broadcasts.event_id            (event detail broadcasts)
- fighters.weight_class_name     (fighter list filter)
- fighters.nationality           (fighter list filter)
- fighters.full_name             (fighter search)

Revision ID: 003
Revises: 002
Create Date: 2026-08-03
"""
from typing import Sequence, Union

from alembic import op

revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_index("ix_events_promotion_id", "events", ["promotion_id"])
    op.create_index("ix_competitions_event_id", "competitions", ["event_id"])
    op.create_index("ix_competitors_competition_id", "competitors", ["competition_id"])
    op.create_index("ix_competitors_fighter_id", "competitors", ["fighter_id"])
    op.create_index("ix_rankings_fighter_id", "rankings", ["fighter_id"])
    op.create_index("ix_rankings_category_name", "rankings", ["category_name"])
    op.create_index("ix_statistics_fighter_id", "statistics", ["fighter_id"])
    op.create_index("ix_statistics_competitor_id", "statistics", ["competitor_id"])
    op.create_index("ix_broadcasts_event_id", "broadcasts", ["event_id"])
    op.create_index("ix_fighters_weight_class_name", "fighters", ["weight_class_name"])
    op.create_index("ix_fighters_nationality", "fighters", ["nationality"])
    op.create_index("ix_fighters_full_name", "fighters", ["full_name"])


def downgrade() -> None:
    op.drop_index("ix_fighters_full_name", table_name="fighters")
    op.drop_index("ix_fighters_nationality", table_name="fighters")
    op.drop_index("ix_fighters_weight_class_name", table_name="fighters")
    op.drop_index("ix_broadcasts_event_id", table_name="broadcasts")
    op.drop_index("ix_statistics_competitor_id", table_name="statistics")
    op.drop_index("ix_statistics_fighter_id", table_name="statistics")
    op.drop_index("ix_rankings_category_name", table_name="rankings")
    op.drop_index("ix_rankings_fighter_id", table_name="rankings")
    op.drop_index("ix_competitors_fighter_id", table_name="competitors")
    op.drop_index("ix_competitors_competition_id", table_name="competitors")
    op.drop_index("ix_competitions_event_id", table_name="competitions")
    op.drop_index("ix_events_promotion_id", table_name="events")
