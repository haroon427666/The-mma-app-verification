"""Pagination shape contract test — T11.

Pins the WIRE shape of every paginated list endpoint to exactly
{items, total, page, limit, pages} — no `data` wrapper, no `pageSize`/`hasMore`
(mobile `PaginatedResponse` used to declare those; decision: keep backend shape,
align mobile types).

Consumers verified against this shape:
- GET /v1/fighters            (list_fighters → PaginatedResponse)
- GET /v1/events              (list_events → PaginatedResponse)
- GET /v1/events/past         (past_events → PaginatedResponse)
- GET /v1/fights              (list_fights → PaginatedResponse)
"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

EXPECTED_KEYS = {"items", "total", "page", "limit", "pages"}


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


def envelope(items, total, page, limit):
    from src.schemas.common import PaginatedResponse, PaginationParams

    params = PaginationParams(page=page, limit=limit)
    return PaginatedResponse.from_query(items=items, total=total, params=params).model_dump(mode="json")


class TestEnvelopeShape:
    def test_envelope_exact_keys(self):
        payload = envelope(items=[{"id": "a"}, {"id": "b"}], total=2, page=1, limit=2)
        assert set(payload.keys()) == EXPECTED_KEYS

    def test_envelope_has_no_legacy_keys(self):
        payload = envelope(items=[], total=0, page=1, limit=50)
        assert "data" not in payload
        assert "pageSize" not in payload
        assert "hasMore" not in payload

    def test_envelope_field_types(self):
        payload = envelope(items=[1, 2, 3], total=3, page=1, limit=3)
        assert isinstance(payload["items"], list)
        assert isinstance(payload["total"], int)
        assert isinstance(payload["page"], int)
        assert isinstance(payload["limit"], int)
        assert isinstance(payload["pages"], int)

    def test_pages_is_ceil_division(self):
        payload = envelope(items=[1] * 50, total=200, page=2, limit=50)
        assert payload["pages"] == 4
        assert payload["total"] == 200
        assert payload["page"] == 2
        assert payload["limit"] == 50
        assert len(payload["items"]) == 50

    def test_empty_result_pages_zero(self):
        payload = envelope(items=[], total=0, page=1, limit=50)
        assert payload["total"] == 0
        assert payload["pages"] == 0
        assert payload["items"] == []

    def test_partial_last_page(self):
        payload = envelope(items=[1] * 5, total=105, page=11, limit=10)
        assert payload["pages"] == 11
        assert len(payload["items"]) == 5


class TestRouteEmitsEnvelope:
    @pytest.mark.asyncio
    async def test_past_events_route_emits_envelope(self, db_session):
        """A real route (GET /v1/events/past) must return the exact envelope."""
        from src.api.v1.events import past_events
        from src.db.unit_of_work import UnitOfWork
        from src.schemas.common import PaginationParams

        uow = UnitOfWork(session=db_session)
        resp = await past_events(pagination=PaginationParams(page=1, limit=2), uow=uow)
        payload = resp.model_dump(mode="json")
        assert set(payload.keys()) == EXPECTED_KEYS
        assert payload["items"] == []
        assert payload["total"] == 0
        assert payload["page"] == 1
        assert payload["limit"] == 2
        assert payload["pages"] == 0
