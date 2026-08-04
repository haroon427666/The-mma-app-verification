"""Common Pydantic models — pagination, errors, enums."""

from datetime import UTC, datetime
from typing import TypeVar

from pydantic import BaseModel, Field

# ── Pagination ──────────────────────────────────────────────────────────────

T = TypeVar("T")


class PaginationParams(BaseModel):
    page: int = Field(1, ge=1, description="Page number (1-based)")
    limit: int = Field(50, ge=1, le=200, description="Items per page (max 200)")


class PaginatedResponse[T](BaseModel):
    items: list[T]
    total: int
    page: int
    limit: int
    pages: int

    @classmethod
    def from_query(cls, items: list[T], total: int, params: PaginationParams) -> "PaginatedResponse[T]":
        return cls(
            items=items,
            total=total,
            page=params.page,
            limit=params.limit,
            pages=(total + params.limit - 1) // params.limit,
        )


# ── Sorting ─────────────────────────────────────────────────────────────────

class SortParams(BaseModel):
    sort_by: str | None = Field(None, description="Field to sort by")
    sort_dir: str = Field("asc", pattern="^(asc|desc)$", description="Sort direction")


# ── Filters ─────────────────────────────────────────────────────────────────

class FighterFilters(BaseModel):
    weight_class: str | None = None
    country: str | None = None
    active: bool | None = True
    ranked: bool | None = None
    promotion_slug: str | None = None
    stance: str | None = None
    gym: str | None = None
    style: str | None = None
    search: str | None = Field(None, description="Search by name or nickname")


class EventFilters(BaseModel):
    status: str | None = Field(None, description="SCHEDULED, IN_PROGRESS, FINAL, CANCELLED")
    promotion_slug: str | None = None
    year: int | None = None
    country: str | None = None
    city: str | None = None
    search: str | None = None


class FightFilters(BaseModel):
    status: str | None = None
    weight_class: str | None = None
    event_id: str | None = None
    fighter_id: str | None = None
    outcome: str | None = Field(None, description="WIN, LOSS, DRAW, NC")
    method: str | None = Field(None, description="KO/TKO, Submission, Decision")
    card_segment: str | None = None


class RankingFilters(BaseModel):
    division: str | None = None
    gender: str | None = Field(None, description="MALE, FEMALE")


# ── Error Response ──────────────────────────────────────────────────────────

class ErrorDetail(BaseModel):
    field: str | None = None
    message: str
    type: str = "error"


class ErrorResponse(BaseModel):
    error: str
    code: int
    details: list[ErrorDetail] | None = None
    timestamp: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())

    @classmethod
    def not_found(cls, entity: str, identifier: str = "") -> "ErrorResponse":
        return cls(error=f"{entity} not found", code=404,
                   details=[ErrorDetail(message=f"No {entity} found{f' for: {identifier}' if identifier else ''}")])

    @classmethod
    def bad_request(cls, message: str) -> "ErrorResponse":
        return cls(error="Bad request", code=400, details=[ErrorDetail(message=message)])


# ── Enums ───────────────────────────────────────────────────────────────────

from enum import Enum as PyEnum


class Stance(str, PyEnum):
    orthodox = "Orthodox"
    southpaw = "Southpaw"
    switch = "Switch"
    open_stance = "Open Stance"


class EventStatus(str, PyEnum):
    scheduled = "SCHEDULED"
    in_progress = "IN_PROGRESS"
    final = "FINAL"
    cancelled = "CANCELLED"


class FightOutcome(str, PyEnum):
    win = "WIN"
    loss = "LOSS"
    draw = "DRAW"
    nc = "NC"
    dq = "DQ"


class FightMethod(str, PyEnum):
    ko_tko = "KO/TKO"
    submission = "Submission"
    decision_unanimous = "Decision - Unanimous"
    decision_split = "Decision - Split"
    decision_majority = "Decision - Majority"
    dq = "DQ"
    no_contest = "No Contest"


class CardSegment(str, PyEnum):
    main_card = "Main Card"
    prelims = "Prelims"
    early_prelims = "Early Prelims"


class Corner(str, PyEnum):
    red = "RED"
    blue = "BLUE"
