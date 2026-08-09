"""Preferences API tests — T09 (real persistence, replacing the echo stub).

GET /v1/me/preferences returns defaults before any PATCH; PATCH persists and
merges partial updates; a second GET reflects the stored row.
"""

from uuid import uuid4

import pytest
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


class TestPreferences:
    @pytest.mark.asyncio
    async def test_defaults_before_any_patch(self, db_session):
        from src.api.v1.users import get_preferences

        prefs = await get_preferences(user=make_user(str(uuid4())), session=db_session)
        assert prefs.theme == "system"
        assert prefs.default_homepage == "rankings"
        assert prefs.notify_upcoming_fight is True

    @pytest.mark.asyncio
    async def test_patch_persists_and_get_reflects(self, db_session):
        from src.api.v1.users import UpdatePreferencesRequest, get_preferences, update_preferences

        user = make_user(str(uuid4()))
        await update_preferences(
            UpdatePreferencesRequest(theme="dark", notify_ranking_changed=True),
            user=user, session=db_session,
        )
        prefs = await get_preferences(user=user, session=db_session)
        assert prefs.theme == "dark"
        assert prefs.notify_ranking_changed is True

    @pytest.mark.asyncio
    async def test_patch_is_partial_merge(self, db_session):
        from src.api.v1.users import UpdatePreferencesRequest, get_preferences, update_preferences

        user = make_user(str(uuid4()))
        await update_preferences(
            UpdatePreferencesRequest(theme="dark"), user=user, session=db_session,
        )
        await update_preferences(
            UpdatePreferencesRequest(notify_fight_cancelled=False),
            user=user, session=db_session,
        )
        prefs = await get_preferences(user=user, session=db_session)
        assert prefs.theme == "dark"  # untouched field survived
        assert prefs.notify_fight_cancelled is False

    @pytest.mark.asyncio
    async def test_preferences_are_scoped_to_user(self, db_session):
        from src.api.v1.users import UpdatePreferencesRequest, get_preferences, update_preferences

        uid_a, uid_b = str(uuid4()), str(uuid4())
        await update_preferences(
            UpdatePreferencesRequest(theme="dark"), user=make_user(uid_a), session=db_session,
        )
        prefs_b = await get_preferences(user=make_user(uid_b), session=db_session)
        assert prefs_b.theme == "system"
