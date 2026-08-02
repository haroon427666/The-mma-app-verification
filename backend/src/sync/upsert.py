"""UpsertResult — standard return type for upsert services.

Every upsert service in Phase 3.2 returns an UpsertResult.
Carries both counts AND IDs for debugging and audit trails.
"""

from dataclasses import dataclass, field
from uuid import UUID


@dataclass
class UpsertResult:
    """Result of a single upsert batch operation.

    All upsert services return this type.
    The pipeline aggregates these into JobResult totals.
    """

    inserted: int = 0
    updated: int = 0
    skipped: int = 0
    errors: int = 0

    # IDs for debugging / audit trails
    inserted_ids: list[UUID] = field(default_factory=list)
    """UUIDs of entities that were created in this batch."""

    updated_ids: list[UUID] = field(default_factory=list)
    """UUIDs of entities that had changes applied."""

    skipped_ids: list[UUID] = field(default_factory=list)
    """UUIDs of entities that were unchanged (no fields differed)."""

    error_details: list[str] = field(default_factory=list)
    """Error messages for failed operations."""

    def to_dict(self) -> dict:
        return {
            "inserted": self.inserted,
            "updated": self.updated,
            "skipped": self.skipped,
            "errors": self.errors,
            "inserted_ids": [str(i) for i in self.inserted_ids],
            "updated_ids": [str(i) for i in self.updated_ids],
            "skipped_ids": [str(i) for i in self.skipped_ids],
        }

    @classmethod
    def empty(cls) -> "UpsertResult":
        return cls()

    def __add__(self, other: "UpsertResult") -> "UpsertResult":
        return UpsertResult(
            inserted=self.inserted + other.inserted,
            updated=self.updated + other.updated,
            skipped=self.skipped + other.skipped,
            errors=self.errors + other.errors,
            inserted_ids=self.inserted_ids + other.inserted_ids,
            updated_ids=self.updated_ids + other.updated_ids,
            skipped_ids=self.skipped_ids + other.skipped_ids,
            error_details=self.error_details + other.error_details,
        )
