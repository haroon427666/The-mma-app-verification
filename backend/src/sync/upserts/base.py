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
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from src.db.models import WeightClass
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
        self._wc_cache: dict[str, str] = {}

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
        to_update: list[tuple[str, str, Any]] = []
        for dto in dtos:
            eid = self._extract_external_id(dto)
            if not eid:
                continue
            euuid = existing_map.get(eid)
            if euuid is None:
                to_insert.append((eid, dto))
            else:
                to_update.append((eid, euuid, dto))

        result = UpsertResult()

        # 3. Bulk insert
        if to_insert:
            result += await self._bulk_insert(to_insert)

        # 4. Per-row update
        for eid, euuid, dto in to_update:
            try:
                changed, uid = await self._update_one(euuid, dto, eid)
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
            try:
                model = self._prepare_new(self._to_model(dto), eid)
                await self._enrich_model(model, dto)
            except Exception as e:
                logger.error(f"Insert skipped {self.entity_type}/{eid}: {e}")
                result.errors += 1
                result.error_details.append(str(e))
                continue
            model.id = str(uuid4())
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
            model = self._prepare_new(self._to_model(dto), external_id)
            await self._enrich_model(model, dto)
            model.id = str(uuid4())
            self._resolver._db.add(model)
            await self._resolver.register(
                self.provider, external_id, self.entity_type, model.id
            )
            await self._resolver._db.flush()
            return UpsertResult(inserted=1, inserted_ids=[model.id])
        except IntegrityError:
            await self._resolver._db.rollback()
            self._resolver._cache.pop(
                (self.provider, external_id, self.entity_type), None
            )
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
            changed, uid = await self._update_one(euuid, dto, external_id)
            return UpsertResult(
                updated=1 if changed else 0,
                skipped=0 if changed else 1,
                updated_ids=[uid] if changed else [],
                skipped_ids=[uid] if not changed else [],
            )

    # ── Update ─────────────────────────────────────────────────────────────

    async def _update_one(
        self, euuid: str, dto: Any, external_id: str
    ) -> tuple[bool, str]:
        """Update entity — only if fields changed. Returns (changed, uuid)."""
        existing = await self._load_existing(euuid)
        if existing is None:
            model = self._prepare_new(self._to_model(dto), external_id)
            await self._enrich_model(model, dto)
            model.id = str(euuid)
            self._resolver._db.add(model)
            return True, euuid

        changed = self._changed_fields(existing, dto)
        if not changed:
            return False, euuid

        self._apply_changes(existing, dto, changed)
        self._resolver._db.add(existing)
        return True, euuid

    # ── Helpers ─────────────────────────────────────────────────────────────

    def _prepare_new(self, model: Any, external_id: str) -> Any:
        """Set insert-time identity on a new model.

        Entity models carry NOT NULL provider/external_id columns, but DTOs only
        carry the external ID and _to_model implementations don't fill them.
        Populate both from the upsert's provider + the extracted external ID,
        without clobbering values a subclass already set.
        """
        if getattr(model, "external_id", None) is None:
            model.external_id = external_id
        if getattr(model, "provider", None) is None:
            model.provider = self.provider
        return model

    async def _load_existing(self, euuid: str) -> Any | None:
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

    async def _ensure_weight_class(
        self, external_id: str, name: str
    ) -> str | None:
        """Resolve a weight class external id, creating the row when missing.

        Weight classes arrive as INLINE data on fighters and competitions
        (e.g. {id: 970, text: "Bantamweight"}), so the weight_class sync job
        has nothing to fetch. This helper lazily materializes the row on
        first use and registers it in the resolver so later rows in the same
        batch resolve without further lookups.
        """
        if not external_id or not name:
            return None

        uuid_val = await self._resolver.resolve(
            self.provider, external_id, "weight_class"
        )
        if uuid_val:
            return uuid_val
        if name in self._wc_cache:
            return self._wc_cache[name]

        existing = await self._resolver._db.execute(
            select(WeightClass).where(
                WeightClass.provider == self.provider,
                WeightClass.name == name,
            )
        )
        wc = existing.scalar_one_or_none()
        if wc is None:
            wc = WeightClass(
                provider=self.provider,
                external_id=external_id,
                name=name,
            )
            wc.id = str(uuid4())
            self._resolver._db.add(wc)
            wc_uuid = str(wc.id)
        else:
            wc_uuid = str(wc.id)

        await self._resolver.register(
            self.provider, external_id, "weight_class", wc_uuid
        )
        self._wc_cache[name] = wc_uuid
        return wc_uuid

    async def _enrich_model(self, model: Any, dto: Any) -> None:
        """Resolve FK/derived fields on a new model before insert.

        Runs after _to_model on every insert path (bulk, race-retry, and the
        missing-existing update branch). Default: no-op. Subclasses override to
        resolve external references via the IdResolver (e.g. an event DTO's
        promotion_external_id → promotions.id). Raise to skip the row (counted
        as an error) or to fail the batch.
        """

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
