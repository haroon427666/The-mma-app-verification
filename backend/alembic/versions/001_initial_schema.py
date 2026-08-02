"""Initial schema — all tables from DATA_CONTRACT.md v2.0

Revision ID: 001
Revises:
Create Date: 2026-08-01
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── promotions ─────────────────────────────────────────────────────────
    op.create_table(
        "promotions",
        sa.Column("id", sa.Uuid(), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("provider", sa.String(20), nullable=False),
        sa.Column("external_id", sa.String(50), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("abbreviation", sa.String(10), nullable=True),
        sa.Column("short_name", sa.String(50), nullable=True),
        sa.Column("slug", sa.String(100), nullable=True),
        sa.Column("country", sa.String(100), nullable=True),
        sa.Column("founded_year", sa.Integer(), nullable=True),
        sa.Column("first_event_date", sa.Date(), nullable=True),
        sa.Column("gender", sa.String(10), nullable=True),
        sa.Column("season_year", sa.Integer(), nullable=True),
        sa.Column("logo_url", sa.Text(), nullable=True),
        sa.Column("poster_url", sa.Text(), nullable=True),
        sa.Column("banner_url", sa.Text(), nullable=True),
        sa.Column("trophy_url", sa.Text(), nullable=True),
        sa.Column("fanart_urls", sa.JSON(), nullable=True),
        sa.Column("website", sa.Text(), nullable=True),
        sa.Column("facebook_url", sa.Text(), nullable=True),
        sa.Column("instagram_url", sa.Text(), nullable=True),
        sa.Column("twitter_url", sa.Text(), nullable=True),
        sa.Column("youtube_url", sa.Text(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("tv_rights", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.UniqueConstraint("provider", "external_id", name="uq_promotions_provider_external"),
    )

    # ── weight_classes ─────────────────────────────────────────────────────
    op.create_table(
        "weight_classes",
        sa.Column("id", sa.Uuid(), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("provider", sa.String(20), nullable=False),
        sa.Column("external_id", sa.String(20), nullable=False),
        sa.Column("name", sa.String(50), nullable=False),
        sa.Column("abbreviation", sa.String(30), nullable=True),
        sa.Column("min_weight_kg", sa.Float(), nullable=True),
        sa.Column("max_weight_kg", sa.Float(), nullable=True),
        sa.Column("gender", sa.String(10), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.UniqueConstraint("provider", "external_id", name="uq_weight_classes_provider_external"),
    )

    # ── venues ─────────────────────────────────────────────────────────────
    op.create_table(
        "venues",
        sa.Column("id", sa.Uuid(), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("provider", sa.String(20), nullable=False),
        sa.Column("external_id", sa.String(20), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("city", sa.String(100), nullable=True),
        sa.Column("state", sa.String(100), nullable=True),
        sa.Column("country", sa.String(100), nullable=True),
        sa.Column("latitude", sa.Float(), nullable=True),
        sa.Column("longitude", sa.Float(), nullable=True),
        sa.Column("capacity", sa.Integer(), nullable=True),
        sa.Column("indoor", sa.Boolean(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.UniqueConstraint("provider", "external_id", name="uq_venues_provider_external"),
    )

    # ── fighters ───────────────────────────────────────────────────────────
    op.create_table(
        "fighters",
        sa.Column("id", sa.Uuid(), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("provider", sa.String(20), nullable=False),
        sa.Column("external_id", sa.String(50), nullable=False),
        sa.Column("first_name", sa.String(100), nullable=False),
        sa.Column("last_name", sa.String(100), nullable=False),
        sa.Column("full_name", sa.String(200), nullable=True),
        sa.Column("short_name", sa.String(50), nullable=True),
        sa.Column("nickname", sa.String(100), nullable=True),
        sa.Column("slug", sa.String(200), nullable=True),
        sa.Column("weight_kg", sa.Float(), nullable=True),
        sa.Column("height_cm", sa.Float(), nullable=True),
        sa.Column("reach_cm", sa.Float(), nullable=True),
        sa.Column("leg_reach_cm", sa.Float(), nullable=True),
        sa.Column("stance", sa.String(20), nullable=True),
        sa.Column("weight_class_id", sa.Uuid(), nullable=True),
        sa.Column("weight_class_name", sa.String(50), nullable=True),
        sa.Column("nationality", sa.String(100), nullable=True),
        sa.Column("birth_date", sa.Date(), nullable=True),
        sa.Column("birth_location", sa.String(200), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("headshot_url", sa.Text(), nullable=True),
        sa.Column("cutout_url", sa.Text(), nullable=True),
        sa.Column("render_url", sa.Text(), nullable=True),
        sa.Column("biography", sa.Text(), nullable=True),
        sa.Column("ethnicity", sa.String(50), nullable=True),
        sa.Column("trains_at", sa.String(200), nullable=True),
        sa.Column("fighting_style", sa.String(50), nullable=True),
        sa.Column("debut_date", sa.Date(), nullable=True),
        sa.Column("record_wins", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("record_losses", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("record_draws", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("record_no_contests", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("facebook_url", sa.Text(), nullable=True),
        sa.Column("instagram_url", sa.Text(), nullable=True),
        sa.Column("twitter_url", sa.Text(), nullable=True),
        sa.Column("wikidata_id", sa.String(20), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.UniqueConstraint("provider", "external_id", name="uq_fighters_provider_external"),
        sa.ForeignKeyConstraint(["weight_class_id"], ["weight_classes.id"], name="fk_fighters_weight_class"),
    )

    # ── events ─────────────────────────────────────────────────────────────
    op.create_table(
        "events",
        sa.Column("id", sa.Uuid(), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("provider", sa.String(20), nullable=False),
        sa.Column("external_id", sa.String(50), nullable=False),
        sa.Column("name", sa.String(300), nullable=False),
        sa.Column("short_name", sa.String(100), nullable=True),
        sa.Column("slug", sa.String(200), nullable=True),
        sa.Column("date_utc", sa.DateTime(timezone=True), nullable=True),
        sa.Column("time_utc", sa.Time(), nullable=True),
        sa.Column("time_local", sa.String(10), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default=sa.text("'SCHEDULED'")),
        sa.Column("season", sa.String(10), nullable=True),
        sa.Column("promotion_id", sa.Uuid(), nullable=False),
        sa.Column("venue_id", sa.Uuid(), nullable=True),
        sa.Column("venue_name_inline", sa.String(200), nullable=True),
        sa.Column("city_inline", sa.String(100), nullable=True),
        sa.Column("country_inline", sa.String(100), nullable=True),
        sa.Column("poster_url", sa.Text(), nullable=True),
        sa.Column("square_url", sa.Text(), nullable=True),
        sa.Column("fanart_url", sa.Text(), nullable=True),
        sa.Column("thumbnail_url", sa.Text(), nullable=True),
        sa.Column("banner_url", sa.Text(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("spectators", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.UniqueConstraint("provider", "external_id", name="uq_events_provider_external"),
        sa.ForeignKeyConstraint(["promotion_id"], ["promotions.id"], name="fk_events_promotion"),
        sa.ForeignKeyConstraint(["venue_id"], ["venues.id"], name="fk_events_venue"),
    )

    # ── competitions ───────────────────────────────────────────────────────
    op.create_table(
        "competitions",
        sa.Column("id", sa.Uuid(), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("provider", sa.String(20), nullable=False),
        sa.Column("external_id", sa.String(50), nullable=False),
        sa.Column("event_id", sa.Uuid(), nullable=False),
        sa.Column("order_num", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("card_segment", sa.String(30), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default=sa.text("'SCHEDULED'")),
        sa.Column("is_main_event", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("is_title_fight", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("description", sa.String(50), nullable=True),
        sa.Column("weight_class_id", sa.Uuid(), nullable=True),
        sa.Column("weight_class_name", sa.String(50), nullable=True),
        sa.Column("result_method", sa.String(30), nullable=True),
        sa.Column("result_detail", sa.String(100), nullable=True),
        sa.Column("result_round", sa.Integer(), nullable=True),
        sa.Column("result_time", sa.String(10), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.UniqueConstraint("provider", "external_id", name="uq_competitions_provider_external"),
        sa.ForeignKeyConstraint(["event_id"], ["events.id"], name="fk_competitions_event"),
        sa.ForeignKeyConstraint(["weight_class_id"], ["weight_classes.id"], name="fk_competitions_weight_class"),
    )

    # ── competitors ────────────────────────────────────────────────────────
    op.create_table(
        "competitors",
        sa.Column("id", sa.Uuid(), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("competition_id", sa.Uuid(), nullable=False),
        sa.Column("fighter_id", sa.Uuid(), nullable=False),
        sa.Column("corner", sa.String(10), nullable=False),
        sa.Column("outcome", sa.String(10), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.UniqueConstraint("competition_id", "fighter_id", name="uq_competitors_comp_fighter"),
        sa.ForeignKeyConstraint(["competition_id"], ["competitions.id"], name="fk_competitors_competition"),
        sa.ForeignKeyConstraint(["fighter_id"], ["fighters.id"], name="fk_competitors_fighter"),
    )

    # ── rankings ───────────────────────────────────────────────────────────
    op.create_table(
        "rankings",
        sa.Column("id", sa.Uuid(), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("provider", sa.String(20), nullable=False),
        sa.Column("fighter_id", sa.Uuid(), nullable=False),
        sa.Column("promotion_id", sa.Uuid(), nullable=False),
        sa.Column("category_name", sa.String(100), nullable=False),
        sa.Column("category_type", sa.String(30), nullable=True),
        sa.Column("rank", sa.Integer(), nullable=False),
        sa.Column("trend", sa.String(5), nullable=True),
        sa.Column("is_champion", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("title_defenses", sa.Integer(), nullable=True),
        sa.Column("weight_class_id", sa.Uuid(), nullable=True),
        sa.Column("gender", sa.String(10), nullable=True),
        sa.Column("synced_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["fighter_id"], ["fighters.id"], name="fk_rankings_fighter"),
        sa.ForeignKeyConstraint(["promotion_id"], ["promotions.id"], name="fk_rankings_promotion"),
        sa.ForeignKeyConstraint(["weight_class_id"], ["weight_classes.id"], name="fk_rankings_weight_class"),
    )

    # ── statistics ─────────────────────────────────────────────────────────
    op.create_table(
        "statistics",
        sa.Column("id", sa.Uuid(), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("competitor_id", sa.Uuid(), nullable=False),
        sa.Column("fighter_id", sa.Uuid(), nullable=False),
        sa.Column("category", sa.String(30), nullable=False),
        sa.Column("label", sa.String(100), nullable=False),
        sa.Column("value", sa.Float(), nullable=False),
        sa.Column("display_value", sa.String(20), nullable=True),
        sa.Column("synced_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.UniqueConstraint("competitor_id", "category", "label", name="uq_statistics_comp_cat_label"),
        sa.ForeignKeyConstraint(["competitor_id"], ["competitors.id"], name="fk_statistics_competitor"),
        sa.ForeignKeyConstraint(["fighter_id"], ["fighters.id"], name="fk_statistics_fighter"),
    )

    # ── broadcasts ─────────────────────────────────────────────────────────
    op.create_table(
        "broadcasts",
        sa.Column("id", sa.Uuid(), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("provider", sa.String(20), nullable=False),
        sa.Column("event_id", sa.Uuid(), nullable=False),
        sa.Column("network", sa.String(100), nullable=False),
        sa.Column("region", sa.String(50), nullable=True),
        sa.Column("language", sa.String(10), nullable=True),
        sa.Column("broadcast_type", sa.String(20), nullable=False, server_default=sa.text("'TV'")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.UniqueConstraint("event_id", "network", "region", name="uq_broadcasts_event_network_region"),
        sa.ForeignKeyConstraint(["event_id"], ["events.id"], name="fk_broadcasts_event"),
    )

    # ── external_ids ───────────────────────────────────────────────────────
    op.create_table(
        "external_ids",
        sa.Column("id", sa.Uuid(), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("entity_type", sa.String(30), nullable=False),
        sa.Column("entity_id", sa.Uuid(), nullable=False),
        sa.Column("provider", sa.String(20), nullable=False),
        sa.Column("external_id", sa.String(50), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.UniqueConstraint("entity_type", "entity_id", "provider", name="uq_external_ids_entity_provider"),
    )

    # ── sync_runs ──────────────────────────────────────────────────────────
    op.create_table(
        "sync_runs",
        sa.Column("id", sa.Uuid(), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("status", sa.String(20), nullable=False, server_default=sa.text("'RUNNING'")),
        sa.Column("mode", sa.String(20), nullable=False),
        sa.Column("provider", sa.String(20), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )

    # ── sync_jobs ──────────────────────────────────────────────────────────
    op.create_table(
        "sync_jobs",
        sa.Column("id", sa.Uuid(), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("sync_run_id", sa.Uuid(), nullable=False),
        sa.Column("entity_type", sa.String(30), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default=sa.text("'PENDING'")),
        sa.Column("records_inserted", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("records_updated", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("records_skipped", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("records_errors", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("api_calls", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("duration_ms", sa.Float(), nullable=False, server_default=sa.text("0")),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["sync_run_id"], ["sync_runs.id"], name="fk_sync_jobs_run"),
    )

    # ── dead_letters ───────────────────────────────────────────────────────
    op.create_table(
        "dead_letters",
        sa.Column("id", sa.Uuid(), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("entity_type", sa.String(30), nullable=False),
        sa.Column("provider", sa.String(20), nullable=False),
        sa.Column("external_id", sa.String(50), nullable=True),
        sa.Column("payload", sa.JSON(), nullable=True),
        sa.Column("error", sa.Text(), nullable=False),
        sa.Column("error_category", sa.String(30), nullable=False),
        sa.Column("replayed", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("replayed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )

    # ── indexes ──────────────────────────────────────────────────────────
    op.create_index("ix_sync_runs_status", "sync_runs", ["status"])
    op.create_index("ix_sync_jobs_sync_run_id", "sync_jobs", ["sync_run_id"])
    op.create_index("ix_sync_jobs_entity_type", "sync_jobs", ["entity_type"])
    op.create_index("ix_dead_letters_entity_type", "dead_letters", ["entity_type"])
    op.create_index("ix_dead_letters_replayed", "dead_letters", ["replayed"])
    op.create_index("ix_external_ids_entity_type_provider", "external_ids", ["entity_type", "provider", "external_id"])
    op.create_index("ix_events_date", "events", ["date_utc"])
    op.create_index("ix_events_status", "events", ["status"])
    op.create_index("ix_fighters_is_active", "fighters", ["is_active"])
    op.create_index("ix_rankings_category", "rankings", ["promotion_id", "category_name"])


def downgrade() -> None:
    op.drop_table("dead_letters")
    op.drop_table("sync_jobs")
    op.drop_table("sync_runs")
    op.drop_table("external_ids")
    op.drop_table("broadcasts")
    op.drop_table("statistics")
    op.drop_table("rankings")
    op.drop_table("competitors")
    op.drop_table("competitions")
    op.drop_table("events")
    op.drop_table("fighters")
    op.drop_table("venues")
    op.drop_table("weight_classes")
    op.drop_table("promotions")
