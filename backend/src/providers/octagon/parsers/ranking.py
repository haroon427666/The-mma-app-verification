"""Octagon API Ranking Parser.

Returns clean ranking data for cross-verification with ESPN.

Octagon ranking format:
[
  {
    "id": "flyweight",
    "categoryName": "Flyweight",
    "champion": {"id": "alexandre-pantoja", "championName": "Alexandre Pantoja"},
    "fighters": [
      {"id": "brandon-royval", "name": "Brandon Royval"},
      ...
    ]
  }
]
"""

from src.providers.dto import RankingDTO


def parse_rankings(data: list[dict], promotion_external_id: str = "ufc") -> list[RankingDTO]:
    rankings: list[RankingDTO] = []
    for category in data:
        if not isinstance(category, dict):
            continue
        category_name = category.get("categoryName", "")
        category_type = category.get("id", "")

        # Champion (rank 0, is_champion=True)
        champion = category.get("champion", {}) or {}
        if isinstance(champion, dict) and champion.get("id"):
            rankings.append(RankingDTO(
                provider="octagon",
                fighter_external_id=champion["id"],
                promotion_external_id=promotion_external_id,
                category=category_name,
                rank=0,  # Champion = rank 0
                is_champion=True,
            ))

        # Ranked fighters (1-indexed)
        fighters = category.get("fighters", []) or []
        for idx, fighter in enumerate(fighters):
            if not isinstance(fighter, dict):
                continue
            rankings.append(RankingDTO(
                provider="octagon",
                fighter_external_id=fighter.get("id", ""),
                promotion_external_id=promotion_external_id,
                category=category_name,
                rank=idx + 1,
                is_champion=False,
            ))

    return rankings
