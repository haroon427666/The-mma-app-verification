"""Compare route — T15 (FTR-1905/1906/1907).

`GET /v1/compare?a=&b=` — one call: two fighter summaries + head-to-head
bouts (most recent first) + common opponents (with per-side chronological
outcomes). Unknown fighter → 404; invalid UUID → 404; a == b → 422.

Note: all ids below contain letters — all-digit UUID strings get REAL-stored
by sqlite NUMERIC affinity (the postgresql-UUID bind processor strips
hyphens), which breaks string equality assertions.
"""

from datetime import UTC, datetime

import pytest
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from tests.api.test_uuid_guards import BAD_ID, make_request, make_uow

FIGHTER_A = "550e8400-e29b-41d4-a716-4466554400aa"
FIGHTER_B = "6f9619ff-8b86-d011-b42d-00c04fc964bb"
OPP_X = "a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d"
OPP_Y = "b2c3d4e5-f6a7-4b8c-9d0e-1f2a3b4c5d6e"
PROMO_ID = "f0f1f2f3-f4f5-4f6f-8f7f-6f5f4f3f2f1f"
EVENT_H2H = "c8f0d7e6-b5a4-4c3b-a291-8f7e6d5c4b3a"
EVENT_OLDER = "d4e5f6a7-b8c9-4d0e-8f1a-2b3c4d5e6f7a"
EVENT_AB = "e6f7a8b9-c0d1-4e2f-9a3b-4c5d6e7f8a9b"
EVENT_AX = "f8a9b0c1-d2e3-4f4a-8b5c-6d7e8f9a0b1c"
EVENT_AX2 = "0c1d2e3f-4a5b-4c6d-8e7f-9a0b1c2d3e4f"
EVENT_BX = "1d2e3f4a-5b6c-4d7e-9f8a-0b1c2d3e4f5a"
COMP_H2H = "2e3f4a5b-6c7d-4e8f-9a0b-1c2d3e4f5a6b"
COMP_OLDER = "3f4a5b6c-7d8e-4f9a-8b0c-1d2e3f4a5b6c"
COMP_AB = "4a5b6c7d-8e9f-4a0b-8c1d-2e3f4a5b6c7d"


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


async def seed(session: AsyncSession):
    from src.db.models import Fighter, Promotion

    session.add(Promotion(id=PROMO_ID, provider="espn", external_id="ufc", name="UFC"))
    session.add(Fighter(id=FIGHTER_A, provider="espn", external_id="1",
                        first_name="Islam", last_name="Makhachev",
                        record_wins=26, record_losses=1, record_draws=0))
    session.add(Fighter(id=FIGHTER_B, provider="espn", external_id="2",
                        first_name="Arman", last_name="Tsarukyan",
                        record_wins=22, record_losses=3, record_draws=0))
    session.add(Fighter(id=OPP_X, provider="espn", external_id="3",
                        first_name="Charles", last_name="Oliveira",
                        record_wins=34, record_losses=10, record_draws=0))
    session.add(Fighter(id=OPP_Y, provider="espn", external_id="4",
                        first_name="Beneil", last_name="Dariush"))
    await session.commit()


async def add_event(session: AsyncSession, event_id: str, name: str, date_utc: datetime):
    from src.db.models.event import Event

    session.add(Event(id=event_id, provider="espn", external_id=event_id,
                      name=name, status="FINAL", date_utc=date_utc,
                      promotion_id=PROMO_ID))
    await session.commit()


async def add_fight(session: AsyncSession, comp_id: str, event_id: str,
                    fighter_id: str, opponent_id: str, *,
                    order: int = 1, title: bool = False, wc: str = "Lightweight",
                    method: str | None = None, round_: int | None = None):
    from src.db.models.event import Competition, Competitor

    session.add(Competition(id=comp_id, provider="espn", external_id=comp_id,
                            event_id=event_id, order_num=order, status="FINAL",
                            is_title_fight=title, weight_class_name=wc,
                            result_method=method, result_round=round_))
    session.add(Competitor(competition_id=comp_id, fighter_id=fighter_id,
                           corner="red", outcome="WIN"))
    session.add(Competitor(competition_id=comp_id, fighter_id=opponent_id,
                           corner="blue", outcome="LOSS"))
    await session.commit()


def _route():
    from src.api.v1.compare import compare_fighters

    return compare_fighters


class TestCompare:
    async def test_returns_both_summaries(self, db_session):
        await seed(db_session)
        async with make_uow(db_session) as uow:
            resp = await _route()(make_request(), a=FIGHTER_A, b=FIGHTER_B, uow=uow)
        import json
        data = json.loads(resp.body)
        assert data["a"]["first_name"] == "Islam"
        assert data["a"]["last_name"] == "Makhachev"
        assert data["a"]["record"] == "26-1-0"
        assert data["b"]["first_name"] == "Arman"
        assert data["b"]["last_name"] == "Tsarukyan"
        assert data["b"]["record"] == "22-3-0"
        assert data["head_to_head"] == []
        assert data["common_opponents"] == []

    async def test_head_to_head_lists_bouts_with_results(self, db_session):
        await seed(db_session)
        await add_event(db_session, EVENT_H2H, "UFC 302", datetime(2024, 6, 1, 22, 0, tzinfo=UTC))
        await add_fight(db_session, COMP_H2H, EVENT_H2H, FIGHTER_A, FIGHTER_B,
                        title=True, method="Submission", round_=1)
        async with make_uow(db_session) as uow:
            resp = await _route()(make_request(), a=FIGHTER_A, b=FIGHTER_B, uow=uow)
        import json
        data = json.loads(resp.body)
        assert len(data["head_to_head"]) == 1
        bout = data["head_to_head"][0]
        assert bout["competition_id"] == COMP_H2H
        assert bout["event_name"] == "UFC 302"
        assert bout["result_a"] == "WIN"
        assert bout["result_b"] == "LOSS"
        assert bout["method"] == "Submission"
        assert bout["round"] == 1
        assert bout["is_title_fight"] is True
        assert bout["weight_class"] == "Lightweight"

    async def test_head_to_head_orders_most_recent_first(self, db_session):
        await seed(db_session)
        await add_event(db_session, EVENT_H2H, "Recent Card", datetime(2025, 6, 1, 22, 0, tzinfo=UTC))
        await add_fight(db_session, COMP_H2H, EVENT_H2H, FIGHTER_A, FIGHTER_B, order=2)
        await add_event(db_session, EVENT_OLDER, "Older Card", datetime(2023, 1, 1, 22, 0, tzinfo=UTC))
        await add_fight(db_session, COMP_OLDER, EVENT_OLDER, FIGHTER_A, FIGHTER_B, order=1)
        async with make_uow(db_session) as uow:
            resp = await _route()(make_request(), a=FIGHTER_A, b=FIGHTER_B, uow=uow)
        import json
        bouts = json.loads(resp.body)["head_to_head"]
        assert [b["competition_id"] for b in bouts] == [COMP_H2H, COMP_OLDER]

    async def test_common_opponents_with_per_side_outcomes(self, db_session):
        await seed(db_session)
        # X is the opponent in both bouts → X's outcomes are LOSS vs each side
        await add_event(db_session, EVENT_AX, "A vs X", datetime(2025, 6, 1, 22, 0, tzinfo=UTC))
        await add_fight(db_session, COMP_AB, EVENT_AX, FIGHTER_A, OPP_X)
        await add_event(db_session, EVENT_BX, "B vs X", datetime(2025, 1, 1, 22, 0, tzinfo=UTC))
        await add_fight(db_session, COMP_OLDER, EVENT_BX, FIGHTER_B, OPP_X)
        # Y fought only A → must not appear
        await add_event(db_session, EVENT_AX2, "A vs Y", datetime(2024, 3, 1, 22, 0, tzinfo=UTC))
        await add_fight(db_session, COMP_H2H, EVENT_AX2, FIGHTER_A, OPP_Y)
        async with make_uow(db_session) as uow:
            resp = await _route()(make_request(), a=FIGHTER_A, b=FIGHTER_B, uow=uow)
        import json
        common = json.loads(resp.body)["common_opponents"]
        assert [c["name"] for c in common] == ["Charles Oliveira"]
        assert common[0]["record"] == "34-10-0"
        assert common[0]["vs_a"] == ["LOSS"]
        assert common[0]["vs_b"] == ["LOSS"]

    async def test_common_opponents_outcomes_chronological(self, db_session):
        await seed(db_session)
        # X lost to A twice — oldest first
        await add_event(db_session, EVENT_AX2, "First A-X", datetime(2023, 3, 1, 22, 0, tzinfo=UTC))
        await add_fight(db_session, COMP_H2H, EVENT_AX2, FIGHTER_A, OPP_X)
        await add_event(db_session, EVENT_AX, "Second A-X", datetime(2025, 6, 1, 22, 0, tzinfo=UTC))
        await add_fight(db_session, COMP_AB, EVENT_AX, FIGHTER_A, OPP_X)
        await add_event(db_session, EVENT_BX, "B vs X", datetime(2025, 1, 1, 22, 0, tzinfo=UTC))
        await add_fight(db_session, COMP_OLDER, EVENT_BX, FIGHTER_B, OPP_X)
        async with make_uow(db_session) as uow:
            resp = await _route()(make_request(), a=FIGHTER_A, b=FIGHTER_B, uow=uow)
        import json
        common = json.loads(resp.body)["common_opponents"]
        assert common[0]["vs_a"] == ["LOSS", "LOSS"]

    async def test_same_fighter_returns_422(self, db_session):
        await seed(db_session)
        with pytest.raises(HTTPException) as exc:
            async with make_uow(db_session) as uow:
                await _route()(make_request(), a=FIGHTER_A, b=FIGHTER_A, uow=uow)
        assert exc.value.status_code == 422

    async def test_unknown_fighter_returns_404(self, db_session):
        await seed(db_session)
        with pytest.raises(HTTPException) as exc:
            async with make_uow(db_session) as uow:
                await _route()(make_request(),
                               a=FIGHTER_A,
                               b="00000000-0000-4000-8000-000000000001",
                               uow=uow)
        assert exc.value.status_code == 404

    async def test_invalid_uuid_returns_404(self, db_session):
        await seed(db_session)
        with pytest.raises(HTTPException) as exc:
            async with make_uow(db_session) as uow:
                await _route()(make_request(), a=FIGHTER_A, b=BAD_ID, uow=uow)
        assert exc.value.status_code == 404
