#!/usr/bin/env python3
"""rebuild_rankings.py — offline pipeline: recalculate Elo + Glicko from fight history.

Processes all fights chronologically to produce up-to-date ratings.
"""

import sys
import numpy as np

from intelligence.rankings_engine.elo import update_elo, INITIAL_ELO
from intelligence.rankings_engine.glicko import update_glicko, INITIAL_RATING, INITIAL_RD
from intelligence.rankings_engine.composite import composite_ranking_score, rank_fighters
from intelligence.feature_store.serializer import save_rankings


def rebuild_rankings(fights: list[dict], fighters: dict[str, dict]) -> dict[str, dict]:
    """Process all fights chronologically, updating Elo + Glicko for each fighter.

    Returns dict of fighter_id → {elo, glicko_rating, glicko_rd, composite, rank}
    """
    ratings = {}
    for fid in fighters:
        ratings[fid] = {"elo": INITIAL_ELO, "glicko_rating": INITIAL_RATING, "glicko_rd": INITIAL_RD}

    fights_sorted = sorted(fights, key=lambda f: f.get("date", "2000-01-01"))

    for fight in fights_sorted:
        a = fight.get("fighter_a_id", "")
        b = fight.get("fighter_b_id", "")
        if a not in ratings or b not in ratings:
            continue

        a_won = fight.get("winner_id") == a
        is_finish = fight.get("method", "").lower() not in ("decision", "decision - unanimous",
            "decision - split", "decision - majority")
        is_title = fight.get("is_title", False)

        a_total = fighters.get(a, {}).get("wins", 0) + fighters.get(a, {}).get("losses", 0)
        b_total = fighters.get(b, {}).get("wins", 0) + fighters.get(b, {}).get("losses", 0)

        new_a, new_b = update_elo(ratings[a]["elo"], ratings[b]["elo"], a_won,
                                  a_fights=a_total, b_fights=b_total,
                                  is_title=is_title, is_finish=is_finish)
        ratings[a]["elo"] = new_a
        ratings[b]["elo"] = new_b

        new_ga, new_rda = update_glicko(ratings[a]["glicko_rating"], ratings[a]["glicko_rd"],
                                        ratings[b]["glicko_rating"], ratings[b]["glicko_rd"], a_won)
        new_gb, new_rdb = update_glicko(ratings[b]["glicko_rating"], ratings[b]["glicko_rd"],
                                        ratings[a]["glicko_rating"], ratings[a]["glicko_rd"], not a_won)
        ratings[a].update(glicko_rating=new_ga, glicko_rd=new_rda)
        ratings[b].update(glicko_rating=new_gb, glicko_rd=new_rdb)

    # Composite scores
    for fid, r in ratings.items():
        f = fighters.get(fid, {})
        r["composite"] = composite_ranking_score(
            elo_rating=r["elo"], championship=f.get("championship", 0),
            momentum=f.get("momentum_score", 0.5), finish_rate=f.get("finish_rate", 0.5),
        )

    return ratings


if __name__ == "__main__":
    print("Ranking pipeline — import and use programmatically")
