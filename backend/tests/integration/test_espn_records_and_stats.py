"""Integration tests — fighter records + career statistics persistence.

Validates the frozen-research GAP fixes:
- Records: /athletes/{id}/records flows into the fighter_records table; an
  empty/unavailable records response NEVER resets stored values.
- is_active: presence-guarded — only a real bool from ESPN changes the flag.
- Career statistics persist keyed by (fighter_id, category, label) with NULL
  competitor_id (migration 006 shape).
- The discovery-driven fighter job resolves IDs + attaches records.
"""

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine


@pytest.fixture
async def db_session():
    """In-memory SQLite session (same pattern as existing integration tests)."""
    engine = create_async_engine("sqlite+aiosqlite://", echo=False)
    async with engine.begin() as conn:
        import src.db.models
        import src.db.models.support  # noqa: F401
        from src.db.base import Base

        await conn.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, class_=AsyncSession)
    async with factory() as session:
        yield session
    await engine.dispose()


async def _make_fighter(db, external_id: str, first: str, last: str) -> str:
    """Insert a fighter + external_id mapping, return the UUID string."""
    from uuid import uuid4

    from src.db.models.fighter import Fighter
    from src.db.models.support import ExternalId

    fid = str(uuid4())
    db.add(
        Fighter(
            id=fid,
            provider="espn",
            external_id=external_id,
            first_name=first,
            last_name=last,
            full_name=f"{first} {last}",
        )
    )
    db.add(
        ExternalId(
            provider="espn",
            external_id=external_id,
            entity_type="fighter",
            entity_id=fid,
        )
    )
    await db.flush()
    return fid


def _record_dto(external_id: str, wins: int = 21, losses: int = 5) -> dict:
    from src.providers.dto import FighterDTO

    return FighterDTO(
        provider="espn",
        external_id=external_id,
        first_name="Islam",
        last_name="Makhachev",
        record_wins=wins,
        record_losses=losses,
        record_draws=0,
        record_no_contests=0,
        record_summary=f"{wins}-{losses}-0",
        ko_tko_wins=9,
        ko_tko_losses=1,
        submission_wins=1,
        submission_losses=1,
        title_wins=7,
        title_losses=2,
        title_draws=0,
        total_fights=wins + losses,
        win_percentage=round(wins / (wins + losses), 4),
        finish_rate=round(10 / 21, 4),
    )


class TestFighterRecordsPersistence:
    @pytest.mark.asyncio
    async def test_record_upserted_into_fighter_records(self, db_session):
        from src.db.models.fighter import FighterRecord
        from src.sync.upserts.fighter import FighterUpsert
        from src.sync.upserts.id_resolver import IdResolver

        fid = await _make_fighter(db_session, "3088812", "Islam", "Makhachev")
        dto = _record_dto("3088812")

        upsert = FighterUpsert(IdResolver(db_session))
        result = await upsert.upsert_batch([dto])
        await db_session.flush()

        assert result.inserted >= 1  # fighter row
        row = (
            await db_session.execute(
                select(FighterRecord).where(FighterRecord.fighter_id == fid)
            )
        ).scalar_one_or_none()
        assert row is not None
        assert row.record_summary == "21-5-0"
        assert row.ko_tko_wins == 9
        assert row.submission_wins == 1
        assert row.title_wins == 7
        assert row.finish_rate == round(10 / 21, 4)

    @pytest.mark.asyncio
    async def test_record_idempotent_no_duplicate(self, db_session):
        from src.db.models.fighter import FighterRecord
        from src.sync.upserts.fighter import FighterUpsert
        from src.sync.upserts.id_resolver import IdResolver

        await _make_fighter(db_session, "3088812", "Islam", "Makhachev")
        dto = _record_dto("3088812")

        upsert = FighterUpsert(IdResolver(db_session))
        await upsert.upsert_batch([dto])
        await db_session.flush()
        await upsert.upsert_batch([dto])
        await db_session.flush()

        rows = (
            await db_session.execute(select(FighterRecord))
        ).scalars().all()
        assert len(rows) == 1

    @pytest.mark.asyncio
    async def test_missing_record_never_resets_stored_values(self, db_session):
        from src.db.models.fighter import FighterRecord
        from src.providers.dto import FighterDTO
        from src.sync.upserts.fighter import FighterUpsert
        from src.sync.upserts.id_resolver import IdResolver

        await _make_fighter(db_session, "3088812", "Islam", "Makhachev")

        # First: real record persists
        upsert = FighterUpsert(IdResolver(db_session))
        await upsert.upsert_batch([_record_dto("3088812")])
        await db_session.flush()

        # Second: records unavailable → DTO has no breakdown fields (all None)
        no_record = FighterDTO(
            provider="espn",
            external_id="3088812",
            first_name="Islam",
            last_name="Makhachev",
            record_wins=0,
            record_losses=0,
            record_draws=0,
            record_no_contests=0,
        )
        await upsert.upsert_batch([no_record])
        await db_session.flush()

        row = (
            await db_session.execute(select(FighterRecord))
        ).scalar_one_or_none()
        assert row is not None
        # Stored values preserved — NOT reset to 0-0-0-0
        assert row.record_summary == "21-5-0"
        assert row.wins == 21
        assert row.ko_tko_wins == 9


class TestIsActivePersistence:
    @pytest.mark.asyncio
    async def test_is_active_updated_when_present(self, db_session):
        from src.db.models.fighter import Fighter
        from src.providers.dto import FighterDTO
        from src.sync.upserts.fighter import FighterUpsert
        from src.sync.upserts.id_resolver import IdResolver

        await _make_fighter(db_session, "2354359", "Jason", "Reinhardt")

        inactive = FighterDTO(
            provider="espn",
            external_id="2354359",
            first_name="Jason",
            last_name="Reinhardt",
            is_active=False,
        )
        upsert = FighterUpsert(IdResolver(db_session))
        await upsert.upsert_batch([inactive])
        await db_session.flush()

        fighter = (
            await db_session.execute(
                select(Fighter).where(Fighter.external_id == "2354359")
            )
        ).scalar_one()
        assert fighter.is_active is False

    @pytest.mark.asyncio
    async def test_is_active_none_does_not_overwrite(self, db_session):
        from src.db.models.fighter import Fighter
        from src.providers.dto import FighterDTO
        from src.sync.upserts.fighter import FighterUpsert
        from src.sync.upserts.id_resolver import IdResolver

        await _make_fighter(db_session, "3088812", "Islam", "Makhachev")
        active = FighterDTO(
            provider="espn",
            external_id="3088812",
            first_name="Islam",
            last_name="Makhachev",
            is_active=True,
        )
        upsert = FighterUpsert(IdResolver(db_session))
        await upsert.upsert_batch([active])
        await db_session.flush()

        # Payload without `active` → is_active=None → must NOT flip the flag
        unknown = FighterDTO(
            provider="espn",
            external_id="3088812",
            first_name="Islam",
            last_name="Makhachev",
            is_active=None,
        )
        await upsert.upsert_batch([unknown])
        await db_session.flush()

        fighter = (
            await db_session.execute(
                select(Fighter).where(Fighter.external_id == "3088812")
            )
        ).scalar_one()
        assert fighter.is_active is True


class TestCareerStatisticsPersistence:
    @pytest.mark.asyncio
    async def test_career_stats_persist_with_null_competitor(self, db_session):
        from src.db.models.core import Statistic
        from src.providers.dto import StatisticDTO
        from src.sync.upserts.id_resolver import IdResolver
        from src.sync.upserts.statistics import StatisticsUpsert

        fid = await _make_fighter(db_session, "3088812", "Islam", "Makhachev")

        dtos = [
            StatisticDTO(
                fighter_external_id="3088812",
                competition_external_id="",  # career shape
                category="Striking",
                label="Sig. Strikes Landed/Min",
                value=4.2,
                display_value="4.2",
            ),
            StatisticDTO(
                fighter_external_id="3088812",
                competition_external_id="",
                category="Grappling",
                label="Takedown Accuracy",
                value=58.0,
                display_value="58%",
            ),
        ]

        upsert = StatisticsUpsert(IdResolver(db_session))
        result = await upsert.upsert_batch(dtos)
        await db_session.flush()

        assert result.inserted == 2
        rows = (await db_session.execute(select(Statistic))).scalars().all()
        assert len(rows) == 2
        for row in rows:
            assert row.fighter_id == fid
            assert row.competitor_id is None  # career — NULL competitor

    @pytest.mark.asyncio
    async def test_career_stats_idempotent(self, db_session):
        from src.db.models.core import Statistic
        from src.providers.dto import StatisticDTO
        from src.sync.upserts.id_resolver import IdResolver
        from src.sync.upserts.statistics import StatisticsUpsert

        await _make_fighter(db_session, "3088812", "Islam", "Makhachev")
        dto = StatisticDTO(
            fighter_external_id="3088812",
            competition_external_id="",
            category="Striking",
            label="Sig. Strikes Landed/Min",
            value=4.2,
            display_value="4.2",
        )

        upsert = StatisticsUpsert(IdResolver(db_session))
        await upsert.upsert_batch([dto])
        await db_session.flush()
        await upsert.upsert_batch([dto])
        await db_session.flush()

        rows = (await db_session.execute(select(Statistic))).scalars().all()
        assert len(rows) == 1

    @pytest.mark.asyncio
    async def test_career_stats_update_value(self, db_session):
        from src.db.models.core import Statistic
        from src.providers.dto import StatisticDTO
        from src.sync.upserts.id_resolver import IdResolver
        from src.sync.upserts.statistics import StatisticsUpsert

        await _make_fighter(db_session, "3088812", "Islam", "Makhachev")
        upsert = StatisticsUpsert(IdResolver(db_session))

        dto = StatisticDTO(
            fighter_external_id="3088812",
            competition_external_id="",
            category="Striking",
            label="Sig. Strikes Landed/Min",
            value=4.2,
            display_value="4.2",
        )
        await upsert.upsert_batch([dto])
        await db_session.flush()

        dto.value = 5.1
        dto.display_value = "5.1"
        result = await upsert.upsert_batch([dto])
        await db_session.flush()

        assert result.updated == 1
        row = (
            await db_session.execute(
                select(Statistic).where(Statistic.label == "Sig. Strikes Landed/Min")
            )
        ).scalar_one()
        assert row.value == 5.1


class TestDiscoveryFighterJob:
    @pytest.mark.asyncio
    async def test_job_resolves_ids_and_attaches_records(self, db_session):
        """Discovery job: fake provider returns IDs; records attach to DTOs."""
        from src.providers.espn.jobs.fighter import ESPN_FighterSyncJob
        from src.sync.context import SyncContext
        from src.sync.state import SyncState
        from src.sync.types import EntityType

        class FakeProvider:
            class _Cfg:
                max_concurrency = 2

            _config = _Cfg()

            async def fetch_athlete_ids(self):
                return {"3088812", "2354359"}

            async def fetch_fighters_by_ids(self, athlete_ids):
                from src.providers.dto import FighterDTO

                return [
                    FighterDTO(
                        provider="espn",
                        external_id="3088812",
                        first_name="Islam",
                        last_name="Makhachev",
                    ),
                    FighterDTO(
                        provider="espn",
                        external_id="2354359",
                        first_name="Jason",
                        last_name="Reinhardt",
                    ),
                ]

            async def fetch_fighter_record(self, external_id):
                from src.providers.espn.parsers.records import FighterRecord

                if external_id == "3088812":
                    return FighterRecord(
                        wins=21,
                        losses=5,
                        record_summary="21-5-0",
                        ko_tko_wins=9,
                        total_fights=26,
                        finish_rate=round(10 / 21, 4),
                    )
                return None  # unavailable → no record

        provider = FakeProvider()
        job = ESPN_FighterSyncJob()
        state = SyncState.for_entity(EntityType.FIGHTER, "espn")

        from src.sync.clock import SystemClock

        ctx = SyncContext(provider=provider, db=db_session, clock=SystemClock())
        dtos = await job._fetch(ctx, state)

        assert len(dtos) == 2
        # Checkpoint cached for resumability
        assert state.checkpoint.get("athlete_ids") == ["2354359", "3088812"]

        by_id = {d.external_id: d for d in dtos}
        # Records attached for the fighter with a real record
        assert by_id["3088812"].record_summary == "21-5-0"
        assert by_id["3088812"].record_wins == 21
        assert by_id["3088812"].ko_tko_wins == 9
        # Unavailable records → None fields (never fabricate / never reset)
        assert by_id["2354359"].record_summary is None

    @pytest.mark.asyncio
    async def test_job_window_respects_sync_limit(self, db_session, monkeypatch):
        from src.providers.espn.jobs.fighter import ESPN_FighterSyncJob
        from src.sync.context import SyncContext
        from src.sync.state import SyncState
        from src.sync.types import EntityType

        monkeypatch.setenv("ESPN_FIGHTER_SYNC_LIMIT", "1")

        class FakeProvider:
            _config = type("_Cfg", (), {"max_concurrency": 2})()

            async def fetch_athlete_ids(self):
                return {"1", "2", "3"}

            async def fetch_fighters_by_ids(self, athlete_ids):
                from src.providers.dto import FighterDTO

                return [
                    FighterDTO(
                        provider="espn",
                        external_id=a,
                        first_name="F",
                        last_name=a,
                    )
                    for a in athlete_ids
                ]

            async def fetch_fighter_record(self, external_id):
                return None

        job = ESPN_FighterSyncJob()
        state = SyncState.for_entity(EntityType.FIGHTER, "espn")
        ctx = SyncContext(provider=FakeProvider(), db=db_session)
        dtos = await job._fetch(ctx, state)
        assert len(dtos) == 1  # bounded window
