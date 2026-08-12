"""Integration tests — Phase D fighter_provider_record_status lifecycle.

Covers:
- EMPTY fetch → CONFIRMED_ABSENT (never a fabricated fighter_records row)
- FAILED fetch → FETCH_FAILED with retry_count increment (never absence)
- repeated outcomes are idempotent (one row per fighter+provider)
- AVAILABLE / real record persistence clears absence evidence
- provider scoping — independent rows per provider
- records job selection skips CONFIRMED_ABSENT and exhausted FETCH_FAILED,
  but includes retryable FETCH_FAILED
- registry untouched, no unrelated table mutation
"""

import pytest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.sync.types import RecordFetchOutcome


@pytest.fixture
async def db_session():
    """In-memory SQLite session (same pattern as existing integration tests)."""
    engine = create_async_engine("sqlite+aiosqlite://", echo=False)
    async with engine.begin() as conn:
        import src.db.models  # noqa: F401
        from src.db.base import Base

        await conn.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, class_=AsyncSession)
    async with factory() as session:
        yield session
    await engine.dispose()


async def _make_fighter(db, external_id: str, first: str = "F", last: str = "F") -> str:
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


def _dto(external_id: str):
    from src.providers.dto import FighterDTO

    return FighterDTO(provider="espn", external_id=external_id, first_name="", last_name="")


def _record_dto(external_id: str, summary: str = "21-5-0"):
    from src.providers.dto import FighterDTO

    return FighterDTO(
        provider="espn",
        external_id=external_id,
        first_name="Islam",
        last_name="Makhachev",
        record_wins=21,
        record_losses=5,
        record_summary=summary,
        ko_tko_wins=9,
        total_fights=26,
    )


def _upsert(db):
    from src.sync.upserts.fighter import FighterUpsert
    from src.sync.upserts.id_resolver import IdResolver

    return FighterUpsert(IdResolver(db))


async def _status_rows(db):
    from src.db.models.support import FighterProviderRecordStatus

    return (await db.execute(select(FighterProviderRecordStatus))).scalars().all()


async def _record_count(db):
    from src.db.models.fighter import FighterRecord

    return (
        await db.execute(select(func.count()).select_from(FighterRecord))
    ).scalar_one()


class TestStatusLifecycle:
    @pytest.mark.asyncio
    async def test_empty_outcome_persists_confirmed_absent_without_fabrication(
        self, db_session
    ):
        from uuid import uuid4

        from src.sync.types import RecordFetchStatus

        run_id = str(uuid4())  # last_run_id is a real UUID column
        await _make_fighter(db_session, "100")
        await _upsert(db_session).apply_record_fetch_outcomes(
            [(_dto("100"), RecordFetchOutcome.EMPTY, 200)], run_id=run_id
        )
        await db_session.flush()

        rows = await _status_rows(db_session)
        assert len(rows) == 1
        assert rows[0].provider == "espn"
        assert rows[0].status == RecordFetchStatus.CONFIRMED_ABSENT.value
        assert rows[0].last_http_status == 200
        assert rows[0].retry_count == 0
        assert rows[0].last_run_id == run_id
        assert await _record_count(db_session) == 0  # never fabricated

    @pytest.mark.asyncio
    async def test_failed_outcome_persists_fetch_failed_and_increments_retries(
        self, db_session
    ):
        from src.sync.types import RecordFetchStatus

        await _make_fighter(db_session, "101")
        upsert = _upsert(db_session)
        for _ in range(2):
            await upsert.apply_record_fetch_outcomes(
                [(_dto("101"), RecordFetchOutcome.FAILED, 503)]
            )
            await db_session.flush()

        rows = await _status_rows(db_session)
        assert len(rows) == 1
        assert rows[0].status == RecordFetchStatus.FETCH_FAILED.value
        assert rows[0].last_http_status == 503
        assert rows[0].retry_count == 2
        assert await _record_count(db_session) == 0  # failure never fabricates

    @pytest.mark.asyncio
    async def test_repeated_empty_outcome_is_idempotent(self, db_session):
        await _make_fighter(db_session, "102")
        upsert = _upsert(db_session)
        for _ in range(3):
            await upsert.apply_record_fetch_outcomes(
                [(_dto("102"), RecordFetchOutcome.EMPTY, 200)]
            )
            await db_session.flush()

        assert len(await _status_rows(db_session)) == 1  # PK (fighter, provider)

    @pytest.mark.asyncio
    async def test_available_outcome_clears_status_row(self, db_session):
        await _make_fighter(db_session, "103")
        upsert = _upsert(db_session)
        await upsert.apply_record_fetch_outcomes(
            [(_dto("103"), RecordFetchOutcome.EMPTY, 200)]
        )
        await db_session.flush()
        assert len(await _status_rows(db_session)) == 1

        await upsert.apply_record_fetch_outcomes(
            [(_dto("103"), RecordFetchOutcome.AVAILABLE, 200)]
        )
        await db_session.flush()
        assert await _status_rows(db_session) == []

    @pytest.mark.asyncio
    async def test_real_record_persistence_deletes_existing_absence(self, db_session):
        from src.db.models.fighter import FighterRecord

        await _make_fighter(db_session, "104")
        upsert = _upsert(db_session)
        await upsert.apply_record_fetch_outcomes(
            [(_dto("104"), RecordFetchOutcome.EMPTY, 200)]
        )
        await db_session.flush()
        assert len(await _status_rows(db_session)) == 1

        # A real record arrives later → persisted, absence cleared.
        await upsert.upsert_records([_record_dto("104")])
        await db_session.flush()

        record = (
            await db_session.execute(
                select(FighterRecord).where(FighterRecord.record_summary == "21-5-0")
            )
        ).scalar_one_or_none()
        assert record is not None
        assert await _status_rows(db_session) == []  # absence must not survive

    @pytest.mark.asyncio
    async def test_provider_scoping_independent_rows(self, db_session):
        from src.db.models.support import FighterProviderRecordStatus

        fid = await _make_fighter(db_session, "105")
        # A hypothetical second provider has already checked this fighter.
        db_session.add(
            FighterProviderRecordStatus(
                fighter_id=fid,
                provider="ufcstats",
                status="CONFIRMED_ABSENT",
            )
        )
        await db_session.flush()

        await _upsert(db_session).apply_record_fetch_outcomes(
            [(_dto("105"), RecordFetchOutcome.EMPTY, 200)]
        )
        await db_session.flush()

        rows = await _status_rows(db_session)
        assert len(rows) == 2  # independent per (fighter, provider)
        providers = {r.provider for r in rows}
        assert providers == {"espn", "ufcstats"}


class TestRecordsJobSelection:
    """Records backfill selection skips established absences (Phase D)."""

    class FakeProvider:
        _config = type("_Cfg", (), {"max_concurrency": 2})()

        def __init__(self):
            self.calls: list[str] = []

        async def fetch_fighter_record_with_outcome(self, external_id):
            from src.sync.types import RecordFetchOutcome

            self.calls.append(external_id)
            return None, RecordFetchOutcome.EMPTY, 200

    async def _fetch_ids(self, db_session) -> list[str]:
        from src.providers.espn.jobs.records import ESPN_RecordsBackfillJob
        from src.sync.context import SyncContext
        from src.sync.state import SyncState
        from src.sync.types import EntityType

        provider = self.FakeProvider()
        job = ESPN_RecordsBackfillJob()
        ctx = SyncContext(provider=provider, db=db_session)
        state = SyncState.for_entity(EntityType.RECORDS, "espn")
        dtos = await job._fetch(ctx, state)
        assert provider.calls == [d.external_id for d, _o, _s in dtos]
        return [d.external_id for d, _o, _s in dtos]

    @pytest.mark.asyncio
    async def test_skips_confirmed_absent_permanent_and_exhausted_failed(self, db_session):
        from src.db.models.support import FighterProviderRecordStatus
        from src.sync.types import RecordFetchStatus

        await _make_fighter(db_session, "201")  # no status → selected
        fid_b = await _make_fighter(db_session, "202")
        fid_c = await _make_fighter(db_session, "203")
        fid_d = await _make_fighter(db_session, "204")

        db_session.add(
            FighterProviderRecordStatus(
                fighter_id=fid_b, provider="espn",
                status=RecordFetchStatus.CONFIRMED_ABSENT.value,
            )
        )
        db_session.add(
            FighterProviderRecordStatus(
                fighter_id=fid_c, provider="espn",
                status=RecordFetchStatus.FETCH_FAILED.value, retry_count=3,
            )
        )
        db_session.add(
            FighterProviderRecordStatus(
                fighter_id=fid_d, provider="espn",
                status=RecordFetchStatus.PERMANENT_FAILURE.value,
            )
        )
        await db_session.flush()

        # Ascending selection: absent/permanent/exhausted-failed all excluded.
        ids = await self._fetch_ids(db_session)
        assert ids == ["201"]

    @pytest.mark.asyncio
    async def test_includes_retryable_fetch_failed(self, db_session):
        from src.db.models.support import FighterProviderRecordStatus
        from src.sync.types import RecordFetchStatus

        await _make_fighter(db_session, "204")
        fid = await _make_fighter(db_session, "205")
        db_session.add(
            FighterProviderRecordStatus(
                fighter_id=fid, provider="espn",
                status=RecordFetchStatus.FETCH_FAILED.value, retry_count=1,
            )
        )
        await db_session.flush()

        ids = await self._fetch_ids(db_session)
        assert ids == ["204", "205"]  # within retry budget → still selected

    @pytest.mark.asyncio
    async def test_registry_untouched_by_status_writes(self, db_session):
        from src.db.models.support import SyncDiscoveredAthlete

        await _make_fighter(db_session, "206")
        await _upsert(db_session).apply_record_fetch_outcomes(
            [(_dto("206"), RecordFetchOutcome.EMPTY, 200)]
        )
        await db_session.flush()

        registry = (
            await db_session.execute(select(func.count()).select_from(SyncDiscoveredAthlete))
        ).scalar_one()
        assert registry == 0  # registry-neutral invariant


class TestRecordFetchApiAccess:
    """D5 — repository + service wiring behind FighterProfileResponse.record_fetch.

    The profile field is additive and strictly evidence-backed: populated only
    when a status row exists; None for HAS_RECORD and NOT_CHECKED fighters.
    """

    @pytest.mark.asyncio
    async def test_repository_single_lookup(self, db_session):
        from src.db.models.support import FighterProviderRecordStatus
        from src.db.repositories.fighter import FighterRepository

        fid_checked = await _make_fighter(db_session, "301")
        fid_unchecked = await _make_fighter(db_session, "302")
        db_session.add(
            FighterProviderRecordStatus(
                fighter_id=fid_checked, provider="espn",
                status="CONFIRMED_ABSENT", last_http_status=200,
                provenance="FINAL_SWEEP",
            )
        )
        await db_session.flush()

        repo = FighterRepository(db_session)
        row = await repo.get_record_fetch_status(fid_checked)
        assert row is not None
        assert row.status == "CONFIRMED_ABSENT"
        assert row.provenance == "FINAL_SWEEP"
        assert await repo.get_record_fetch_status(fid_unchecked) is None
        # provider scoping — wrong provider must not match
        assert await repo.get_record_fetch_status(fid_checked, provider="ufcstats") is None

    @pytest.mark.asyncio
    async def test_repository_batch_lookup(self, db_session):
        from src.db.models.support import FighterProviderRecordStatus
        from src.db.repositories.fighter import FighterRepository

        fids = [await _make_fighter(db_session, e) for e in ("303", "304", "305")]
        db_session.add(
            FighterProviderRecordStatus(
                fighter_id=fids[0], provider="espn", status="CONFIRMED_ABSENT",
            )
        )
        db_session.add(
            FighterProviderRecordStatus(
                fighter_id=fids[2], provider="espn", status="FETCH_FAILED",
            )
        )
        await db_session.flush()

        rows = await FighterRepository(db_session).get_record_fetch_statuses(fids)
        assert set(rows) == {fids[0], fids[2]}  # missing fighter absent from dict
        assert rows[fids[0]].status == "CONFIRMED_ABSENT"
        assert rows[fids[2]].status == "FETCH_FAILED"
        assert await FighterRepository(db_session).get_record_fetch_statuses([]) == {}

    @pytest.mark.asyncio
    async def test_service_detail_includes_record_fetch(self, db_session):
        from datetime import UTC, datetime

        from src.db.models.support import FighterProviderRecordStatus
        from src.db.unit_of_work import UnitOfWork
        from src.services.fighter_service import FighterService

        fid_checked = await _make_fighter(db_session, "306", first="Herb", last="Dean")
        fid_has_record = await _make_fighter(db_session, "307", first="Islam", last="Makhachev")
        await _upsert(db_session).upsert_records([_record_dto("307", "28-1-0")])
        db_session.add(
            FighterProviderRecordStatus(
                fighter_id=fid_checked, provider="espn",
                status="CONFIRMED_ABSENT", last_http_status=200,
                result_detail="http 200 — no usable record payload",
                last_checked_at=datetime(2026, 8, 12, 8, 47, 45, tzinfo=UTC),
                provenance="FINAL_SWEEP",
            )
        )
        await db_session.flush()

        # Assertions stay INSIDE the UoW block: __aexit__ commits and expires
        # ORM instances; reading expired attributes after the block would trigger
        # a lazy reload outside the greenlet context.
        async with UnitOfWork(db_session) as uow:
            svc = FighterService(uow)
            checked = await svc.get_fighter_detail(fid_checked)
            has_record = await svc.get_fighter_detail(fid_has_record)

            assert checked is not None and has_record is not None
            # CONFIRMED_ABSENT fighter → record_fetch populated, record absent
            assert checked["record"] is None
            assert checked["record_fetch"] is not None
            assert checked["record_fetch"].status == "CONFIRMED_ABSENT"
            assert checked["record_fetch"].last_http_status == 200
            assert checked["record_fetch"].provenance == "FINAL_SWEEP"
            # HAS_RECORD fighter → canonical record present, no status row
            assert has_record["record"] is not None
            assert has_record["record_fetch"] is None

    @pytest.mark.asyncio
    async def test_api_mapper_end_to_end(self, db_session):
        """Full chain: status row → service detail → profile schema → JSON."""
        from src.api.v1.fighters import _fighter_to_profile
        from src.db.models.support import FighterProviderRecordStatus
        from src.db.unit_of_work import UnitOfWork
        from src.services.fighter_service import FighterService

        fid = await _make_fighter(db_session, "308")
        db_session.add(
            FighterProviderRecordStatus(
                fighter_id=fid, provider="espn", status="CONFIRMED_ABSENT",
                last_http_status=200, retry_count=0, provenance="FINAL_SWEEP",
            )
        )
        await db_session.flush()

        # Mapping happens inside the UoW block (mirrors the endpoint loader):
        # the mapper reads ORM columns, which expire at commit on block exit.
        async with UnitOfWork(db_session) as uow:
            detail = await FighterService(uow).get_fighter_detail(fid)
            profile = _fighter_to_profile(
                fighter=detail["fighter"],
                record=detail.get("record"),
                record_fetch=detail.get("record_fetch"),
                rankings=detail.get("rankings"),
                recent_fights=detail.get("recent_fights"),
            )
        dumped = profile.model_dump(mode="json")
        assert dumped["record"] is None
        assert dumped["record_fetch"] == {
            "status": "CONFIRMED_ABSENT",
            "provider": "espn",
            "last_checked_at": profile.record_fetch.last_checked_at.isoformat()
            if profile.record_fetch.last_checked_at else None,
            "last_http_status": 200,
            "result_detail": None,
            "retry_count": 0,
            "provenance": "FINAL_SWEEP",
        }
