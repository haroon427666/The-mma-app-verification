"""Search API extensions — autocomplete, trending, popular, history."""

from typing import Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.session import get_session
from src.schemas.misc import SearchResultItem

router = APIRouter(prefix="/v1/search", tags=["search"])


@router.get("/autocomplete")
async def search_autocomplete(
    q: str = Query(..., min_length=2),
    limit: int = Query(10, le=20),
    session: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    """Autocomplete suggestions from fighter names."""
    from sqlalchemy import select as sa_select

    from src.db.models.fighter import Fighter
    result = await session.execute(
        sa_select(Fighter.full_name)
        .where(Fighter.full_name.ilike(f"%{q}%"))
        .limit(limit)
    )
    return {"query": q, "suggestions": [row[0] for row in result.all()]}


@router.get("/trending")
async def search_trending(
    limit: int = Query(10, le=20),
    session: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    """Trending searches (simplified — returns recently synced fighters)."""
    from sqlalchemy import desc
    from sqlalchemy import select as sa_select

    from src.db.models.fighter import Fighter
    result = await session.execute(
        sa_select(Fighter.full_name, Fighter.headshot_url, Fighter.weight_class_name)
        .where(Fighter.is_active == True)
        .order_by(desc(Fighter.synced_at))
        .limit(limit)
    )
    items = []
    for row in result.all():
        items.append(SearchResultItem(
            id=f"fighter:{row[0]}", type="fighter", name=row[0],
            subtitle=row[2], image_url=row[1], relevance=0.85,
        ))
    return {"trending": [i.model_dump() for i in items]}


@router.get("/popular")
async def search_popular(
    limit: int = Query(10, le=20),
    session: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    """Popular searches (simplified — returns top weight class names)."""
    from sqlalchemy import func
    from sqlalchemy import select as sa_select

    from src.db.models.fighter import Fighter
    result = await session.execute(
        sa_select(Fighter.weight_class_name, func.count(Fighter.id).label("cnt"))
        .where(Fighter.weight_class_name.isnot(None))
        .group_by(Fighter.weight_class_name)
        .order_by(func.count(Fighter.id).desc())
        .limit(limit)
    )
    return {"popular": [row[0] for row in result.all()]}


@router.get("/history")
async def search_history() -> dict[str, Any]:
    """Recent searches — client-side only. Returns empty list for now."""
    return {"history": []}


@router.delete("/history")
async def clear_search_history() -> dict[str, Any]:
    """Clear recent searches — client-side only."""
    return {"status": "cleared"}
