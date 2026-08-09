"""UUID path-param guards — T12.

Non-UUID ids on `{id}` routes previously reached the DB and surfaced as a 500
(asyncpg DataError on Postgres UUID columns). Every entity route must now
reject them with 404 before touching the DB or cache.
"""

import pytest
from fastapi import HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

BAD_ID = "not-a-uuid"


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


def make_request() -> Request:
    return Request(scope={
        "type": "http",
        "asgi": {"version": "3.0"},
        "http_version": "1.1",
        "method": "GET",
        "scheme": "http",
        "path": "/",
        "raw_path": b"/",
        "query_string": b"",
        "headers": [],
        "client": ("test", 1),
        "server": ("test", 80),
    })


def make_uow(session):
    from src.db.unit_of_work import UnitOfWork
    return UnitOfWork(session=session)


async def expect_404(coro):
    with pytest.raises(HTTPException) as exc:
        await coro
    assert exc.value.status_code == 404


class TestRequireUuid:
    def test_valid_uuid_passes(self):
        from src.api.utils import require_uuid

        assert require_uuid("550e8400-e29b-41d4-a716-446655440000") == "550e8400-e29b-41d4-a716-446655440000"

    def test_invalid_uuid_404(self):
        from src.api.utils import require_uuid

        with pytest.raises(HTTPException) as exc:
            require_uuid(BAD_ID)
        assert exc.value.status_code == 404


class TestWatchlistGuards:
    @pytest.mark.asyncio
    async def test_add_event_watchlist_rejects_bad_uuid(self, db_session):
        from src.api.v1.watchlist import add_event_watchlist
        from src.auth.jwt import TokenPayload
        user = TokenPayload(sub="u1", email="t@example.com", role="user")
        await expect_404(add_event_watchlist(BAD_ID, user=user, session=db_session))

    @pytest.mark.asyncio
    async def test_add_fighter_favorite_rejects_bad_uuid(self, db_session):
        from src.api.v1.watchlist import add_fighter_favorite
        from src.auth.jwt import TokenPayload
        user = TokenPayload(sub="u1", email="t@example.com", role="user")
        await expect_404(add_fighter_favorite(BAD_ID, user=user, session=db_session))


class TestNotificationGuards:
    @pytest.mark.asyncio
    async def test_mark_read_rejects_bad_uuid(self, db_session):
        from src.api.v1.notifications import mark_read
        from src.auth.jwt import TokenPayload
        user = TokenPayload(sub="u1", email="t@example.com", role="user")
        await expect_404(mark_read(BAD_ID, user=user, session=db_session))

    @pytest.mark.asyncio
    async def test_delete_rejects_bad_uuid(self, db_session):
        from src.api.v1.notifications import delete_notification
        from src.auth.jwt import TokenPayload
        user = TokenPayload(sub="u1", email="t@example.com", role="user")
        await expect_404(delete_notification(BAD_ID, user=user, session=db_session))


class TestFighterGuards:
    @pytest.mark.asyncio
    async def test_get_fighter_rejects_bad_uuid(self, db_session):
        from src.api.v1.fighters import get_fighter

        await expect_404(get_fighter(make_request(), BAD_ID, uow=make_uow(db_session)))

    @pytest.mark.asyncio
    async def test_get_fighter_stats_rejects_bad_uuid(self, db_session):
        from src.api.v1.fighters import get_fighter_stats

        await expect_404(get_fighter_stats(make_request(), BAD_ID, uow=make_uow(db_session)))

    @pytest.mark.asyncio
    async def test_get_fighter_history_rejects_bad_uuid(self, db_session):
        from src.api.v1.fighters import get_fighter_history

        await expect_404(get_fighter_history(make_request(), BAD_ID, uow=make_uow(db_session)))

    @pytest.mark.asyncio
    async def test_get_fighter_media_rejects_bad_uuid(self, db_session):
        from src.api.v1.fighters import get_fighter_media

        await expect_404(get_fighter_media(BAD_ID, uow=make_uow(db_session)))


class TestEventGuards:
    @pytest.mark.asyncio
    async def test_get_event_rejects_bad_uuid(self, db_session):
        from src.api.v1.events import get_event

        await expect_404(get_event(make_request(), BAD_ID, uow=make_uow(db_session)))

    @pytest.mark.asyncio
    async def test_get_event_fights_rejects_bad_uuid(self, db_session):
        from src.api.v1.events import get_event_fights

        await expect_404(get_event_fights(make_request(), BAD_ID, uow=make_uow(db_session)))


class TestFightGuards:
    @pytest.mark.asyncio
    async def test_get_fight_rejects_bad_uuid(self, db_session):
        from src.api.v1.fights import get_fight

        await expect_404(get_fight(make_request(), BAD_ID, uow=make_uow(db_session)))


class TestVenueGuards:
    @pytest.mark.asyncio
    async def test_get_venue_rejects_bad_uuid(self, db_session):
        from src.api.v1.other import get_venue

        await expect_404(get_venue(BAD_ID, uow=make_uow(db_session)))

    @pytest.mark.asyncio
    async def test_venue_events_rejects_bad_uuid(self, db_session):
        from src.api.v1.other import venue_events
        from src.schemas.common import PaginationParams
        await expect_404(venue_events(BAD_ID, pagination=PaginationParams(page=1, limit=10), uow=make_uow(db_session)))
