"""Fighter next-fight route — T14 (FTR-107).

`GET /v1/fighters/{id}/next-fight` — earliest bout on an event that has not
finished and is not cancelled, ordered by event date (nulls last), then card
order. Past-dated SCHEDULED events are excluded. Unknown fighter → 404;
fighter with no upcoming bout → `null`.
"""

from datetime import UTC, datetime

import pytest
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from tests.api.test_uuid_guards import BAD_ID, make_request, make_uow

FIGHTER_ID = "550e8400-e29b-41d4-a716-446655440000"
OPPONENT_ID = "6f9619ff-8b86-d011-b42d-00c04fc964ff"
EVENT_UPCOMING = "8d2a6f30-4f2e-4b7a-9c3e-1a2b3c4d5e6f"
EVENT_LATER = "c8f0d7e6-b5a4-4c3b-a291-8f7e6d5c4b3a"
EVENT_FINAL = "deadbeef-dead-4eed-a11e-deadbeeff00d"
EVENT_PAST = "01234567-89ab-4cde-9f01-23456789abcd"
COMP1_ID = "a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d"
COMP2_ID = "b2c3d4e5-f6a7-4b8c-9d0e-1f2a3b4c5d6e"
COMP3_ID = "c3d4e5f6-a7b8-4c9d-8e0f-1a2b3c4d5e6f"
COMP4_ID = "d4e5f6a7-b8c9-4d0e-8f1a-2b3c4d5e6f7a"


@pytest.fixture
async def db_session():
    engine = create_async_engine("sqlite+aiosqlite://", echo=False)
    async with engine.begin() as conn:
        import src.db.models  # noqa: F401  (registers models on Base.metadata)
        from src.db.base import Base
        await conn.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, class_=AsyncSession)
    async with factory() as session:
        yield session
    await engine.dispose()


def _now() -> datetime:
    return datetime.now(UTC)


def _days_from_now(days: int) -> datetime:
    """Relative date so tests stay green regardless of when they run."""
    from datetime import timedelta

    return _now() + timedelta(days=days)


async def seed_fighter(session: AsyncSession, fighter_id: str = FIGHTER_ID,
                       opponent_id: str = OPPONENT_ID):
    from src.db.models import Fighter, Promotion

    session.add(Promotion(id="f0f1f2f3-f4f5-4f6f-8f7f-6f5f4f3f2f1f",
                          provider="espn", external_id="ufc", name="UFC"))
    session.add(Fighter(id=fighter_id, provider="espn", external_id="1",
                        first_name="Islam", last_name="Makhachev"))
    session.add(Fighter(id=opponent_id, provider="espn", external_id="2",
                        first_name="Arman", last_name="Tsarukyan"))
    await session.commit()


async def add_event(session: AsyncSession, event_id: str, name: str, status: str,
                    date_utc: datetime | None):
    from src.db.models.event import Event

    session.add(Event(id=event_id, provider="espn", external_id=event_id,
                      name=name, status=status, date_utc=date_utc,
                      promotion_id="f0f1f2f3-f4f5-4f6f-8f7f-6f5f4f3f2f1f"))
    await session.commit()


async def add_fight(session: AsyncSession, comp_id: str, event_id: str,
                    order: int = 1, title: bool = False,
                    wc: str = "Lightweight", segment: str = "mainCard",
                    status: str = "SCHEDULED"):
    from src.db.models.event import Competition, Competitor

    session.add(Competition(id=comp_id, provider="espn", external_id=comp_id,
                            event_id=event_id, order_num=order, status=status,
                            is_title_fight=title, weight_class_name=wc,
                            card_segment=segment))
    session.add(Competitor(competition_id=comp_id, fighter_id=FIGHTER_ID, corner="red"))
    session.add(Competitor(competition_id=comp_id, fighter_id=OPPONENT_ID, corner="blue"))
    await session.commit()


class TestNextFight:
    async def test_returns_next_fight_with_opponent(self, db_session):
        from src.api.v1.fighters import get_fighter_next_fight

        await seed_fighter(db_session)
        await add_event(db_session, EVENT_UPCOMING, "UFC FN: Gamrot vs Salkilld",
                        "SCHEDULED", _days_from_now(3))
        await add_fight(db_session, COMP1_ID, EVENT_UPCOMING, order=1,
                        title=True, segment="mainCard")

        async with make_uow(db_session) as uow:
            resp = await get_fighter_next_fight(make_request(), FIGHTER_ID, uow)
        import json
        data = json.loads(resp.body)
        assert data["event_id"] == EVENT_UPCOMING
        assert data["event_name"] == "UFC FN: Gamrot vs Salkilld"
        assert data["event_status"] == "SCHEDULED"
        assert data["competition_id"] == COMP1_ID
        assert data["opponent_id"] == OPPONENT_ID
        assert data["opponent_name"] == "Arman Tsarukyan"
        assert data["corner"] == "red"
        assert data["weight_class"] == "Lightweight"
        assert data["is_title_fight"] is True
        assert data["card_segment"] == "mainCard"

    async def test_picks_earliest_of_multiple_scheduled(self, db_session):
        from src.api.v1.fighters import get_fighter_next_fight

        await seed_fighter(db_session)
        await add_event(db_session, EVENT_UPCOMING, "Early Card", "SCHEDULED",
                        _days_from_now(3))
        await add_fight(db_session, COMP1_ID, EVENT_UPCOMING, order=1)
        await add_event(db_session, EVENT_LATER, "Main Card", "SCHEDULED",
                        _days_from_now(30))
        await add_fight(db_session, COMP2_ID, EVENT_LATER, order=1)

        async with make_uow(db_session) as uow:
            resp = await get_fighter_next_fight(make_request(), FIGHTER_ID, uow)
        import json
        data = json.loads(resp.body)
        assert data["competition_id"] == COMP1_ID
        assert data["event_id"] == EVENT_UPCOMING

    async def test_ignores_final_events(self, db_session):
        from src.api.v1.fighters import get_fighter_next_fight

        await seed_fighter(db_session)
        await add_event(db_session, EVENT_FINAL, "Past Card", "FINAL",
                        datetime(2026, 1, 1, 0, 0, tzinfo=UTC))
        await add_fight(db_session, COMP3_ID, EVENT_FINAL)

        async with make_uow(db_session) as uow:
            resp = await get_fighter_next_fight(make_request(), FIGHTER_ID, uow)
        import json
        assert json.loads(resp.body) is None

    async def test_ignores_past_dated_scheduled_event(self, db_session):
        from src.api.v1.fighters import get_fighter_next_fight

        await seed_fighter(db_session)
        await add_event(db_session, EVENT_PAST, "Stale Card", "SCHEDULED",
                        datetime(2025, 1, 1, 0, 0, tzinfo=UTC))
        await add_fight(db_session, COMP4_ID, EVENT_PAST)

        async with make_uow(db_session) as uow:
            resp = await get_fighter_next_fight(make_request(), FIGHTER_ID, uow)
        import json
        assert json.loads(resp.body) is None

    async def test_null_when_fighter_has_no_upcoming(self, db_session):
        from src.api.v1.fighters import get_fighter_next_fight

        await seed_fighter(db_session)
        async with make_uow(db_session) as uow:
            resp = await get_fighter_next_fight(make_request(), FIGHTER_ID, uow)
        import json
        assert json.loads(resp.body) is None

    async def test_unknown_fighter_returns_404(self, db_session):
        from src.api.v1.fighters import get_fighter_next_fight

        await seed_fighter(db_session)
        with pytest.raises(HTTPException) as exc:
            async with make_uow(db_session) as uow:
                await get_fighter_next_fight(
                    make_request(), "00000000-0000-4000-8000-000000000001", uow)
        assert exc.value.status_code == 404

    async def test_invalid_uuid_returns_404(self, db_session):
        from src.api.v1.fighters import get_fighter_next_fight

        await seed_fighter(db_session)
        with pytest.raises(HTTPException) as exc:
            async with make_uow(db_session) as uow:
                await get_fighter_next_fight(make_request(), BAD_ID, uow)
        assert exc.value.status_code == 404
