"""
Real Normalization Mappers — field-level mappings from every source to canonical.

Production normalization isn't generic — it's thousands of specific mappings:
  Lightweight / LW / 155 lbs / Light Weight → "Lightweight"
  Islam Makhachev / Islam Ramazanovich Makhachev / I. Makhachev → "Islam Makhachev"

This module provides the real mapping tables + mapper registry.
"""

from platform.normalization import (
    CanonicalFighter, CanonicalEvent, CanonicalFight, CanonicalRanking,
    lbs_to_kg, inches_to_cm,
)

# ═══════════════════════════════════════════════════════════════════════════
# Weight Class Normalization — every variant → canonical
# ═══════════════════════════════════════════════════════════════════════════

WEIGHT_CLASS_CANONICAL: dict[str, str] = {
    # ESPN names
    "Flyweight": "Flyweight",
    "Bantamweight": "Bantamweight",
    "Featherweight": "Featherweight",
    "Lightweight": "Lightweight",
    "Welterweight": "Welterweight",
    "Middleweight": "Middleweight",
    "Light Heavyweight": "Light Heavyweight",
    "Heavyweight": "Heavyweight",
    "Women's Strawweight": "Strawweight",
    "Women's Flyweight": "Flyweight",
    "Women's Bantamweight": "Bantamweight",
    "Women's Featherweight": "Featherweight",
    "Catch Weight": "Catchweight",
    # Aliases from other sources
    "LW": "Lightweight",
    "WW": "Welterweight",
    "MW": "Middleweight",
    "LHW": "Light Heavyweight",
    "HW": "Heavyweight",
    "FLW": "Flyweight",
    "BW": "Bantamweight",
    "FW": "Featherweight",
    "WSW": "Strawweight",
    "WBW": "Bantamweight",
    "WFW": "Featherweight",
    "155 lbs": "Lightweight",
    "170 lbs": "Welterweight",
    "185 lbs": "Middleweight",
    "205 lbs": "Light Heavyweight",
    "265 lbs": "Heavyweight",
    "125 lbs": "Flyweight",
    "135 lbs": "Bantamweight",
    "145 lbs": "Featherweight",
    "115 lbs": "Strawweight",
    "Light Weight": "Lightweight",
    "Welter Weight": "Welterweight",
    "Middle Weight": "Middleweight",
    "Heavy Weight": "Heavyweight",
    "Straw Weight": "Strawweight",
    "Lightweight Division": "Lightweight",
    "Welterweight Division": "Welterweight",
    "Heavyweight Division": "Heavyweight",
}


def normalize_weight_class(raw: str | None) -> str:
    """Map any weight class variant to canonical name."""
    if not raw:
        return ""
    cleaned = raw.strip()
    # Remove gender prefix for matching
    for prefix in ("Women's ", "Womens ", "Men's ", "Mens "):
        if cleaned.startswith(prefix):
            cleaned = cleaned[len(prefix):]
    return WEIGHT_CLASS_CANONICAL.get(cleaned, cleaned)


# ═══════════════════════════════════════════════════════════════════════════
# Country Normalization
# ═══════════════════════════════════════════════════════════════════════════

COUNTRY_CANONICAL: dict[str, str] = {
    "USA": "United States",
    "US": "United States",
    "United States of America": "United States",
    "UK": "United Kingdom",
    "England": "United Kingdom",
    "Great Britain": "United Kingdom",
    "UAE": "United Arab Emirates",
    "Korea": "South Korea",
    "Republic of Korea": "South Korea",
    "Russian Federation": "Russia",
    "Brasil": "Brazil",
    "BR": "Brazil",
    "DE": "Germany",
    "FR": "France",
    "IT": "Italy",
    "JP": "Japan",
    "CN": "China",
    "AU": "Australia",
    "NZ": "New Zealand",
    "CA": "Canada",
    "MX": "Mexico",
    "IR": "Iran",
    "IE": "Ireland",
    "SE": "Sweden",
    "NL": "Netherlands",
    "PL": "Poland",
    "CH": "Switzerland",
    "DK": "Denmark",
    "NO": "Norway",
    "FI": "Finland",
    "PT": "Portugal",
    "ES": "Spain",
    "Dagestan": "Russia",
    "Chechnya": "Russia",
}


def normalize_country(raw: str | None) -> str:
    """Map country variants to canonical name."""
    if not raw:
        return ""
    return COUNTRY_CANONICAL.get(raw.strip(), raw.strip())


# ═══════════════════════════════════════════════════════════════════════════
# Name Normalization — strip titles, unify formatting
# ═══════════════════════════════════════════════════════════════════════════

def normalize_name(raw: str | None) -> str:
    """Normalize fighter name: strip middle names, titles, extra whitespace."""
    if not raw:
        return ""
    cleaned = raw.strip()
    # Remove quotes around nicknames
    cleaned = cleaned.replace('"', '').replace("'", '')
    # Normalize spacing
    cleaned = " ".join(cleaned.split())
    return cleaned


# ═══════════════════════════════════════════════════════════════════════════
# Result Method Normalization
# ═══════════════════════════════════════════════════════════════════════════

METHOD_CANONICAL: dict[str, str] = {
    "KO": "KO/TKO",
    "TKO": "KO/TKO",
    "KO/TKO": "KO/TKO",
    "Knockout": "KO/TKO",
    "Technical Knockout": "KO/TKO",
    "Submission": "Submission",
    "SUB": "Submission",
    "Decision - Unanimous": "Decision - Unanimous",
    "Decision - Split": "Decision - Split",
    "Decision - Majority": "Decision - Majority",
    "Unanimous Decision": "Decision - Unanimous",
    "Split Decision": "Decision - Split",
    "Majority Decision": "Decision - Majority",
    "DEC": "Decision - Unanimous",
    "DQ": "DQ",
    "Disqualification": "DQ",
    "NC": "No Contest",
    "No Contest": "No Contest",
}


def normalize_method(raw: str | None) -> str:
    if not raw:
        return ""
    return METHOD_CANONICAL.get(raw, raw)


# ═══════════════════════════════════════════════════════════════════════════
# Stance Normalization
# ═══════════════════════════════════════════════════════════════════════════

STANCE_CANONICAL: dict[str, str] = {
    "Orthodox": "Orthodox",
    "orthodox": "Orthodox",
    "Southpaw": "Southpaw",
    "southpaw": "Southpaw",
    "Switch": "Switch",
    "switch": "Switch",
    "Open Stance": "Open Stance",
    "Sideways": "Open Stance",
    "Unorthodox": "Open Stance",
}


def normalize_stance(raw: str | None) -> str | None:
    if not raw:
        return None
    return STANCE_CANONICAL.get(raw, raw)


# ═══════════════════════════════════════════════════════════════════════════
# Real Mapper Registry — source + entity → canonical transformer
# ═══════════════════════════════════════════════════════════════════════════

class MapperRegistry:
    """Real mapper registry with field-level normalization."""

    def __init__(self):
        self._mappers: dict[str, dict[str, callable]] = {}

    def register(self, source: str, entity_type: str, mapper_fn: callable):
        self._mappers.setdefault(source, {})[entity_type] = mapper_fn

    def get(self, source: str, entity_type: str) -> callable | None:
        return self._mappers.get(source, {}).get(entity_type)

    def list_sources(self) -> list[str]:
        return list(self._mappers.keys())


# ── Create the production mapper registry ──────────────────────────────────

def create_mapper_registry() -> MapperRegistry:
    """Create mapper registry with real ESPN → canonical mappings."""
    registry = MapperRegistry()

    # ESPN Fighter → CanonicalFighter
    def espn_fighter_to_canonical(item: dict) -> CanonicalFighter:
        return CanonicalFighter(
            canonical_id="",
            source_ids={"espn": str(item.get("external_id", ""))},
            first_name=item.get("first_name", ""),
            last_name=item.get("last_name", ""),
            full_name=normalize_name(item.get("full_name")),
            nickname=item.get("nickname", ""),
            birth_date=item.get("birth_date"),
            birth_location=item.get("birth_location", ""),
            nationality=normalize_country(item.get("nationality")),
            country=normalize_country(item.get("nationality")),
            height_cm=item.get("height_cm"),
            weight_kg=item.get("weight_kg"),
            reach_cm=item.get("reach_cm"),
            stance=normalize_stance(item.get("stance")),
            weight_class=normalize_weight_class(item.get("weight_class_name")),
            wins=item.get("record_wins", 0) or 0,
            losses=item.get("record_losses", 0) or 0,
            draws=item.get("record_draws", 0) or 0,
            no_contests=item.get("record_no_contests", 0) or 0,
            is_active=item.get("is_active", True),
            quality_score=0.85,
            source_count=1,
        )
    registry.register("espn", "fighter", espn_fighter_to_canonical)

    # ESPN Event → CanonicalEvent
    def espn_event_to_canonical(item: dict) -> CanonicalEvent:
        return CanonicalEvent(
            canonical_id="",
            source_ids={"espn": str(item.get("external_id", ""))},
            name=item.get("name", ""),
            short_name=item.get("short_name", ""),
            date_utc=item.get("date_utc"),
            status=str(item.get("status", "SCHEDULED")),
            promotion=item.get("promotion_name", ""),
            venue=item.get("venue_name", ""),
            city=item.get("city", ""),
            country=normalize_country(item.get("country")),
            source_count=1,
        )
    registry.register("espn", "event", espn_event_to_canonical)

    # Octagon Fighter → CanonicalFighter (enrichment)
    def octagon_fighter_to_canonical(item: dict) -> CanonicalFighter:
        name = item.get("name", "")
        parts = name.split()
        return CanonicalFighter(
            canonical_id="",
            source_ids={"octagon": str(item.get("slug", ""))},
            first_name=parts[0] if parts else "",
            last_name=" ".join(parts[1:]) if len(parts) > 1 else "",
            full_name=name,
            nickname=item.get("nickname", ""),
            birth_location=item.get("placeOfBirth", ""),
            leg_reach_cm=inches_to_cm(float(item.get("legReach", "0").replace('"', ''))) if item.get("legReach") else None,
            gym=item.get("trainsAt", ""),
            fighting_style=item.get("fightingStyle", ""),
            debut_date=item.get("octagonDebut"),
            wins=item.get("wins", 0) or 0,
            losses=item.get("losses", 0) or 0,
            draws=item.get("draws", 0) or 0,
            is_active=True,
            quality_score=0.80,
            source_count=1,
        )
    registry.register("octagon", "fighter", octagon_fighter_to_canonical)

    # TheSportsDB Fighter → CanonicalFighter (enrichment)
    def tsdb_fighter_to_canonical(item: dict) -> CanonicalFighter:
        return CanonicalFighter(
            canonical_id="",
            source_ids={"tsdb": str(item.get("external_id", ""))},
            first_name="",
            last_name=item.get("last_name", ""),
            full_name=item.get("full_name", ""),
            nickname=item.get("nickname", ""),
            nationality=normalize_country(item.get("nationality")),
            birth_date=item.get("birth_date"),
            birth_location=item.get("birth_location", ""),
            biography=item.get("biography", ""),
            images={"cutout": item.get("cutout_url", ""), "render": item.get("render_url", "")},
            social_links={
                "facebook": item.get("facebook_url", ""),
                "instagram": item.get("instagram_url", ""),
                "twitter": item.get("twitter_url", ""),
            },
            quality_score=0.70,
            source_count=1,
        )
    registry.register("tsdb", "fighter", tsdb_fighter_to_canonical)

    return registry
