"""Migration coverage — every ORM table has a migration; verified drift-fixes hold.

Covers the Phase 1 schema work:
1. Every model registered on Base.metadata maps to a CREATE TABLE in the alembic chain.
2. No duplicate ADD COLUMN synced_at on rankings (002 loop excludes rankings; 001 owns it).
3. Auth tables (004) exist.
4. Column-type fixes (005) hold: promotions.first_event_date String(20),
   events.time_utc String(10), sync_runs/sync_jobs.duration_ms Float.
5. Full model metadata create_all smoke test on SQLite (models are coherent).
"""

import re
from pathlib import Path

from sqlalchemy import inspect as sa_inspect

VERSIONS_DIR = Path(__file__).resolve().parents[2] / "alembic" / "versions"


def _read_migrations() -> str:
    return "\n".join(
        p.read_text(encoding="utf-8")
        for p in sorted(VERSIONS_DIR.glob("*.py"))
        if re.match(r"^\d{3}_", p.name)
    )


def _migration_created_tables() -> set[str]:
    sql = _read_migrations()
    return set(re.findall(r'op\.create_table\(\s*"([a-z_]+)"', sql))


class TestTableCoverage:
    def test_every_model_table_has_a_migration(self):
        from src.db import models  # noqa: F401  — registers all models on Base
        from src.db.base import Base

        model_tables = set(Base.metadata.tables.keys())
        migration_tables = _migration_created_tables()

        missing = sorted(model_tables - migration_tables)
        assert missing == [], f"Tables with no migration: {missing}"

    def test_auth_tables_are_migrated(self):
        tables = _migration_created_tables()
        for t in ["users", "user_sessions", "user_preferences",
                  "favorite_fighters", "favorite_events", "watchlist_events",
                  "notifications", "devices"]:
            assert t in tables, f"Auth table {t} missing from migrations"

    def test_support_tables_are_migrated(self):
        tables = _migration_created_tables()
        for t in ["fighter_records", "provider_conflicts", "provider_payloads",
                  "sync_checkpoints", "fighter_provider_record_status"]:
            assert t in tables, f"Support table {t} missing from migrations"


class TestDuplicateColumnConflict:
    def test_rankings_synced_at_created_once(self):
        sql = _read_migrations()
        adds = re.findall(r'op\.add_column\("rankings",\s*sa\.Column\("synced_at"', sql)
        assert adds == [], (
            "002 must NOT re-add rankings.synced_at — 001 already creates it "
            "(DuplicateColumnError on fresh DB)"
        )
        # Rankings still get their SyncableMixin columns (from 005)
        assert 'op.add_column(\n        "rankings",\n        sa.Column("source_provider"' in sql
        assert 'op.add_column(\n        "rankings",\n        sa.Column("version"' in sql

    def test_syncable_loop_excludes_rankings(self):
        sql = _read_migrations()
        m = re.search(r'for table in \[([^\]]*)\]', sql, re.DOTALL)
        assert m is not None
        tables = re.findall(r'"([a-z_]+)"', m.group(1))
        assert "rankings" not in tables


class TestTypeFixes:
    def test_sync_runs_duration_ms_is_float(self):
        sql = _read_migrations()
        assert 'sa.Column("duration_ms", sa.Float()' in sql

    def test_first_event_date_and_time_utc_aligned_to_models(self):
        sql = _read_migrations()
        assert 'existing_type=sa.Date(), type_=sa.String(20)' in sql
        assert 'existing_type=sa.Time(), type_=sa.String(10)' in sql

    def test_model_duration_ms_is_float(self):
        from src.db.models.support import SyncJob, SyncRun

        assert isinstance(SyncRun.__table__.c.duration_ms.type, __import__("sqlalchemy").Float)
        assert isinstance(SyncJob.__table__.c.duration_ms.type, __import__("sqlalchemy").Float)


class TestModelCoherence:
    async def test_create_all_smoke_on_sqlite(self):
        """create_all must succeed — proves model metadata is internally coherent."""
        from sqlalchemy.ext.asyncio import create_async_engine

        from src.db import models  # noqa: F401
        from src.db.base import Base

        engine = create_async_engine("sqlite+aiosqlite:///:memory:")
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        async with engine.connect() as conn:
            tables = await conn.run_sync(lambda sync_conn: sa_inspect(sync_conn).get_table_names())
        await engine.dispose()

        assert len(tables) >= 26, f"Expected >=26 tables, got {len(tables)}"
        for t in ["users", "rankings", "statistics", "broadcasts", "competitors",
                  "external_ids", "sync_runs", "sync_jobs", "dead_letters"]:
            assert t in tables, f"Missing table in create_all: {t}"
