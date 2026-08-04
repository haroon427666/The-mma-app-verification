"""BaseUpsert — abstract base for all entity upsert services.

Race-condition-safe: catches IntegrityError on concurrent inserts, re-resolves
the external ID, and applies the update instead.

N+1 safe: all external IDs resolved in a single bulk query.
Batch write: add_all() + flush() for single DB round-trip.

Every subclass defines FIELD_MAP: {dto_field: model_attribute} for automatic
change detection. No handwritten _changed_fields needed for standard fields.
"""

import logging
from abc import ABC, abstractmethod
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from src.sync.upsert import UpsertResult
from src.sync.upserts.id_resolver import IdResolver

logger = logging.getLogger(__name__)


class BaseUpsert(ABC):
    """Abstract base for entity-specific upsert services.

    FIELD_MAP drives automatic change detection and value application.
    Subclasses only implement: _model_class, _extract_external_id, _to_model.

    Race conditions: IntegrityError on insert → re-resolve → update.
    Cache: IdResolver cache is per-batch, cleared between runs.
    """

    entity_type: str = ""
    provider: str = "espn"
    FIELD_MAP: dict[str, str] = {}
    """{dto_field: model_attribute} — drives automatic change detection."""

    def __init__(self, resolver: IdResolver) -> None:
        self._resolver = resolver

    # ── Public API ──────────────────────────────────────────────────────────

    async def upsert(self, dto: Any) -> UpsertResult:
        return await self.upsert_batch([dto])

    async def upsert_batch(self, dtos: list[Any]) -> UpsertResult:
        """N+1 safe batch upsert.

        1. Bulk-resolve all external IDs (1 query)
        2. Split: inserts vs updates
        3. add_all + flush for inserts (1 DB round-trip)
        4. Per-row update for existing entities (changed fields only)
        5. IntegrityError on insert → re-resolve → update (race-safe)
        """
        if not dtos:
            return UpsertResult.empty()

        # 1. Bulk-resolve — single query
        external_ids = [self._extract_external_id(d) for d in dtos]
        external_ids = [eid for eid in external_ids if eid]
        existing_map = await self._resolver.resolve_bulk(
            self.provider, self.entity_type, external_ids
        )

        # 2. Split
        to_insert: list[tuple[str, Any]] = []
        to_update: list[tuple[UUID, Any]] = []
        for dto in dtos:
            eid = self._extract_external_id(dto)
            if not eid:
                continue
            euuid = existing_map.get(eid)
            if euuid is None:
                to_insert.append((eid, dto))
            else:
                to_update.append((euuid, dto))

        result = UpsertResult()

        # 3. Bulk insert
        if to_insert:
            result += await self._bulk_insert(to_insert)

        # 4. Per-row update
        for euuid, dto in to_update:
            try:
                changed, uid = await self._update_one(euuid, dto)
                if changed:
                    result.updated += 1
                    result.updated_ids.append(uid)
                else:
                    result.skipped += 1
                    result.skipped_ids.append(uid)
            except Exception as e:
                logger.error(f"Update failed {self.entity_type}/{euuid}: {e}")
                result.errors += 1
                result.error_details.append(str(e))

        return result

    # ── Bulk Insert ─────────────────────────────────────────────────────────

    async def _bulk_insert(
        self, to_insert: list[tuple[str, Any]]
    ) -> UpsertResult:
        """add_all + flush: single DB round-trip for all new entities.

        Race-safe: IntegrityError → rollback → retry each row individually.
        On retry: re-resolve (now it exists!) → update instead.
        """
        result = UpsertResult()
        eid_to_model: dict[str, Any] = {}

        for eid, dto in to_insert:
            model = self._to_model(dto)
            model.id = uuid4()
            self._resolver._db.add(model)
            eid_to_model[eid] = model

        try:
            await self._resolver._db.flush()
        except IntegrityError:
            # Concurrent worker inserted first → retry individually
            await self._resolver._db.rollback()
            logger.warning(
                f"Bulk insert conflict ({self.entity_type}) — "
                f"retrying {len(to_insert)} rows individually"
            )
            for eid, dto in to_insert:
                try:
                    result += await self._insert_with_race_retry(eid, dto)
                except Exception as e:
                    result.errors += 1
                    result.error_details.append(str(e))
            return result

        # Register external IDs
        for eid, model in eid_to_model.items():
            await self._resolver.register(
                self.provider, eid, self.entity_type, model.id
            )
            result.inserted += 1
            result.inserted_ids.append(model.id)

        await self._resolver.flush()
        return result

    async def _insert_with_race_retry(
        self, external_id: str, dto: Any
    ) -> UpsertResult:
        """Single-row insert with concurrent-write recovery.

        IntegrityError → re-resolve (other worker inserted) → update.
        """
        try:
            model = self._to_model(dto)
            model.id = uuid4()
            self._resolver._db.add(model)
            await self._resolver.register(
                self.provider, external_id, self.entity_type, model.id
            )
            await self._resolver._db.flush()
            return UpsertResult(inserted=1, inserted_ids=[model.id])
        except IntegrityError:
            await self._resolver._db.rollback()
            logger.info(
                f"Race resolved: {self.entity_type}/{external_id} "
                f"inserted concurrently — updating"
            )
            euuid = await self._resolver.resolve(
                self.provider, external_id, self.entity_type
            )
            if euuid is None:
                raise RuntimeError(
                    f"Re-resolve failed after IntegrityError: "
                    f"{self.entity_type}/{external_id}"
                )
            changed, uid = await self._update_one(euuid, dto)
            return UpsertResult(
                updated=1 if changed else 0,
                skipped=0 if changed else 1,
                updated_ids=[uid] if changed else [],
                skipped_ids=[uid] if not changed else [],
            )

    # ── Update ─────────────────────────────────────────────────────────────

    async def _update_one(self, euuid: UUID, dto: Any) -> tuple[bool, UUID]:
        """Update entity — only if fields changed. Returns (changed, uuid)."""
        existing = await self._load_existing(euuid)
        if existing is None:
            model = self._to_model(dto)
            model.id = euuid
            self._resolver._db.add(model)
            return True, euuid

        changed = self._changed_fields(existing, dto)
        if not changed:
            return False, euuid

        self._apply_changes(existing, dto, changed)
        self._resolver._db.add(existing)
        return True, euuid

    # ── Helpers ─────────────────────────────────────────────────────────────

    async def _load_existing(self, euuid: UUID) -> Any | None:
        result: Any = await self._resolver._db.execute(
            select(self._model_class).where(getattr(self._model_class, "id") == euuid)  # noqa: B009
        )
        return result.scalar_one_or_none()

    # ── FIELD_MAP-driven change detection ───────────────────────────────────

    def _changed_fields(self, existing: Any, dto: Any) -> set[str]:
        """Auto-detect changed fields from FIELD_MAP + _special_fields()."""
        changes: set[str] = set()
        for dto_field, model_attr in self.FIELD_MAP.items():
            if getattr(dto, dto_field, None) != getattr(existing, model_attr, None):
                changes.add(model_attr)
        changes |= self._special_fields(existing, dto)
        return changes

    def _apply_changes(self, model: Any, dto: Any, fields: set[str]) -> None:
        """Auto-apply changed fields from FIELD_MAP."""
        reverse = {v: k for k, v in self.FIELD_MAP.items()}
        for model_attr in fields:
            dto_field = reverse.get(model_attr)
            if dto_field:
                setattr(model, model_attr, getattr(dto, dto_field, None))
        self._apply_special_fields(model, dto, fields)

    # ── Override points ─────────────────────────────────────────────────────

    def _special_fields(self, existing: Any, dto: Any) -> set[str]:
        """Fields needing custom comparison (e.g. derived values)."""
        return set()

    def _apply_special_fields(self, model: Any, dto: Any, fields: set[str]) -> None:
        """Apply fields computed from DTO rather than direct mapping."""

    # ── Abstract ────────────────────────────────────────────────────────────

    @property
    @abstractmethod
    def _model_class(self) -> type:
        ...

    @abstractmethod
    def _extract_external_id(self, dto: Any) -> str:
        ...

    @abstractmethod
    def _to_model(self, dto: Any) -> Any:
        ...
