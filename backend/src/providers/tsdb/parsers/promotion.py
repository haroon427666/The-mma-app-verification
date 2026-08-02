"""TheSportsDB Promotion (League) Parser.

Maps TSDB league fields → PromotionDTO (same DTO as ESPN).
TSDB provides: media assets, social links, descriptions, historical data.
"""

from src.providers.dto import PromotionDTO


def parse_promotion(data: dict) -> PromotionDTO:
    """Parse TSDB league → PromotionDTO (enrichment fields only).

    ESPN is the authority for: id, name, slug, abbreviation, short_name.
    TSDB provides: logos, posters, banners, fanart, social links, descriptions, country, founded, tv rights.
    """
    external_id = str(data.get("idLeague", ""))
    name = data.get("strLeague", "") or data.get("strLeagueAlternate", "")
    slug = (data.get("strLeague", "") or "").lower().replace(" ", "-")

    return PromotionDTO(
        provider="tsdb",
        external_id=external_id,
        name=name,
        slug=slug,
        # TSDB enrichment fields (ESPN doesn't have these)
        country=data.get("strCountry"),
        logo_url=data.get("strBadge") or data.get("strLogo"),
        season_year=data.get("strCurrentSeason"),
        # These are stored via merge, not in the base PromotionDTO —
        # stored in separate enrichment columns or JSONB
    )


def parse_promotion_enrichment(data: dict) -> dict:
    """Extract enrichment-only fields that supplement the ESPN PromotionDTO."""
    return {
        "poster_url": data.get("strPoster"),
        "banner_url": data.get("strBanner"),
        "trophy_url": data.get("strTrophy"),
        "fanart_urls": [
            u for u in [
                data.get("strFanart1"), data.get("strFanart2"),
                data.get("strFanart3"), data.get("strFanart4"),
            ] if u
        ],
        "website": data.get("strWebsite"),
        "facebook_url": data.get("strFacebook"),
        "instagram_url": data.get("strInstagram"),
        "twitter_url": data.get("strTwitter"),
        "youtube_url": data.get("strYoutube"),
        "description": data.get("strDescriptionEN"),
        "tv_rights": data.get("strTvRights"),
        "founded_year": data.get("intFormedYear"),
        "first_event_date": data.get("dateFirstEvent"),
        "country": data.get("strCountry"),
    }
