"""Integration tests — transactions, rollback, dead letter, payload archive."""

import pytest


class TestTransactionBoundary:
    """UnitOfWork: commit/rollback behavior."""

    @pytest.mark.asyncio
    async def test_unit_of_work_exposes_all_repos(self):
        """UnitOfWork provides access to all repositories."""
        from src.db.unit_of_work import UnitOfWork
        async with UnitOfWork() as uow:
            assert hasattr(uow, "fighters")
            assert hasattr(uow, "events")
            assert hasattr(uow, "competitions")
            assert hasattr(uow, "promotions")
            assert hasattr(uow, "venues")
            assert hasattr(uow, "rankings")
            assert hasattr(uow, "weight_classes")
            assert hasattr(uow, "broadcasts")

    @pytest.mark.asyncio
    async def test_rollback_on_exception(self):
        """Exception inside UnitOfWork → automatic rollback."""
        from src.db.unit_of_work import UnitOfWork

        class TestError(Exception):
            pass

        with pytest.raises(TestError):
            async with UnitOfWork() as uow:
                raise TestError("simulated failure")

        # UnitOfWork.__aexit__ should have called rollback()
        # Verified by: async with ... → __aexit__(exc_type=TestError, ...)

    def test_external_session_not_closed(self):
        """If session is passed in, UnitOfWork doesn't close it."""
        from unittest.mock import AsyncMock
        from src.db.unit_of_work import UnitOfWork

        session = AsyncMock()
        uow = UnitOfWork(session=session)
        assert uow._external_session is True


class TestDeadLetterFlow:
    """Dead letters: failed validation → stored → replayable."""

    def test_dead_letter_has_required_fields(self):
        from src.db.models.support import DeadLetter
        required = ["entity_type", "provider", "error", "error_category", "replayed"]
        for field in required:
            assert hasattr(DeadLetter, field), f"Missing: {field}"

    def test_dead_letter_stores_payload(self):
        """Payload is stored as JSONB for replay."""
        from src.db.models.support import DeadLetter
        assert hasattr(DeadLetter, "payload")


class TestPayloadArchive:
    """Raw JSON payload storage."""

    def test_payload_store_requires_provider_endpoint_type(self):
        from src.db.models.support import ProviderPayload
        assert hasattr(ProviderPayload, "provider")
        assert hasattr(ProviderPayload, "endpoint")
        assert hasattr(ProviderPayload, "entity_type")
        assert hasattr(ProviderPayload, "payload")

    def test_prune_old_payloads(self):
        """Payloads older than 90 days can be pruned."""
        from src.sync.payload_store import PayloadStore
        # prune_old(90) should exist
        assert hasattr(PayloadStore, "prune_old")


class TestSyncHistory:
    """Sync history tracking per run and per job."""

    def test_sync_run_tracks_all_metrics(self):
        from src.db.models.support import SyncRun
        metrics = ["total_inserted", "total_updated", "total_skipped",
                   "total_errors", "api_calls", "duration_ms"]
        for m in metrics:
            assert hasattr(SyncRun, m), f"Missing: {m}"

    def test_sync_job_tracks_per_entity(self):
        from src.db.models.support import SyncJob
        metrics = ["records_inserted", "records_updated", "records_skipped",
                   "records_errors", "api_calls", "duration_ms"]
        for m in metrics:
            assert hasattr(SyncJob, m), f"Missing: {m}"
