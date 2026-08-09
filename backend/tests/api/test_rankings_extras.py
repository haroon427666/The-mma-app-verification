"""Rankings-extras API tests — movement, GOAT, prospects, streaks, title-defenses.

These endpoints derive data from the rankings snapshots, fighter records, and
competition outcomes — all real columns, no fabricated data.
"""

import asyncio
import json
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

import pytest


def _make_fake_uow(rows=None, first_row=None, scalars=None):
    uow = MagicMock()
    session = AsyncMock()
    result = MagicMock()
    result.all.return_value = rows or []
    result.first.return_value = first_row
    result.scalar_one_or_none.return_value = first_row
    result.scalars.return_value.all.return_value = scalars or []
    session.execute.return_value = result
    uow._session = session
    return uow


def _request():
    return MagicMock()


def _ranking(fid, cat, rank, synced_at, gender="MALE", trend="STEADY",
             champion=False, defenses=0, cat_type="division"):
    from src.db.models.core import Ranking

    return Ranking(
        fighter_id=fid, category_name=cat, category_type=cat_type,
        gender=gender, rank=rank, trend=trend,
        is_champion=champion, title_defenses=defenses,
        synced_at=synced_at,
    )


def _fighter(fid, name, wins, losses, height=None, reach=None, weight=None,
             finish_rate=None, win_pct=None, active=True, wc="Lightweight"):
    from src.db.models.fighter import Fighter, FighterRecord

    rb = FighterRecord(
        fighter_id=fid, wins=wins, losses=losses, draws=0, total_fights=wins + losses,
        win_percentage=win_pct or (wins / (wins + losses) if wins + losses else 0.0),
        finish_rate=finish_rate or 0.0,
    )
    f = Fighter(
        id=fid, first_name=name.split()[0], last_name=name.split()[-1],
        full_name=name, record_wins=wins, record_losses=losses, record_draws=0,
        height_cm=height, reach_cm=reach, weight_kg=weight,
        is_active=active, weight_class_name=wc,
    )
    f.record_breakdown = rb
    return f


# ═══════════════════════════════════════════════════════════════════════════════
# Movement
# ═══════════════════════════════════════════════════════════════════════════════


class TestMovement:
    def test_movement_requires_two_snapshots(self):
        from src.api.v1.other import rankings_movement

        single = [_ranking("f-1", "Lightweight", 3, datetime(2026, 7, 1))]
        uow = _make_fake_uow(scalars=single)
        resp = asyncio.run(rankings_movement(_request(), uow=uow))
        assert json.loads(resp.body) == []

    def test_movement_reports_rank_changes(self):
        from src.api.v1.other import rankings_movement

        t1 = datetime(2026, 7, 1)
        t2 = datetime(2026, 8, 1)
        rows = [
            _ranking("f-1", "Lightweight", 3, t2),
            _ranking("f-2", "Lightweight", 1, t2),
            _ranking("f-1", "Lightweight", 5, t1),
            _ranking("f-2", "Lightweight", 1, t1),
        ]
        f1 = _fighter("f-1", "Islam Makhachev", 28, 1)
        f2 = _fighter("f-2", "Jon Jones", 28, 1)
        uow = _make_fake_uow(scalars=rows)
        first = MagicMock()
        first.scalars.return_value.all.return_value = rows
        frows = MagicMock()
        frows.scalars.return_value.all.return_value = [f1, f2]
        uow._session.execute.side_effect = [first, frows]

        resp = asyncio.run(rankings_movement(_request(), uow=uow))
        body = json.loads(resp.body)
        assert len(body) == 1
        assert body[0]["fighter"]["id"] == "f-1"
        assert body[0]["from_rank"] == 5
        assert body[0]["to_rank"] == 3
        assert body[0]["change"] == 2


# ═══════════════════════════════════════════════════════════════════════════════
# GOAT
# ═══════════════════════════════════════════════════════════════════════════════


class TestGoat:
    def test_goat_lists_champions_with_score(self):
        from src.api.v1.other import goat_rankings

        champ = _ranking("f-1", "Lightweight", 1, datetime(2026, 8, 1),
                         champion=True, defenses=4)
        f = _fighter("f-1", "Islam Makhachev", 28, 1, finish_rate=0.5, win_pct=0.9)
        uow = _make_fake_uow(rows=[(champ, f)])

        resp = asyncio.run(goat_rankings(_request(), uow=uow))
        body = json.loads(resp.body)
        assert len(body) == 1
        assert body[0]["fighter"]["full_name"] == "Islam Makhachev"
        assert body[0]["title_defenses"] == 4
        assert body[0]["composite_score"] > 0
        assert body[0]["rank"] == 1

    def test_goat_scores_defenses_highest(self):
        from src.api.v1.other import goat_rankings

        c1 = _ranking("f-1", "Lightweight", 1, datetime(2026, 8, 1),
                      champion=True, defenses=8)
        c2 = _ranking("f-2", "Welterweight", 1, datetime(2026, 8, 1),
                      champion=True, defenses=1)
        f1 = _fighter("f-1", "Fighter A", 30, 0, finish_rate=0.6, win_pct=1.0)
        f2 = _fighter("f-2", "Fighter B", 30, 0, finish_rate=0.6, win_pct=1.0)
        uow = _make_fake_uow(rows=[(c1, f1), (c2, f2)])

        resp = asyncio.run(goat_rankings(_request(), uow=uow))
        body = json.loads(resp.body)
        assert body[0]["fighter"]["full_name"] == "Fighter A"
        assert body[0]["rank"] == 1
        assert body[1]["rank"] == 2

    def test_goat_fills_from_active_unranked(self):
        from src.api.v1.other import goat_rankings

        uow = _make_fake_uow(rows=[], scalars=[_fighter("f-9", "Rising Star", 10, 0, finish_rate=0.9, win_pct=1.0)])
        resp = asyncio.run(goat_rankings(_request(), uow=uow))
        body = json.loads(resp.body)
        assert any(e["fighter"]["id"] == "f-9" for e in body)


# ═══════════════════════════════════════════════════════════════════════════════
# Prospects
# ═══════════════════════════════════════════════════════════════════════════════


class TestProspects:
    def test_prospects_only_unranked_active(self):
        from src.api.v1.other import prospect_rankings

        ranked_ids_result = MagicMock()
        ranked_ids_result.all.return_value = [("f-1",)]
        f1 = _fighter("f-1", "Ranked Guy", 15, 3, finish_rate=0.9, win_pct=0.8)
        f2 = _fighter("f-2", "Unranked Guy", 12, 2, finish_rate=0.75, win_pct=0.85)
        fighters_result = MagicMock()
        fighters_result.scalars.return_value.all.return_value = [f1, f2]
        uow = _make_fake_uow()
        uow._session.execute.side_effect = [ranked_ids_result, fighters_result]

        resp = asyncio.run(prospect_rankings(_request(), uow=uow))
        body = json.loads(resp.body)
        assert len(body) == 1
        assert body[0]["fighter"]["full_name"] == "Unranked Guy"
        assert body[0]["trajectory"] == "rising"

    def test_prospects_sorted_by_finish_rate(self):
        from src.api.v1.other import prospect_rankings

        f_low = _fighter("f-1", "Low Finish", 10, 5, finish_rate=0.3, win_pct=0.66)
        f_high = _fighter("f-2", "High Finish", 10, 5, finish_rate=0.9, win_pct=0.66)
        ranked_ids_result = MagicMock()
        ranked_ids_result.all.return_value = []
        fighters_result = MagicMock()
        fighters_result.scalars.return_value.all.return_value = [f_low, f_high]
        uow = _make_fake_uow()
        uow._session.execute.side_effect = [ranked_ids_result, fighters_result]

        resp = asyncio.run(prospect_rankings(_request(), uow=uow))
        body = json.loads(resp.body)
        assert body[0]["fighter"]["full_name"] == "High Finish"


# ═══════════════════════════════════════════════════════════════════════════════
# Streaks
# ═══════════════════════════════════════════════════════════════════════════════


class TestStreaks:
    def test_streak_counts_consecutive_wins(self):
        from src.api.v1.other import win_streaks

        f = _fighter("f-1", "Streak Guy", 10, 5)
        frows = MagicMock()
        frows.scalars.return_value.all.return_value = [f]
        comp_rows = MagicMock()
        comp_rows.all.return_value = [
            ("f-1", "FINAL", "WIN", None),
            ("f-1", "FINAL", "WIN", None),
            ("f-1", "FINAL", "WIN", None),
        ]
        uow = _make_fake_uow()
        uow._session.execute.side_effect = [comp_rows, frows]

        resp = asyncio.run(win_streaks(_request(), limit=10, uow=uow))
        body = json.loads(resp.body)
        assert body[0]["fighter"]["full_name"] == "Streak Guy"
        assert body[0]["streak"] == 3

    def test_streak_ignores_losses(self):
        from src.api.v1.other import win_streaks

        f = _fighter("f-1", "Loss Guy", 2, 8)
        frows = MagicMock()
        frows.scalars.return_value.all.return_value = [f]
        comp_rows = MagicMock()
        comp_rows.all.return_value = [
            ("f-1", "FINAL", "WIN", None),
            ("f-1", "FINAL", "LOSS", None),
            ("f-1", "FINAL", "WIN", None),
        ]
        uow = _make_fake_uow()
        uow._session.execute.side_effect = [comp_rows, frows]

        resp = asyncio.run(win_streaks(_request(), limit=10, uow=uow))
        body = json.loads(resp.body)
        assert body == []


# ═══════════════════════════════════════════════════════════════════════════════
# Title defenses
# ═══════════════════════════════════════════════════════════════════════════════


class TestTitleDefenses:
    def test_lists_champions_with_defenses(self):
        from src.api.v1.other import list_title_defenses

        c1 = _ranking("f-1", "Lightweight", 1, datetime(2026, 8, 1),
                      champion=True, defenses=4)
        c2 = _ranking("f-2", "Heavyweight", 1, datetime(2026, 8, 1),
                      champion=True, defenses=0)
        f1 = _fighter("f-1", "Islam Makhachev", 28, 1)
        f2 = _fighter("f-2", "Jon Jones", 28, 1)
        uow = _make_fake_uow(rows=[(c1, f1), (c2, f2)])

        resp = asyncio.run(list_title_defenses(_request(), uow=uow))
        body = json.loads(resp.body)
        assert len(body) == 1
        assert body[0]["fighter"]["full_name"] == "Islam Makhachev"
        assert body[0]["defenses"] == 4
        assert body[0]["division"] == "Lightweight"


# ═══════════════════════════════════════════════════════════════════════════════
# Similar fighters
# ═══════════════════════════════════════════════════════════════════════════════


class TestSimilarFighters:
    def test_similar_returns_same_division(self):
        from src.api.v1.other import _fighter_brief
        from src.schemas.misc import FighterBrief

        f = _fighter("f-1", "Islam Makhachev", 28, 1, height=178, reach=183, weight=70)
        brief = _fighter_brief(f)
        assert isinstance(brief, FighterBrief)
        assert brief.full_name == "Islam Makhachev"
        assert brief.record == "28-1-0"

    def test_endpoint_404_unknown_fighter(self):
        from fastapi import HTTPException

        from src.api.v1.fighters import get_similar_fighters

        uow = _make_fake_uow(first_row=None)
        with pytest.raises(HTTPException) as exc:
            asyncio.run(get_similar_fighters(_request(), "missing", uow=uow))
        assert exc.value.status_code == 404

    def test_endpoint_ranks_closest_fighter_first(self):
        from src.api.v1.fighters import get_similar_fighters

        target = _fighter("f-1", "Target Guy", 20, 5, height=180, reach=185, weight=70)
        close = _fighter("f-2", "Close Clone", 21, 4, height=181, reach=184, weight=71)
        far = _fighter("f-3", "Far Away", 5, 10, height=160, reach=160, weight=60)

        uow = _make_fake_uow(first_row=target)
        session = AsyncMock()
        target_res = MagicMock()
        target_res.scalar_one_or_none.return_value = target
        cand_res = MagicMock()
        cand_res.scalars.return_value.all.return_value = [close, far]
        session.execute.side_effect = [target_res, cand_res]
        uow._session = session

        resp = asyncio.run(get_similar_fighters(_request(), "11111111-1111-4111-8111-111111111111", uow=uow))
        body = json.loads(resp.body)
        assert body["fighter"]["full_name"] == "Target Guy"
        assert len(body["similar"]) == 2
        assert body["similar"][0]["fighter"]["full_name"] == "Close Clone"
        assert body["similar"][0]["similarity_score"] > body["similar"][1]["similarity_score"]
