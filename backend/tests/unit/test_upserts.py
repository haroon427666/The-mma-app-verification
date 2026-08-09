"""BaseUpsert identity tests — T01 (provider/external_id NOT NULL)."""

from unittest.mock import AsyncMock

import pytest
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine


@pytest.fixture
async def db_session():
    """In-memory SQLite session for test isolation."""
    engine = create_async_engine("sqlite+aiosqlite://", echo=False)
    async with engine.begin() as conn:
        import src.db.models
        import src.db.models.auth
        import src.db.models.support  # noqa: F401
        from src.db.base import Base
        await conn.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, class_=AsyncSession)
    async with factory() as session:
        yield session
    await engine.dispose()


def make_fighter_dto(
    external_id: str,
    first_name: str,
    last_name: str,
    record_wins: int = 27,
    weight_class_external_id: str | None = None,
    weight_class_name: str | None = None,
):
    from src.providers.dto import FighterDTO

    return FighterDTO(
        provider="espn",
        external_id=external_id,
        first_name=first_name,
        last_name=last_name,
        record_wins=record_wins,
        weight_class_external_id=weight_class_external_id,
        weight_class_name=weight_class_name,
    )


async def count_fighters(db: AsyncSession) -> int:
    from src.db.models.fighter import Fighter

    result = await db.execute(select(func.count()).select_from(Fighter))
    return int(result.scalar_one())


class TestInsertIdentity:
    @pytest.mark.asyncio
    async def test_insert_sets_provider_and_external_id(self, db_session):
        """A new entity insert must carry NOT NULL provider/external_id."""
        from src.db.models.fighter import Fighter
        from src.db.models.support import ExternalId
        from src.sync.upserts.fighter import FighterUpsert
        from src.sync.upserts.id_resolver import IdResolver

        upsert = FighterUpsert(IdResolver(db_session))
        result = await upsert.upsert_batch([make_fighter_dto("3088812", "Islam", "Makhachev")])
        await db_session.commit()

        assert result.inserted == 1
        assert result.errors == 0

        fighter = (
            await db_session.execute(
                select(Fighter).where(Fighter.external_id == "3088812")
            )
        ).scalar_one()
        assert fighter.provider == "espn"
        assert fighter.external_id == "3088812"

        mapping = (
            await db_session.execute(
                select(ExternalId).where(ExternalId.external_id == "3088812")
            )
        ).scalar_one()
        assert mapping.provider == "espn"
        assert mapping.entity_type == "fighter"
        assert mapping.entity_id == str(fighter.id)

    @pytest.mark.asyncio
    async def test_insert_via_race_retry_sets_identity(self, db_session):
        """The single-row race-retry insert path sets identity too."""
        from src.db.models.fighter import Fighter
        from src.sync.upserts.fighter import FighterUpsert
        from src.sync.upserts.id_resolver import IdResolver

        upsert = FighterUpsert(IdResolver(db_session))
        dto = make_fighter_dto("3320416", "Alex", "Pereira", record_wins=12)
        result = await upsert._insert_with_race_retry("3320416", dto)
        await db_session.commit()

        assert result.inserted == 1
        fighter = (
            await db_session.execute(
                select(Fighter).where(Fighter.external_id == "3320416")
            )
        ).scalar_one()
        assert fighter.provider == "espn"
        assert fighter.external_id == "3320416"


class TestReUpsert:
    @pytest.mark.asyncio
    async def test_reupsert_updates_not_duplicates(self, db_session):
        """Second upsert with changed fields updates, keeps identity."""
        from src.db.models.fighter import Fighter
        from src.sync.upserts.fighter import FighterUpsert
        from src.sync.upserts.id_resolver import IdResolver

        upsert = FighterUpsert(IdResolver(db_session))
        await upsert.upsert_batch([make_fighter_dto("3088812", "Islam", "Makhachev")])
        await db_session.commit()

        result = await upsert.upsert_batch(
            [make_fighter_dto("3088812", "Islam", "Makhachev", record_wins=28)]
        )
        await db_session.commit()

        assert result.inserted == 0
        assert result.updated == 1
        assert await count_fighters(db_session) == 1
        fighter = (
            await db_session.execute(
                select(Fighter).where(Fighter.external_id == "3088812")
            )
        ).scalar_one()
        assert fighter.provider == "espn"
        assert fighter.external_id == "3088812"
        assert fighter.record_wins == 28

    @pytest.mark.asyncio
    async def test_reupsert_unchanged_skips(self, db_session):
        """Identical second upsert is a no-op."""
        from src.sync.upserts.fighter import FighterUpsert
        from src.sync.upserts.id_resolver import IdResolver

        upsert = FighterUpsert(IdResolver(db_session))
        dto = make_fighter_dto("3088812", "Islam", "Makhachev")
        await upsert.upsert_batch([dto])
        await db_session.commit()

        result = await upsert.upsert_batch([dto])
        await db_session.commit()

        assert result.inserted == 0
        assert result.updated == 0
        assert result.skipped == 1
        assert await count_fighters(db_session) == 1


class TestRaceRetry:
    @pytest.mark.asyncio
    async def test_race_retry_recovers_and_preserves_identity(self, db_session):
        """Concurrent-write conflict → re-resolve → update, identity intact."""
        from src.db.models.fighter import Fighter
        from src.sync.upserts.fighter import FighterUpsert
        from src.sync.upserts.id_resolver import IdResolver

        upsert = FighterUpsert(IdResolver(db_session))
        await upsert.upsert_batch([make_fighter_dto("3088812", "Islam", "Makhachev")])
        await db_session.commit()

        original_flush = db_session.flush
        db_session.flush = AsyncMock(
            side_effect=[
                IntegrityError("INSERT", {}, Exception("simulated duplicate")),
                None,
            ]
        )
        try:
            result = await upsert._insert_with_race_retry(
                "3088812", make_fighter_dto("3088812", "Islam", "Makhachev", record_wins=29)
            )
        finally:
            db_session.flush = original_flush
        await db_session.commit()

        assert result.inserted == 0
        assert result.updated == 1
        assert await count_fighters(db_session) == 1
        fighter = (
            await db_session.execute(
                select(Fighter).where(Fighter.external_id == "3088812")
            )
        ).scalar_one()
        assert fighter.provider == "espn"
        assert fighter.external_id == "3088812"
        assert fighter.record_wins == 29


class TestPrepareNew:
    @pytest.mark.asyncio
    async def test_does_not_clobber_subclass_values(self, db_session):
        """Values a subclass already set in _to_model are preserved."""
        from src.db.models.fighter import Fighter
        from src.sync.upserts.fighter import FighterUpsert
        from src.sync.upserts.id_resolver import IdResolver

        upsert = FighterUpsert(IdResolver(db_session))
        model = Fighter(
            provider="custom",
            external_id="pre-set",
            first_name="a",
            last_name="b",
        )
        upsert._prepare_new(model, "extracted")
        assert model.provider == "custom"
        assert model.external_id == "pre-set"

    @pytest.mark.asyncio
    async def test_fills_missing_values(self, db_session):
        """Missing values are filled from the upsert provider + extracted ID."""
        from src.db.models.fighter import Fighter
        from src.sync.upserts.fighter import FighterUpsert
        from src.sync.upserts.id_resolver import IdResolver

        upsert = FighterUpsert(IdResolver(db_session))
        model = Fighter(first_name="a", last_name="b")
        upsert._prepare_new(model, "3088812")
        assert model.provider == "espn"
        assert model.external_id == "3088812"


class TestFkEnrichment:
    """T03 — NOT NULL FK fields (events.promotion_id, competitions.event_id)
    must be resolved from DTO external references before insert."""

    @pytest.mark.asyncio
    async def test_event_insert_resolves_promotion(self, db_session):
        """An event DTO's promotion_external_id maps to promotions.id."""
        from src.db.models.event import Event
        from src.providers.dto import EventDTO, PromotionDTO
        from src.sync.upserts.event import EventUpsert
        from src.sync.upserts.id_resolver import IdResolver
        from src.sync.upserts.promotion import PromotionUpsert

        session = db_session
        resolver = IdResolver(session)
        await PromotionUpsert(resolver).upsert_batch(
            [PromotionDTO(provider="espn", external_id="ufc", name="UFC", slug="ufc")]
        )
        await session.commit()

        upsert = EventUpsert(IdResolver(session))
        result = await upsert.upsert_batch(
            [EventDTO(provider="espn", external_id="1234", name="UFC 300", promotion_external_id="ufc")]
        )
        await session.commit()

        assert result.inserted == 1
        assert result.errors == 0
        event = (
            await session.execute(
                select(Event).where(Event.external_id == "1234")
            )
        ).scalar_one()
        assert event.promotion_id is not None

    @pytest.mark.asyncio
    async def test_event_with_missing_promotion_is_skipped(self, db_session):
        """A DTO referencing an unsynced promotion must not insert (NOT NULL)."""
        from src.db.models.event import Event
        from src.providers.dto import EventDTO
        from src.sync.upserts.event import EventUpsert
        from src.sync.upserts.id_resolver import IdResolver

        upsert = EventUpsert(IdResolver(db_session))
        result = await upsert.upsert_batch(
            [EventDTO(provider="espn", external_id="1234", name="UFC 300", promotion_external_id="ufc")]
        )
        await db_session.commit()

        assert result.inserted == 0
        assert result.errors == 1
        assert await count_fighters(db_session) == 0
        event = (
            await db_session.execute(select(Event).where(Event.external_id == "1234"))
        ).scalar_one_or_none()
        assert event is None

    @pytest.mark.asyncio
    async def test_competition_insert_resolves_event(self, db_session):
        """A competition DTO's event_external_id maps to events.id."""
        from src.db.models.event import Competition, Event
        from src.providers.dto import CompetitionDTO, EventDTO, PromotionDTO
        from src.sync.upserts.competition import CompetitionUpsert
        from src.sync.upserts.event import EventUpsert
        from src.sync.upserts.id_resolver import IdResolver
        from src.sync.upserts.promotion import PromotionUpsert

        session = db_session
        await PromotionUpsert(IdResolver(session)).upsert_batch(
            [PromotionDTO(provider="espn", external_id="ufc", name="UFC", slug="ufc")]
        )
        await EventUpsert(IdResolver(session)).upsert_batch(
            [EventDTO(provider="espn", external_id="1234", name="UFC 300", promotion_external_id="ufc")]
        )
        await session.commit()

        upsert = CompetitionUpsert(IdResolver(session))
        result = await upsert.upsert_batch(
            [CompetitionDTO(provider="espn", external_id="c1", event_external_id="1234")]
        )
        await session.commit()

        assert result.inserted == 1
        assert result.errors == 0
        comp = (
            await session.execute(select(Competition).where(Competition.external_id == "c1"))
        ).scalar_one()
        event = (
            await session.execute(select(Event).where(Event.external_id == "1234"))
        ).scalar_one()
        assert comp.event_id == event.id

    @pytest.mark.asyncio
    async def test_fighter_insert_resolves_weight_class(self, db_session):
        """A fighter DTO's weight_class_external_id maps to weight_classes.id."""
        from src.db.models.fighter import Fighter
        from src.providers.dto import WeightClassDTO
        from src.sync.upserts.fighter import FighterUpsert
        from src.sync.upserts.id_resolver import IdResolver
        from src.sync.upserts.weight_class import WeightClassUpsert

        session = db_session
        await WeightClassUpsert(IdResolver(session)).upsert_batch(
            [WeightClassDTO(provider="espn", external_id="970", name="Bantamweight", abbreviation="BW")]
        )
        await session.commit()

        dto = make_fighter_dto("3088812", "Islam", "Makhachev")
        dto.weight_class_external_id = "970"
        upsert = FighterUpsert(IdResolver(session))
        result = await upsert.upsert_batch([dto])
        await session.commit()

        assert result.inserted == 1
        fighter = (
            await session.execute(select(Fighter).where(Fighter.external_id == "3088812"))
        ).scalar_one()
        assert fighter.weight_class_id is not None


class TestWeightClassLazyCreation:
    """T13 — inline weight-class data must materialize rows on first use."""

    @pytest.mark.asyncio
    async def test_fighter_creates_missing_weight_class(self, db_session):
        from src.db.models.core import WeightClass
        from src.db.models.fighter import Fighter
        from src.sync.upserts.fighter import FighterUpsert
        from src.sync.upserts.id_resolver import IdResolver

        upsert = FighterUpsert(IdResolver(db_session))
        result = await upsert.upsert_batch([
            make_fighter_dto("3088812", "Islam", "Makhachev",
                             weight_class_external_id="970",
                             weight_class_name="Lightweight"),
        ])
        await db_session.commit()

        assert result.inserted == 1
        assert result.errors == 0

        wc = (
            await db_session.execute(
                select(WeightClass).where(WeightClass.external_id == "970")
            )
        ).scalar_one()
        assert wc.provider == "espn"
        assert wc.name == "Lightweight"

        fighter = (
            await db_session.execute(
                select(Fighter).where(Fighter.external_id == "3088812")
            )
        ).scalar_one()
        assert fighter.weight_class_id == wc.id
        assert fighter.weight_class_name == "Lightweight"

    @pytest.mark.asyncio
    async def test_second_fighter_reuses_existing_row(self, db_session):
        from src.db.models.core import WeightClass
        from src.db.models.fighter import Fighter
        from src.sync.upserts.fighter import FighterUpsert
        from src.sync.upserts.id_resolver import IdResolver

        upsert = FighterUpsert(IdResolver(db_session))
        await upsert.upsert_batch([
            make_fighter_dto("3088812", "Islam", "Makhachev",
                             weight_class_external_id="970",
                             weight_class_name="Lightweight"),
        ])
        await db_session.commit()

        upsert2 = FighterUpsert(IdResolver(db_session))
        result = await upsert2.upsert_batch([
            make_fighter_dto("3088813", "Charles", "Oliveira",
                             weight_class_external_id="970",
                             weight_class_name="Lightweight"),
        ])
        await db_session.commit()

        assert result.inserted == 1
        count = (
            await db_session.execute(select(func.count()).select_from(WeightClass))
        ).scalar_one()
        assert count == 1  # no duplicate row for the same division

        fighter2 = (
            await db_session.execute(
                select(Fighter).where(Fighter.external_id == "3088813")
            )
        ).scalar_one()
        assert fighter2.weight_class_id is not None

    @pytest.mark.asyncio
    async def test_fighter_without_weight_class_skips_creation(self, db_session):
        from src.db.models.core import WeightClass
        from src.sync.upserts.fighter import FighterUpsert
        from src.sync.upserts.id_resolver import IdResolver

        upsert = FighterUpsert(IdResolver(db_session))
        result = await upsert.upsert_batch([
            make_fighter_dto("999", "No", "Division"),
        ])
        await db_session.commit()

        assert result.inserted == 1
        count = (
            await db_session.execute(select(func.count()).select_from(WeightClass))
        ).scalar_one()
        assert count == 0
