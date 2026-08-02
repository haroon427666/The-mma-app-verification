"""TheSportsDB Fighter (Player) Parser.

Maps TSDB player fields → FighterDTO.
TSDB provides: nickname, birth_location, biography, cutout/render images,
ethnicity, wikidata_id, social links (often empty for MMA).
"""

from datetime import datetime

from src.providers.dto import FighterDTO


def parse_fighter(data: dict) -> FighterDTO:
    external_id = str(data.get("idPlayer", ""))
    full_name = data.get("strPlayer", "")
    last_name = data.get("strLastName", "") or ""
    first_name = full_name.replace(last_name, "").strip() if last_name else full_name

    birth_date = None
    raw_dob = data.get("dateBorn")
    if raw_dob:
        try:
            birth_date = datetime.strptime(raw_dob, "%Y-%m-%d")
        except (ValueError, TypeError):
            pass

    return FighterDTO(
        provider="tsdb",
        external_id=external_id,
        first_name=first_name,
        last_name=last_name,
        # TSDB enrichment fields
        nickname=data.get("strPlayerAlternate") or None,
        nationality=data.get("strNationality"),
        birth_date=birth_date,
        birth_location=data.get("strBirthLocation"),
        headshot_url=data.get("strThumb"),
        # Record is NOT available from TSDB (defaults to 0)
        record_wins=0,
        record_losses=0,
        record_draws=0,
        record_no_contests=0,
    )


def parse_fighter_enrichment(data: dict) -> dict:
    """Enrichment-only fields from TSDB that supplement ESPN/Octagon."""
    return {
        "nickname": data.get("strPlayerAlternate") or None,
        "birth_location": data.get("strBirthLocation"),
        "cutout_url": data.get("strCutout"),
        "render_url": data.get("strRender"),
        "biography": data.get("strDescriptionEN"),
        "ethnicity": data.get("strEthnicity"),
        "wikidata_id": data.get("idWikidata"),
        "facebook_url": data.get("strFacebook") or None,
        "instagram_url": data.get("strInstagram") or None,
        "twitter_url": data.get("strTwitter") or None,
    }
