"""Favorites API tests — T08 (real DB-backed favorites, replacing stubs).

POST /v1/me/favorites/{fighters|events}/{id} must persist; GET must reflect it;
DELETE must remove it. Uses SQLite in-memory for real DB state.
"""

from uuid import uuid4

import pytest
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine


@pytest.fixture
async def db_session():
    engine = create_async_engine("sqlite+aiosqlite://", echo=False)
    async with engine.begin() as conn:
        import src.db.models
        import src.db.models.auth  # noqa: F401
        from src.db.base import Base
        await conn.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, class_=AsyncSession)
    async with factory() as session:
        yield session
    await engine.dispose()


def make_user(uid):
    from src.auth.jwt import TokenPayload

    return TokenPayload(sub=uid, email="t@example.com", role="user")


class TestFavorites:
    @pytest.mark.asyncio
    async def test_favorite_flow_round_trip(self, db_session):
        from src.api.v1.users import (
            favorite_event,
            favorite_fighter,
            get_favorites,
            unfavorite_fighter,
        )

        uid = str(uuid4())
        fighter_id = str(uuid4())
        event_id = str(uuid4())
        user = make_user(uid)

        resp = await favorite_fighter(fighter_id, user=user, session=db_session)
        assert resp == {"status": "added", "fighter_id": fighter_id}
        await favorite_event(event_id, user=user, session=db_session)

        favs = await get_favorites(user=user, session=db_session)
        assert favs.fighters == [fighter_id]
        assert favs.events == [event_id]

        await unfavorite_fighter(fighter_id, user=user, session=db_session)
        favs = await get_favorites(user=user, session=db_session)
        assert favs.fighters == []
        assert favs.events == [event_id]

    @pytest.mark.asyncio
    async def test_favorite_is_idempotent(self, db_session):
        from src.api.v1.users import favorite_fighter, get_favorites

        uid = str(uuid4())
        fighter_id = str(uuid4())
        user = make_user(uid)

        await favorite_fighter(fighter_id, user=user, session=db_session)
        await favorite_fighter(fighter_id, user=user, session=db_session)

        favs = await get_favorites(user=user, session=db_session)
        assert favs.fighters == [fighter_id]

    @pytest.mark.asyncio
    async def test_favorites_are_scoped_to_user(self, db_session):
        from src.api.v1.users import favorite_fighter, get_favorites

        uid_a, uid_b = str(uuid4()), str(uuid4())
        fighter_id = str(uuid4())
        await favorite_fighter(fighter_id, user=make_user(uid_a), session=db_session)

        favs_b = await get_favorites(user=make_user(uid_b), session=db_session)
        assert favs_b.fighters == []

    @pytest.mark.asyncio
    async def test_invalid_uuid_returns_404(self, db_session):
        from src.api.v1.users import favorite_fighter

        user = make_user(str(uuid4()))
        with pytest.raises(HTTPException) as exc:
            await favorite_fighter("not-a-uuid", user=user, session=db_session)
        assert exc.value.status_code == 404

    @pytest.mark.asyncio
    async def test_promotion_favorites_are_501(self, db_session):
        from src.api.v1.users import favorite_promotion

        user = make_user(str(uuid4()))
        with pytest.raises(HTTPException) as exc:
            await favorite_promotion("ufc", user=user)
        assert exc.value.status_code == 501
