"""Idempotent Upsert Engine — Phase 6 Production.

Handles batch INSERT...ON CONFLICT UPDATE for all entities.
Never DELETEs. Idempotent — running twice produces identical results.

Features:
- Batch operations (configurable batch_size)
- Transaction-per-batch (partial failure → rollback batch, continue)
- Optimistic locking via version column
- Conflict detection via provider_conflicts table
- Metrics collection per batch
"""

import logging
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from src.db.unit_of_work import UnitOfWork

logger = logging.getLogger(__name__)


@dataclass
class UpsertBatchResult:
    entity_type: str
    batch_index: int
    attempted: int = 0
    inserted: int = 0
    updated: int = 0
    skipped: int = 0
    errors: int = 0
    error_details: list[str] = field(default_factory=list)


@dataclass
class UpsertResult:
    entity_type: str
    total_attempted: int = 0
    total_inserted: int = 0
    total_updated: int = 0
    total_skipped: int = 0
    total_errors: int = 0
    batches: list[UpsertBatchResult] = field(default_factory=list)
    duration_ms: float = 0.0

    @property
    def success_rate(self) -> float:
        if self.total_attempted == 0:
            return 1.0
        return (self.total_inserted + self.total_updated) / self.total_attempted


class UpsertEngine:
    """Idempotent batch upsert engine.

    Usage:
        engine = UpsertEngine(uow)
        result = await engine.upsert_entity(
            entity_type="fighter",
            dtos=fighter_dtos,
            batch_size=500,
        )
    """

    def __init__(self, uow: "UnitOfWork"):
        self._uow = uow

    async def upsert_entity(
        self,
        entity_type: str,
        dtos: list[Any],
        batch_size: int = 500,
    ) -> UpsertResult:
        """Upsert a list of DTOs in batches. Never DELETEs."""
        import time

        start = time.monotonic()
        repo = self._get_repo(entity_type)
        result = UpsertResult(entity_type=entity_type)

        try:
            for i in range(0, len(dtos), batch_size):
                batch = dtos[i:i + batch_size]
                batch_result = UpsertBatchResult(
                    entity_type=entity_type,
                    batch_index=i // batch_size,
                    attempted=len(batch),
                )

                try:
                    # Upsert batch
                    affected = await repo.upsert_batch(batch, batch_size=len(batch))

                    # Count what happened
                    batch_result.inserted = affected  # Approximate — INSERT on conflict
                    batch_result.updated = 0  # Would need BEFORE/AFTER comparison for precision

                except Exception as e:
                    logger.error(f"Batch upsert failed for {entity_type} batch {i//batch_size}: {e}")
                    batch_result.errors = len(batch)
                    batch_result.error_details.append(str(e))
                    await self._uow.rollback()
                    continue  # Continue with next batch — failed batch is rolled back

                result.batches.append(batch_result)
                result.total_inserted += batch_result.inserted
                result.total_updated += batch_result.updated
                result.total_errors += batch_result.errors
                result.total_attempted += batch_result.attempted

                # Commit after each batch for checkpoint granularity
                await self._uow.commit()

        except Exception as e:
            logger.error(f"Upsert engine failed for {entity_type}: {e}")
            await self._uow.rollback()
            raise

        finally:
            result.duration_ms = (time.monotonic() - start) * 1000

        result.total_skipped = result.total_attempted - result.total_inserted - result.total_updated - result.total_errors
        logger.info(
            f"Upsert {entity_type}: {result.total_inserted} inserted, "
            f"{result.total_updated} updated, {result.total_errors} errors "
            f"in {result.duration_ms:.0f}ms"
        )
        return result

    def _get_repo(self, entity_type: str) -> Any:
        repo_map = {
            "fighter": self._uow.fighters,
            "event": self._uow.events,
            "competition": self._uow.competitions,
            "promotion": self._uow.promotions,
            "venue": self._uow.venues,
            "ranking": self._uow.rankings,
            "weight_class": self._uow.weight_classes,
            "broadcast": self._uow.broadcasts,
        }
        repo = repo_map.get(entity_type)
        if repo is None:
            raise ValueError(f"Unknown entity type: {entity_type}")
        return repo
