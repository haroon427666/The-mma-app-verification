"""Champions API tests — /v1/champions list, division, and history endpoints."""

import asyncio
import json
from unittest.mock import AsyncMock, MagicMock

import pytest

# ═══════════════════════════════════════════════════════════════════════════════
# Champion builder
# ═══════════════════════════════════════════════════════════════════════════════


class TestChampionBuilder:
    def test_builds_entry_with_record_and_fighter(self):
        from src.api.v1.other import _champion_entry
        from src.db.models.core import Ranking
        from src.db.models.fighter import Fighter

        r = Ranking(
            fighter_id="f-1",
            category_name="Lightweight",
            category_type="weight_class",
            gender="MALE",
            rank=1,
            trend="STEADY",
            is_champion=True,
            title_defenses=4,
        )
        f = Fighter(
            first_name="Islam", last_name="Makhachev",
            full_name="Islam Makhachev", nickname="The Machine",
            record_wins=28, record_losses=1, record_draws=0,
            headshot_url="https://cdn/h.png",
        )
        entry = _champion_entry(r, f)
        assert entry.fighter.full_name == "Islam Makhachev"
        assert entry.fighter.record == "28-1-0"
        assert entry.title_defenses == 4
        assert entry.weight_class == "Lightweight"

    def test_record_always_includes_draws(self):
        from src.api.v1.other import _champion_entry
        from src.db.models.core import Ranking
        from src.db.models.fighter import Fighter

        r = Ranking(fighter_id="f-2", category_name="Heavyweight", rank=1, is_champion=True)
        f = Fighter(first_name="Jon", last_name="Jones",
                    record_wins=28, record_losses=1, record_draws=0)
        entry = _champion_entry(r, f)
        assert entry.fighter.record == "28-1-0"

    def test_record_includes_draws(self):
        from src.api.v1.other import _champion_entry
        from src.db.models.core import Ranking
        from src.db.models.fighter import Fighter

        r = Ranking(fighter_id="f-3", category_name="Heavyweight", rank=1, is_champion=True)
        f = Fighter(first_name="A", last_name="B", record_wins=1, record_losses=0, record_draws=1)
        entry = _champion_entry(r, f)
        assert entry.fighter.record == "1-0-1"


# ═══════════════════════════════════════════════════════════════════════════════
# Endpoint behavior (mocked session, same pattern as integration suite)
# ═══════════════════════════════════════════════════════════════════════════════


def _make_fake_uow(rows=None, first_row=None):
    uow = MagicMock()
    session = AsyncMock()
    result = MagicMock()
    result.all.return_value = rows or []
    result.first.return_value = first_row
    session.execute.return_value = result
    uow._session = session
    return uow


def _request():
    return MagicMock()


class TestChampionsEndpoint:
    def test_list_champions_returns_all_champions(self):
        from src.api.v1.other import list_champions
        from src.db.models.core import Ranking
        from src.db.models.fighter import Fighter

        champ = Ranking(
            fighter_id="f-1", category_name="Lightweight",
            category_type="weight_class", gender="MALE", rank=1,
            trend="STEADY", is_champion=True, title_defenses=4,
        )
        fighter = Fighter(first_name="Islam", last_name="Makhachev", nickname="The Machine",
                          record_wins=28, record_losses=1, record_draws=0)
        uow = _make_fake_uow(rows=[(champ, fighter)])

        resp = asyncio.run(list_champions(_request(), uow=uow))
        body = json.loads(resp.body)
        assert len(body) == 1
        assert body[0]["category_name"] == "Lightweight"
        assert body[0]["fighter"]["full_name"] == "Islam Makhachev"
        assert body[0]["fighter"]["record"] == "28-1-0"
        assert body[0]["title_defenses"] == 4

    def test_list_champions_empty_db(self):
        from src.api.v1.other import list_champions

        uow = _make_fake_uow(rows=[])
        resp = asyncio.run(list_champions(_request(), uow=uow))
        assert json.loads(resp.body) == []

    def test_division_champion_returns_champion(self):
        from src.api.v1.other import division_champion
        from src.db.models.core import Ranking
        from src.db.models.fighter import Fighter

        champ = Ranking(fighter_id="f-1", category_name="Heavyweight", rank=1, is_champion=True)
        fighter = Fighter(first_name="Jon", last_name="Jones", record_wins=28, record_losses=1)
        uow = _make_fake_uow(first_row=(champ, fighter))

        resp = asyncio.run(division_champion(_request(), "heavyweight", uow=uow))
        body = json.loads(resp.body)
        assert body["category_name"] == "Heavyweight"
        assert body["fighter"]["full_name"] == "Jon Jones"

    def test_division_champion_missing_404(self):
        from fastapi import HTTPException

        from src.api.v1.other import division_champion

        uow = _make_fake_uow(first_row=None)
        with pytest.raises(HTTPException) as exc:
            asyncio.run(division_champion(_request(), "flyweight", uow=uow))
        assert exc.value.status_code == 404

    def test_history_returns_empty_list(self):
        from src.api.v1.other import champion_history

        uow = _make_fake_uow()
        resp = asyncio.run(champion_history(_request(), uow=uow))
        assert json.loads(resp.body) == []


# ═══════════════════════════════════════════════════════════════════════════════
# Schema validation
# ═══════════════════════════════════════════════════════════════════════════════


class TestChampionSchema:
    def test_entry_roundtrips(self):
        from src.schemas.misc import ChampionEntry, ChampionFighter

        entry = ChampionEntry(
            category_name="Lightweight",
            category_type="weight_class",
            gender="MALE",
            weight_class="Lightweight",
            rank=1,
            trend="STEADY",
            title_defenses=4,
            fighter=ChampionFighter(
                id="f-1", full_name="Islam Makhachev",
                nickname="The Machine", record="28-1-0",
            ),
        )
        d = entry.model_dump(mode="json")
        assert d["fighter"]["full_name"] == "Islam Makhachev"
        assert d["rank"] == 1

    def test_entry_rejects_extra_fields(self):
        from pydantic import ValidationError

        from src.schemas.misc import ChampionEntry, ChampionFighter

        with pytest.raises(ValidationError):
            ChampionEntry(
                category_name="X", rank=1,
                fighter=ChampionFighter(id="f", full_name="N"),
                leak="should-fail",
            )
