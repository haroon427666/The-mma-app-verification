"""Octagon API Configuration.

Free, open-source MMA API — no authentication required.
Base: https://api.octagon-api.com
Source: GitHub victor-lillo/octagon-api (scrapes ufc.com)
"""

from dataclasses import dataclass

OCTAGON_BASE = "https://api.octagon-api.com"


@dataclass
class OctagonClientConfig:
    base_url: str = OCTAGON_BASE
    request_timeout: float = 15.0
    max_retries: int = 3
    retry_backoff_base: float = 2.0
    user_agent: str = "MMA-Backend/1.0 (Octagon Enrichment)"


# ── Endpoints ─────────────────────────────────────────────────────────────────

ENDPOINTS = {
    "rankings": "/rankings",
    "fighters": "/fighters",
    "fighter": "/fighter/{fighter_id}",
    "division": "/division/{division_id}",
}


# ── Field mappings ────────────────────────────────────────────────────────────

# Octagon uses inches/lbs like ESPN — same conversion needed
# Octagon field → standard DTO field
FIGHTER_FIELD_MAP = {
    "name": "full_name",
    "nickname": "nickname",
    "category": "weight_class_name",
    "wins": "record_wins",
    "losses": "record_losses",
    "draws": "record_draws",
    "status": "is_active",
    "placeOfBirth": "birth_location",
    "trainsAt": "trains_at",
    "fightingStyle": "fighting_style",
    "age": "age",
    "height": "height_cm",      # inches → cm
    "weight": "weight_kg",      # lbs → kg
    "reach": "reach_cm",        # inches → cm
    "legReach": "leg_reach_cm", # inches → cm — UNIQUE to Octagon
    "octagonDebut": "debut_date",
    "imgUrl": "headshot_url",
}
