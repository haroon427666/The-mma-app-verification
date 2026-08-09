"""Shared API helpers."""

from uuid import UUID

from fastapi import HTTPException


def require_uuid(value: str) -> str:
    """Reject non-UUID ids early (404, not a DB-level 500).

    All entity id columns are UUIDs; feeding a non-UUID string to asyncpg
    raises a DataError that would surface as a 500.
    """
    try:
        return str(UUID(value))
    except ValueError:
        raise HTTPException(404, f"Invalid id: {value}")
