"""Weight-class routes — T13.

`GET /v1/weight-classes` and `GET /v1/weight-classes/{id}` backed by the
weight_classes table. Also guards non-UUID ids with 404.

NOTE: seed ids must contain hex letters. The postgresql.UUID bind processor
strips hyphens, so all-digit ids become integer literals that sqlite's
NUMERIC affinity stores as REAL, breaking lookups on sqlite.
"""

import pytest
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from tests.api.test_uuid_guards import BAD_ID, make_request, make_uow

LW_ID = "550e8400-e29b-41d4-a716-446655440000"
BW_ID = "6f9619ff-8b86-d011-b42d-00c04fc964ff"
FIGHTER_ID = "8d2a6f30-4f2e-4b7a-9c3e-1a2b3c4d5e6f"


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
    from src.db.models import Fighter, WeightClass

    lw = WeightClass(id=LW_ID, provider="espn", external_id="970",
                     name="Lightweight", abbreviation="LW",
                     min_weight_kg=65.8, max_weight_kg=70.3)
    bw = WeightClass(id=BW_ID,
                     provider="espn", external_id="971", name="Bantamweight",
                     abbreviation="BW", min_weight_kg=56.7, max_weight_kg=61.2)
    session.add_all([lw, bw])

    session.add(Fighter(
        id=FIGHTER_ID,
        provider="espn", external_id="100",
        first_name="Test", last_name="One",
        weight_class_id=LW_ID, weight_class_name="Lightweight",
    ))
    await session.commit()


class TestListWeightClasses:
    async def test_returns_paginated_shape(self, db_session):
        from src.api.v1.other import list_weight_classes
        from src.dependencies import Pagination

        await seed(db_session)
        resp = await list_weight_classes(
            make_request(), Pagination(page=1, limit=50), make_uow(db_session)
        )
        body = resp.body  # cached_json_response returns Response
        import json
        data = json.loads(body)
        assert data["total"] == 2
        assert data["page"] == 1
        assert data["limit"] == 50
        assert data["pages"] == 1
        names = [i["name"] for i in data["items"]]
        assert names == ["Bantamweight", "Lightweight"]  # ordered by name
        lw_item = next(i for i in data["items"] if i["id"] == LW_ID)
        assert lw_item["fighter_count"] == 1
        assert lw_item["abbreviation"] == "LW"

    async def test_second_page_empty(self, db_session):
        from src.api.v1.other import list_weight_classes
        from src.dependencies import Pagination

        await seed(db_session)
        resp = await list_weight_classes(
            make_request(), Pagination(page=2, limit=50), make_uow(db_session)
        )
        import json
        data = json.loads(resp.body)
        assert data["items"] == []
        assert data["total"] == 2
        assert data["pages"] == 1


class TestGetWeightClass:
    async def test_detail(self, db_session):
        from src.api.v1.other import get_weight_class

        await seed(db_session)
        result = await get_weight_class(LW_ID, make_uow(db_session))
        assert result.name == "Lightweight"
        assert result.abbreviation == "LW"
        assert result.min_weight_kg == 65.8
        assert result.max_weight_kg == 70.3
        assert result.fighter_count == 1

    async def test_missing_returns_404(self, db_session):
        from src.api.v1.other import get_weight_class

        await seed(db_session)
        with pytest.raises(HTTPException) as exc:
            await get_weight_class("deadbeef-dead-4eed-a11e-deadbeeff00d",
                                   make_uow(db_session))
        assert exc.value.status_code == 404

    async def test_invalid_uuid_returns_404(self, db_session):
        from src.api.v1.other import get_weight_class

        await seed(db_session)
        with pytest.raises(HTTPException) as exc:
            await get_weight_class(BAD_ID, make_uow(db_session))
        assert exc.value.status_code == 404
