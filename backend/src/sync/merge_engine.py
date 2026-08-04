"""Merge Engine — Cross-provider field authority enforcement.

Enforces DATA_CONTRACT.md field authority rules at write time.
ESPN fields are NEVER overwritten. Octagon/TSDB fill gaps only.

Usage:
    engine = MergeEngine(uow)
    conflicts = await engine.merge_fighter(fighter_id, enrichment, source="octagon")
"""

import logging
from dataclasses import dataclass
from dataclasses import field as dc_field
from enum import Enum
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from src.db.unit_of_work import UnitOfWork

from src.providers.merge import AUTHORITY_MAP, FieldCategory

logger = logging.getLogger(__name__)


class MergeAction(Enum):
    SET = "set"
    SKIP_ESPN = "skip_espn_owned"
    SKIP_WRONG_PROVIDER = "skip_wrong_provider"
    CONFLICT = "conflict"
    NO_CHANGE = "no_change"


@dataclass
class MergeConflict:
    field: str
    current_value: Any
    proposed_value: Any
    current_provider: str
    proposed_provider: str
    authority: str
    resolution: str = "AUTHORITY"


@dataclass
class MergeResult:
    entity_type: str
    entity_id: str
    source: str
    fields_set: int = 0
    fields_skipped: int = 0
    conflicts: list[MergeConflict] = dc_field(default_factory=list)


class MergeEngine:
    """Enforces field authority during enrichment merges."""

    def __init__(self, uow: "UnitOfWork"):
        self._uow = uow
        self._conflict_repo = None  # Will be set when DB is available

    async def merge_fighter(
        self,
        fighter_id: str,
        enrichment: dict[str, Any],
        source: str,
    ) -> MergeResult:
        """Merge enrichment fields into a fighter. Enforces authority."""
        return await self._merge("fighters", fighter_id, enrichment, source)

    async def merge_event(
        self,
        event_id: str,
        enrichment: dict[str, Any],
        source: str,
    ) -> MergeResult:
        return await self._merge("events", event_id, enrichment, source)

    async def merge_promotion(
        self,
        promotion_id: str,
        enrichment: dict[str, Any],
        source: str,
    ) -> MergeResult:
        return await self._merge("promotions", promotion_id, enrichment, source)

    async def _merge(
        self,
        table: str,
        entity_id: str,
        enrichment: dict[str, Any],
        source: str,
    ) -> MergeResult:
        authority_map = AUTHORITY_MAP.get(table, {})
        result = MergeResult(entity_type=table, entity_id=entity_id, source=source)

        fields_to_set: dict[str, Any] = {}

        for field, value in enrichment.items():
            if value is None:
                result.fields_skipped += 1
                continue

            category = authority_map.get(field)
            if category is None:
                # Unknown field — skip (safety)
                result.fields_skipped += 1
                continue

            action = self._decide_action(field, category, source)
            if action == MergeAction.SET:
                fields_to_set[field] = value
                result.fields_set += 1
            elif action == MergeAction.CONFLICT:
                result.conflicts.append(MergeConflict(
                    field=field,
                    current_value=None,  # Would need to read current value
                    proposed_value=value,
                    current_provider="espn",
                    proposed_provider=source,
                    authority="espn",
                ))
                result.fields_skipped += 1
            else:
                result.fields_skipped += 1

        if fields_to_set:
            repo = self._get_repo(table)
            await repo.update_fields(entity_id, **fields_to_set)

        return result

    def _decide_action(
        self, field: str, category: FieldCategory, source: str,
    ) -> MergeAction:
        """Decide what to do with a field from a given source."""
        if category == FieldCategory.ESPN_AUTHORITY:
            return MergeAction.SKIP_ESPN

        if category.value == source:
            return MergeAction.SET

        # Cross-provider: only set if the owning provider
        if category == FieldCategory.OCTAGON_AUTHORITY:
            if source == "octagon":
                return MergeAction.SET
            return MergeAction.SKIP_WRONG_PROVIDER

        if category == FieldCategory.TSDB_AUTHORITY:
            if source == "tsdb":
                return MergeAction.SET
            return MergeAction.SKIP_WRONG_PROVIDER

        if category == FieldCategory.GAP_FILL:
            return MergeAction.SET  # Any provider can fill gaps

        return MergeAction.SKIP_WRONG_PROVIDER

    def _get_repo(self, table: str) -> Any:
        repo_map = {
            "fighters": self._uow.fighters,
            "events": self._uow.events,
            "promotions": self._uow.promotions,
        }
        return repo_map.get(table)
