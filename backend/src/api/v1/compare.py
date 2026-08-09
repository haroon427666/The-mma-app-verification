"""Compare API — v1. Two-fighter comparison in a single call (FTR-1905/1906/1907).

Serves the `mma://compare/:idA/:idB` deeplink target (T15 decision): keep the
deeplink, back it with a real lightweight endpoint — two fighter summaries +
head-to-head bouts + common opponents, per the data-spec "compare payload
incl. common opponents".
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response

from src.api.cache import cache_key, cached_json_response
from src.api.utils import require_uuid
from src.api.v1.fighters import _fighter_to_list_item
from src.db.unit_of_work import UnitOfWork
from src.dependencies import get_uow
from src.schemas.common import ErrorResponse
from src.schemas.fighter import (
    CommonOpponentEntry,
    CompareBoutEntry,
    CompareResponse,
)
from src.services.fighter_service import FighterService

router = APIRouter(prefix="/v1/compare", tags=["compare"])


@router.get("", response_model=CompareResponse, responses={404: {"model": ErrorResponse}})
async def compare_fighters(
    request: Request,
    a: str = Query(..., description="Fighter A id"),
    b: str = Query(..., description="Fighter B id"),
    uow: UnitOfWork = Depends(get_uow),
) -> Response:
    """Compare two fighters in one call: summaries, head-to-head, common opponents.

    Both `a` and `b` must be UUIDs of existing fighters. Comparing a fighter
    with themselves is rejected (422).
    """
    require_uuid(a)
    require_uuid(b)
    if a == b:
        raise HTTPException(422, "Cannot compare a fighter with themselves")
    svc = FighterService(uow)

    async def loader() -> dict:
        fa = await svc._uow.fighters.get_by_id(a)
        if fa is None:
            raise HTTPException(404, detail=ErrorResponse.not_found("fighter", a).error)
        fb = await svc._uow.fighters.get_by_id(b)
        if fb is None:
            raise HTTPException(404, detail=ErrorResponse.not_found("fighter", b).error)

        data = await svc.compare_fighters(a, b)
        return CompareResponse(
            a=_fighter_to_list_item(fa),
            b=_fighter_to_list_item(fb),
            head_to_head=[CompareBoutEntry(**entry) for entry in data["head_to_head"]],
            common_opponents=[
                CommonOpponentEntry(
                    id=o["fighter"].id,
                    name=f"{o['fighter'].first_name} {o['fighter'].last_name}",
                    headshot_url=o["fighter"].headshot_url,
                    record=(
                        f"{o['fighter'].record_wins or 0}-{o['fighter'].record_losses or 0}"
                        f"-{o['fighter'].record_draws or 0}"
                    ),
                    vs_a=o["vs_a"],
                    vs_b=o["vs_b"],
                )
                for o in data["common_opponents"]
            ],
        ).model_dump(mode="json")

    return await cached_json_response(
        request,
        cache_key=cache_key("compare", a, b),
        ttl=3600,
        loader=loader,
    )
