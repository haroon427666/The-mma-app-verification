"""Notification triggers — when to notify users about what."""

import math
from typing import Any


NOTIFICATION_TYPES = [
    "upcoming_fight",
    "event_starting",
    "ranking_changed",
    "fight_cancelled",
    "new_main_event",
    "title_fight_added",
    "watchlist_event",
    "favorite_fighter_booked",
    "weekly_digest",
]


class NotificationTrigger:
    def __init__(self, ntype: str, user_id: str, title: str, message: str, payload: dict | None = None):
        self.type = ntype
        self.user_id = user_id
        self.title = title
        self.message = message
        self.payload = payload or {}

    def to_dict(self) -> dict:
        return {
            "type": self.type,
            "user_id": self.user_id,
            "title": self.title,
            "message": self.message,
            "payload": self.payload,
        }


class WatchlistChecker:
    """Checks watchlist events for changes worth notifying."""

    def check_event_starting(self, event: dict, watchlist_users: list[str]) -> list[NotificationTrigger]:
        triggers = []
        for uid in watchlist_users:
            triggers.append(NotificationTrigger(
                "event_starting", uid,
                f"🔴 {event.get('name','Event')} is starting!",
                f"Your watchlisted event is live now.",
                {"event_id": event.get("id")},
            ))
        return triggers

    def check_fight_booked(self, fighter_id: str, event: dict, favorite_users: list[str]) -> list[NotificationTrigger]:
        triggers = []
        for uid in favorite_users:
            triggers.append(NotificationTrigger(
                "favorite_fighter_booked", uid,
                f"🥊 {fighter_id} is fighting!",
                f"Booked for {event.get('name','')}",
                {"fighter_id": fighter_id, "event_id": event.get("id")},
            ))
        return triggers


class DigestBuilder:
    """Builds weekly digest notifications — top fights, trending fighters, etc."""

    def build(self, user_id: str, top_fights: list[dict], trending: list[dict]) -> NotificationTrigger:
        parts = []
        if top_fights:
            fight_names = [f.get("name", "") for f in top_fights[:3]]
            parts.append(f"🔥 Top fights: {', '.join(fight_names)}")
        if trending:
            trending_names = [t.get("name", "") for t in trending[:3]]
            parts.append(f"📈 Trending: {', '.join(trending_names)}")

        return NotificationTrigger(
            "weekly_digest", user_id,
            "📊 Your Weekly MMA Digest",
            "\n".join(parts),
            {"top_fights": [f["id"] for f in top_fights[:3]],
             "trending": [t["id"] for t in trending[:3]]},
        )
