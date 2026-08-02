"""Retrieval — candidate generation for fighters, events, fights, promotions.

Fetches candidates from the backend API and enriches them with
embeddings and scores from the intelligence layer.
"""

from typing import Any


class FighterRetrieval:
    """Generate fighter recommendation candidates."""

    def get_candidates(self, fighters: list[dict], limit: int = 200) -> list[dict]:
        """Enrich fighters with required fields for recommendation."""
        return [
            {**f, "type": "fighter",
             "name": f.get("full_name", f"{f.get('first_name','')} {f.get('last_name','')}"),
             "image_url": f.get("headshot_url", ""),
             "finish_rate": _finish_rate(f),
             "elo_rating": f.get("elo_rating", 1500)}
            for f in fighters[:limit]
        ]

    def get_by_weight_class(self, fighters: list[dict], weight_class: str) -> list[dict]:
        return [f for f in fighters if f.get("weight_class") == weight_class]

    def get_ranked_only(self, fighters: list[dict]) -> list[dict]:
        return [f for f in fighters if f.get("latest_rank") is not None]


class EventRetrieval:
    def get_candidates(self, events: list[dict], limit: int = 100) -> list[dict]:
        return [
            {**e, "type": "event", "name": e.get("name", ""),
             "image_url": e.get("poster_url", e.get("thumbnail_url", "")),
             "quality_score": _event_quality(e)}
            for e in events[:limit]
        ]

    def get_upcoming(self, events: list[dict]) -> list[dict]:
        return [e for e in events if e.get("status") == "SCHEDULED"]

    def get_live(self, events: list[dict]) -> list[dict]:
        return [e for e in events if e.get("status") in ("IN_PROGRESS", "LIVE")]


class FightRetrieval:
    def get_candidates(self, fights: list[dict], limit: int = 300) -> list[dict]:
        return [
            {**f, "type": "fight",
             "name": f"{f.get('fighter_a_name','')} vs {f.get('fighter_b_name','')}",
             "is_title_fight": f.get("is_title_fight", False),
             "elo_rating": max(f.get("fighter_a_elo", 1500), f.get("fighter_b_elo", 1500))}
            for f in fights[:limit]
        ]


class PromotionRetrieval:
    def get_candidates(self, promotions: list[dict]) -> list[dict]:
        return [{**p, "type": "promotion", "name": p.get("name", "")} for p in promotions]


def _finish_rate(f: dict) -> float:
    w = max(f.get("wins", 1), 1)
    return (f.get("ko_wins", 0) + f.get("sub_wins", 0)) / w


def _event_quality(e: dict) -> float:
    fights = e.get("fight_count", 0)
    title = 1 if any(f.get("is_title_fight") for f in e.get("fights", [])) else 0
    return min(fights / 12.0, 0.7) + (0.3 if title else 0)
