"""
ESPN Promotion (League) Parser — VERIFIED against live API 2026-08-01.

League response (VERIFIED):
{
    "id": "3321", "name": "Ultimate Fighting Championship",
    "displayName": "UFC", "abbreviation": "UFC", "slug": "ufc",
    "season": {"year": 2026},
    "logos": [{"href": "https://a.espncdn.com/.../500/ufc.png"}],
    "gender": "MALE"
}

NOTE: List endpoint returns items as $ref URLs. Each must be resolved.
This parser handles the RESOLVED league detail.
"""

from src.providers.dto import PromotionDTO


def parse_promotion(data: dict) -> PromotionDTO:
    """Parse a resolved ESPN league resource → PromotionDTO.

    Args:
        data: Raw JSON from GET /leagues/{slug}?lang=en&region=us

    Returns:
        PromotionDTO.
    """
    external_id = str(data.get("id", ""))
    name = data.get("name", "") or data.get("displayName", "")
    slug = data.get("slug", "") or name.lower().replace(" ", "-")

    country = None
    address = data.get("address", {})
    if isinstance(address, dict):
        country = address.get("country")

    # Logo — first logo in the logos array
    logo_url = None
    logos = data.get("logos", []) or []
    if logos and isinstance(logos, list):
        first = logos[0]
        if isinstance(first, dict):
            logo_url = first.get("href")

    # Season year — key signal for active/dead orgs
    season_year = None
    season = data.get("season", {})
    if isinstance(season, dict):
        season_year = season.get("year")

    return PromotionDTO(
        provider="espn",
        external_id=external_id,
        name=name,
        slug=slug,
        country=country,
        logo_url=logo_url,
        season_year=season_year,
    )
