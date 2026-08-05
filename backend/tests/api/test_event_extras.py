"""Event-extras API tests — /v1/events/{id}/fights, /results, /statistics.

These endpoints derive data from the competitions/competitors tables and the
event fight card — all real columns, no fabricated data.
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest


def _make_fake_uow(executions=None, event=None):
    """executions: list of row-lists returned by session.execute().scalars().all()"""
    uow = MagicMock()
    uow.events.get_by_id = AsyncMock(return_value=event if event is not None else MagicMock())
    session = AsyncMock()
    results = []
    for rows in executions or []:
        result = MagicMock()
        result.scalars.return_value.all.return_value = rows
        results.append(result)
    if len(results) == 1:
        session.execute.return_value = results[0]
    else:
        session.execute.side_effect = results
    uow.session = session
    return uow


def _request():
    return MagicMock()


def _competition(cid, order=1, segment="mainCard", status="SCHEDULED",
                 is_title=False, is_main=False, wc="Lightweight",
                 method=None, round_=None, time=None):
    from src.db.models.event import Competition

    return Competition(
        id=cid, event_id="evt-1", order_num=order, card_segment=segment,
        status=status, is_title_fight=is_title, is_main_event=is_main,
        weight_class_name=wc, result_method=method, result_round=round_,
        result_time=time,
    )


def _competitor(comp_id, fighter_id, corner, outcome=None):
    from src.db.models.event import Competitor

    return Competitor(
        competition_id=comp_id, fighter_id=fighter_id, corner=corner,
        outcome=outcome,
    )


def _fighter(fid, country="USA"):
    from src.db.models.fighter import Fighter

    return Fighter(id=fid, first_name="A", last_name=fid, nationality=country)


# ═══════════════════════════════════════════════════════════════════════════════
# Fights (fight card)
# ═══════════════════════════════════════════════════════════════════════════════


class TestEventFights:
    def test_returns_ordered_fight_card(self):
        from src.api.v1.events import get_event_fights

        comp1 = _competition("c1", order=1, is_main=True, is_title=True)
        comp2 = _competition("c2", order=2)
        competitors = [
            _competitor("c1", "fA", "RED"),
            _competitor("c1", "fB", "BLUE", outcome="WIN"),
            _competitor("c2", "fC", "RED", outcome="WIN"),
        ]
        uow = _make_fake_uow(executions=[[comp1, comp2], competitors])
        resp = asyncio.run(get_event_fights(_request(), "evt-1", uow=uow))

        data = resp.body  # cached_json_response returns the raw Response
        import json
        payload = json.loads(data) if isinstance(data, (bytes, str)) else data
        assert len(payload) == 2
        first = payload[0]
        assert first["id"] == "c1"
        assert first["is_main_event"] is True
        assert first["is_title_fight"] is True
        assert first["winner"] == "fB"  # derived from competitor outcome

    def test_404_when_event_missing(self):
        from fastapi import HTTPException

        from src.api.v1.events import get_event_fights

        uow = MagicMock()
        uow.events.get_by_id = AsyncMock(return_value=None)
        session = AsyncMock()
        uow.session = session
        with pytest.raises(HTTPException) as exc:
            asyncio.run(get_event_fights(_request(), "missing", uow=uow))
        assert exc.value.status_code == 404


# ═══════════════════════════════════════════════════════════════════════════════
# Results
# ═══════════════════════════════════════════════════════════════════════════════


class TestEventResults:
    def test_returns_only_fights_with_results(self):
        from src.api.v1.events import get_event_results

        comp = _competition("c1", order=1, method="Submission", round_=2, time="03:45")
        competitors = [
            _competitor("c1", "fA", "RED"),
            _competitor("c1", "fB", "BLUE", outcome="WIN"),
        ]
        uow = _make_fake_uow(executions=[[comp], competitors])
        resp = asyncio.run(get_event_results(_request(), "evt-1", uow=uow))

        import json
        payload = json.loads(resp.body) if isinstance(resp.body, (bytes, str)) else resp.body
        assert len(payload) == 1
        assert payload[0]["method"] == "Submission"
        assert payload[0]["round"] == 2
        assert payload[0]["time"] == "03:45"
        assert payload[0]["winner"] == "fB"

    def test_404_when_event_missing(self):
        from fastapi import HTTPException

        from src.api.v1.events import get_event_results

        uow = MagicMock()
        uow.events.get_by_id = AsyncMock(return_value=None)
        uow.session = AsyncMock()
        with pytest.raises(HTTPException) as exc:
            asyncio.run(get_event_results(_request(), "missing", uow=uow))
        assert exc.value.status_code == 404


# ═══════════════════════════════════════════════════════════════════════════════
# Statistics
# ═══════════════════════════════════════════════════════════════════════════════


class TestEventStatistics:
    def test_computes_aggregates_from_fight_card(self):
        from src.api.v1.events import get_event_statistics

        comps = [
            _competition("c1", order=1, method="KO", wc="Heavyweight", is_title=True),
            _competition("c2", order=2, method="Decision", wc="Lightweight"),
            _competition("c3", order=3, method="Submission", wc="Lightweight"),
            _competition("c4", order=4, method="TKO", wc="Welterweight"),
        ]
        competitors = [
            _competitor("c1", "f1", "RED", outcome="WIN"),
            _competitor("c1", "f2", "BLUE"),
            _competitor("c2", "f3", "RED", outcome="WIN"),
            _competitor("c3", "f4", "RED", outcome="WIN"),
            _competitor("c4", "f5", "RED", outcome="WIN"),
        ]
        fighters = [_fighter("f1", "USA"), _fighter("f3", "Brazil"), _fighter("f4", "USA")]
        uow = _make_fake_uow(executions=[comps, competitors, fighters])
        resp = asyncio.run(get_event_statistics(_request(), "evt-1", uow=uow))

        import json
        payload = json.loads(resp.body) if isinstance(resp.body, (bytes, str)) else resp.body
        assert payload["total_fights"] == 4
        assert payload["title_fights"] == 1
        assert payload["decisions"] == 1
        assert payload["finishes"] == 3
        assert payload["ko_tko"] == 2
        assert payload["submissions"] == 1
        assert payload["countries_represented"] == 2
        assert payload["weight_classes"] == ["Heavyweight", "Lightweight", "Welterweight"]

    def test_empty_card_produces_zeros(self):
        from src.api.v1.events import get_event_statistics

        uow = _make_fake_uow(executions=[[], [], []])
        resp = asyncio.run(get_event_statistics(_request(), "evt-1", uow=uow))

        import json
        payload = json.loads(resp.body) if isinstance(resp.body, (bytes, str)) else resp.body
        assert payload["total_fights"] == 0
        assert payload["countries_represented"] == 0
        assert payload["weight_classes"] == []

    def test_404_when_event_missing(self):
        from fastapi import HTTPException

        from src.api.v1.events import get_event_statistics

        uow = MagicMock()
        uow.events.get_by_id = AsyncMock(return_value=None)
        uow.session = AsyncMock()
        with pytest.raises(HTTPException) as exc:
            asyncio.run(get_event_statistics(_request(), "missing", uow=uow))
        assert exc.value.status_code == 404
