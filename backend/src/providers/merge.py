"""Cross-Provider Merge Logic.

Enforces fixed field authority as defined in DATA_CONTRACT.md.
Each field has exactly ONE authoritative provider. Enrichment providers
can fill gaps but NEVER overwrite authoritative data.

Field Authority Categories:
1. ESPN-OWNED: Never overwritten. Octagon/TSDB can only fill if NULL.
2. OCTAGON-OWNED: Set by Octagon, not touched by TSDB.
3. TSDB-OWNED: Set by TSDB, not touched by Octagon.
4. GAP-FILL: Fill from any source if the authoritative source has NULL.

Strategy:
- ESPN fields → NEVER overwrite (even if NULL, ESPN NULL is authoritative)
- Octagon enrichment → fill ONLY if ESPN has NULL (gap-fill), or if Octagon-owned
- TSDB enrichment → fill ONLY for TSDB-owned fields (media, bios, social)
"""

from enum import Enum
from typing import Any


class FieldCategory(Enum):
    ESPN_AUTHORITY = "espn"       # ESPN owns this field — never overwrite
    OCTAGON_AUTHORITY = "octagon" # Octagon owns this field
    TSDB_AUTHORITY = "tsdb"       # TSDB owns this field
    GAP_FILL = "gap_fill"        # Fill from any source if authoritative is NULL


# ── Field Authority Map (per DATA_CONTRACT.md) ─────────────────────────────────

PROMOTION_AUTHORITY: dict[str, FieldCategory] = {
    "name": FieldCategory.ESPN_AUTHORITY,
    "short_name": FieldCategory.ESPN_AUTHORITY,
    "abbreviation": FieldCategory.ESPN_AUTHORITY,
    "slug": FieldCategory.ESPN_AUTHORITY,
    "display_name": FieldCategory.ESPN_AUTHORITY,
    "season_year": FieldCategory.ESPN_AUTHORITY,
    "gender": FieldCategory.ESPN_AUTHORITY,
    # TSDB-owned media fields
    "logo_url": FieldCategory.TSDB_AUTHORITY,
    "poster_url": FieldCategory.TSDB_AUTHORITY,
    "banner_url": FieldCategory.TSDB_AUTHORITY,
    "trophy_url": FieldCategory.TSDB_AUTHORITY,
    "fanart_urls": FieldCategory.TSDB_AUTHORITY,
    "website": FieldCategory.TSDB_AUTHORITY,
    "facebook_url": FieldCategory.TSDB_AUTHORITY,
    "instagram_url": FieldCategory.TSDB_AUTHORITY,
    "twitter_url": FieldCategory.TSDB_AUTHORITY,
    "youtube_url": FieldCategory.TSDB_AUTHORITY,
    "description": FieldCategory.TSDB_AUTHORITY,
    "tv_rights": FieldCategory.TSDB_AUTHORITY,
    "country": FieldCategory.TSDB_AUTHORITY,
    "founded_year": FieldCategory.TSDB_AUTHORITY,
    "first_event_date": FieldCategory.TSDB_AUTHORITY,
}

FIGHTER_AUTHORITY: dict[str, FieldCategory] = {
    # ESPN-owned — NEVER overwrite
    "first_name": FieldCategory.ESPN_AUTHORITY,
    "last_name": FieldCategory.ESPN_AUTHORITY,
    "full_name": FieldCategory.ESPN_AUTHORITY,
    "short_name": FieldCategory.ESPN_AUTHORITY,
    "slug": FieldCategory.ESPN_AUTHORITY,
    "weight_kg": FieldCategory.ESPN_AUTHORITY,
    "height_cm": FieldCategory.ESPN_AUTHORITY,
    "reach_cm": FieldCategory.ESPN_AUTHORITY,
    "stance": FieldCategory.ESPN_AUTHORITY,
    "nationality": FieldCategory.ESPN_AUTHORITY,
    "birth_date": FieldCategory.ESPN_AUTHORITY,
    "is_active": FieldCategory.ESPN_AUTHORITY,
    "record_wins": FieldCategory.ESPN_AUTHORITY,
    "record_losses": FieldCategory.ESPN_AUTHORITY,
    "record_draws": FieldCategory.ESPN_AUTHORITY,
    "record_no_contests": FieldCategory.ESPN_AUTHORITY,
    "weight_class_name": FieldCategory.ESPN_AUTHORITY,
    # Octagon-owned — unique enrichment fields
    "leg_reach_cm": FieldCategory.OCTAGON_AUTHORITY,
    "trains_at": FieldCategory.OCTAGON_AUTHORITY,
    "fighting_style": FieldCategory.OCTAGON_AUTHORITY,
    "debut_date": FieldCategory.OCTAGON_AUTHORITY,
    "age": FieldCategory.OCTAGON_AUTHORITY,
    # Octagon-primary (higher coverage than TSDB)
    "nickname": FieldCategory.OCTAGON_AUTHORITY,
    "birth_location": FieldCategory.OCTAGON_AUTHORITY,
    "headshot_url": FieldCategory.OCTAGON_AUTHORITY,
    # TSDB-owned media/bio fields
    "cutout_url": FieldCategory.TSDB_AUTHORITY,
    "render_url": FieldCategory.TSDB_AUTHORITY,
    "biography": FieldCategory.TSDB_AUTHORITY,
    "ethnicity": FieldCategory.TSDB_AUTHORITY,
    "wikidata_id": FieldCategory.TSDB_AUTHORITY,
    "facebook_url": FieldCategory.TSDB_AUTHORITY,
    "instagram_url": FieldCategory.TSDB_AUTHORITY,
    "twitter_url": FieldCategory.TSDB_AUTHORITY,
}

EVENT_AUTHORITY: dict[str, FieldCategory] = {
    "name": FieldCategory.ESPN_AUTHORITY,
    "short_name": FieldCategory.ESPN_AUTHORITY,
    "slug": FieldCategory.ESPN_AUTHORITY,
    "date_utc": FieldCategory.ESPN_AUTHORITY,
    "status": FieldCategory.ESPN_AUTHORITY,
    "season": FieldCategory.ESPN_AUTHORITY,
    "venue_id": FieldCategory.ESPN_AUTHORITY,
    "promotion_id": FieldCategory.ESPN_AUTHORITY,
    # TSDB-owned
    "poster_url": FieldCategory.TSDB_AUTHORITY,
    "square_url": FieldCategory.TSDB_AUTHORITY,
    "fanart_url": FieldCategory.TSDB_AUTHORITY,
    "thumbnail_url": FieldCategory.TSDB_AUTHORITY,
    "banner_url": FieldCategory.TSDB_AUTHORITY,
    "description": FieldCategory.TSDB_AUTHORITY,
    "spectators": FieldCategory.TSDB_AUTHORITY,
    "time_local": FieldCategory.TSDB_AUTHORITY,
    "time_utc": FieldCategory.TSDB_AUTHORITY,
    "venue_name_inline": FieldCategory.TSDB_AUTHORITY,
    "city_inline": FieldCategory.TSDB_AUTHORITY,
    "country_inline": FieldCategory.TSDB_AUTHORITY,
}

AUTHORITY_MAP = {
    "promotions": PROMOTION_AUTHORITY,
    "fighters": FIGHTER_AUTHORITY,
    "events": EVENT_AUTHORITY,
}


# ── Merge Logic ───────────────────────────────────────────────────────────────

async def merge_record(
    db: Any,
    table: str,
    entity_id: str,
    enrichment: dict[str, Any],
    source: str,
) -> int:
    """Merge enrichment fields into an existing record.

    Follows fixed field authority:
    - ESPN-owned fields are NEVER modified (skipped silently)
    - Provider-owned fields are set unconditionally
    - GAP_FILL fields are set only if current value is NULL

    Args:
        db: Database session (AsyncSession).
        table: Table name ("promotions", "fighters", "events").
        entity_id: Internal record ID or external_id.
        enrichment: Dict of field_name → value.
        source: Provider slug ("tsdb" or "octagon").

    Returns:
        Number of fields actually updated.
    """
    authority_map = AUTHORITY_MAP.get(table, {})
    if not authority_map:
        return 0

    allowed_fields: dict[str, Any] = {}

    for field, value in enrichment.items():
        if value is None:
            continue

        category = authority_map.get(field)

        if category is None:
            # Unknown field — skip (safety: don't write unmapped fields)
            continue

        if category == FieldCategory.ESPN_AUTHORITY:
            # ESPN fields are NEVER modified by enrichment providers
            continue

        if category.value == source or category == FieldCategory.GAP_FILL:
            # Source-matching or gap-fill: set the value
            allowed_fields[field] = value
        elif category == FieldCategory.OCTAGON_AUTHORITY and source == "tsdb":
            # TSDB can't set Octagon-owned fields
            continue
        elif category == FieldCategory.TSDB_AUTHORITY and source == "octagon":
            # Octagon can't set TSDB-owned fields
            continue
        else:
            allowed_fields[field] = value

    if not allowed_fields:
        return 0

    # Execute update — caller provides the actual DB update mechanism
    # For now, return the count of fields that would be updated
    return await _execute_merge(db, table, entity_id, allowed_fields)


async def _execute_merge(
    db: Any,
    table: str,
    entity_id: str,
    fields: dict[str, Any],
) -> int:
    """Execute the actual database UPDATE.

    This is a placeholder — in production, this would execute:
        UPDATE {table} SET {fields} WHERE id = {entity_id}
    """
    # Production implementation:
    # stmt = update(table).where(table.c.id == entity_id).values(**fields)
    # await db.execute(stmt)
    return len(fields)
