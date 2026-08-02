"""Conflict Detection — tracks provider disagreements.

When ESPN says 178cm and Octagon says 180cm, we store the conflict
and apply the authority rule. Conflicts are resolved, never pending.
"""

import logging
from datetime import datetime
from typing import Any

logger = logging.getLogger(__name__)


class ConflictTracker:
    """Tracks and stores provider conflicts in provider_conflicts table."""

    def __init__(self, session):
        self._session = session

    async def record_conflict(
        self,
        entity_type: str,
        entity_id: str,
        field: str,
        value_a: Any,
        value_b: Any,
        provider_a: str,
        provider_b: str,
        chosen_authority: str,
        chosen_value: Any,
    ) -> None:
        """Record a disagreement between two providers."""
        from sqlalchemy.dialects.postgresql import insert
        from src.db.models.support import ProviderConflict

        values = {
            "entity_type": entity_type,
            "entity_id": entity_id,
            "field": field,
            "provider_a": provider_a,
            "provider_b": provider_b,
            "value_a": str(value_a) if value_a is not None else None,
            "value_b": str(value_b) if value_b is not None else None,
            "chosen_authority": chosen_authority,
            "chosen_value": str(chosen_value) if chosen_value is not None else None,
            "resolution": "AUTHORITY",
            "resolved": True,
        }

        stmt = insert(ProviderConflict).values(**values)
        await self._session.execute(stmt)

        logger.debug(
            f"Conflict recorded: {entity_type}.{field} — "
            f"{provider_a}={value_a} vs {provider_b}={value_b} → "
            f"chose {chosen_authority}={chosen_value}"
        )

    async def get_unresolved(self, entity_type: str | None = None) -> list:
        """Get unresolved conflicts — for manual review."""
        from sqlalchemy import select
        from src.db.models.support import ProviderConflict

        q = select(ProviderConflict).where(ProviderConflict.resolved == False)
        if entity_type:
            q = q.where(ProviderConflict.entity_type == entity_type)

        result = await self._session.execute(q)
        return list(result.scalars().all())

    async def resolve_conflict(self, conflict_id: str, chosen_value: str) -> None:
        """Manually resolve a conflict."""
        from sqlalchemy import update
        from src.db.models.support import ProviderConflict

        await self._session.execute(
            update(ProviderConflict)
            .where(ProviderConflict.id == conflict_id)
            .values(resolution="MANUAL", chosen_value=chosen_value, resolved=True)
        )
