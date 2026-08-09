"""ESPN client pagination tests — T02 (infinite-loop guards) + T05 pagination fix.

Live-proven ESPN v2 core API contract: list endpoints ignore `offset` and honor
`limit` (page size) + `page` (1-indexed). Response echoes the requested page in
`pageIndex`; `pageCount` is authoritative. See PLAN_HISTORY.md for the probe
evidence.
"""

import pytest

from src.providers.espn.client import ESPNClient
from src.providers.espn.config import ESPNClientConfig


def make_client(get_json_fn):
    client = ESPNClient(ESPNClientConfig(page_limit=100))
    client.get_json = get_json_fn
    return client


def make_page(items, page_index, page_count, limit=100):
    return {"items": items, "pageIndex": page_index, "pageCount": page_count, "limit": limit}


async def collect_pages(client, path="/athletes", **kwargs):
    pages = []
    async for page in client.paginate(path, **kwargs):
        pages.append(page)
    return pages


class TestPaginationGuards:
    @pytest.mark.asyncio
    async def test_normal_pagination_follows_page(self):
        """A well-behaved endpoint pages through every page (offset ignored)."""
        requested: list[int] = []

        async def fake_get_json(path, params):
            page = int(params["page"])
            requested.append(page)
            if page == 1:
                return make_page([{"$ref": f"/a/{i}"} for i in range(100)], 1, 3)
            if page == 2:
                return make_page([{"$ref": f"/a/{i}"} for i in range(100, 200)], 2, 3)
            if page == 3:
                return make_page([{"$ref": f"/a/{i}"} for i in range(200, 250)], 3, 3)
            return make_page([], 4, 3)

        client = make_client(fake_get_json)
        pages = await collect_pages(client)

        assert len(pages) == 3
        assert requested == [1, 2, 3]

    @pytest.mark.asyncio
    async def test_page_cap_bounds_run(self, monkeypatch):
        """A long endpoint (pageCount beyond cap) is bounded by ESPN_MAX_PAGES."""
        monkeypatch.setenv("ESPN_MAX_PAGES", "3")
        requested: list[int] = []

        async def fake_get_json(path, params):
            page = int(params["page"])
            requested.append(page)
            return make_page([{"$ref": f"/a/{page * 100 + i}"} for i in range(100)], page, 8)

        client = make_client(fake_get_json)
        pages = await collect_pages(client)

        assert len(pages) == 3
        assert requested == [1, 2, 3]

    @pytest.mark.asyncio
    async def test_empty_items_stops_immediately(self):
        """No items on the first page → zero pages yielded."""
        async def fake_get_json(path, params):
            return make_page([], 1, 1)

        client = make_client(fake_get_json)
        pages = await collect_pages(client)
        assert pages == []

    @pytest.mark.asyncio
    async def test_duplicate_page_stalls(self):
        """A server re-serving the same page (by id) must stop the loop."""
        request_count = 0

        async def fake_get_json(path, params):
            nonlocal request_count
            request_count += 1
            return make_page([{"id": str(i)} for i in range(5)], 1, 9)

        client = make_client(fake_get_json)
        pages = await collect_pages(client)

        assert request_count <= 3
        assert len(pages) >= 1

    @pytest.mark.asyncio
    async def test_limit_stops_after_item_cap(self):
        """limit=N yields only the pages needed to reach N items."""
        async def fake_get_json(path, params):
            page = int(params["page"])
            if page == 1:
                return make_page([{"$ref": f"/a/{i}"} for i in range(100)], 1, 5)
            return make_page([{"$ref": f"/a/{100 + i}"} for i in range(100)], 2, 5)

        client = make_client(fake_get_json)
        pages = await collect_pages(client, limit=150)

        assert len(pages) == 2

    @pytest.mark.asyncio
    async def test_page_count_end_stops(self):
        """Reaching the final page (pageIndex == pageCount) stops."""
        async def fake_get_json(path, params):
            return make_page([{"$ref": f"/a/{i}"} for i in range(50)], 1, 1)

        client = make_client(fake_get_json)
        pages = await collect_pages(client)
        assert len(pages) == 1

    @pytest.mark.asyncio
    async def test_stale_page_index_stops(self):
        """If pageIndex stops advancing despite a new page request, stop."""
        requested: list[int] = []

        async def fake_get_json(path, params):
            requested.append(int(params["page"]))
            return make_page([{"$ref": f"/a/{int(params['page'])}"} for i in range(10)], 1, 5)

        client = make_client(fake_get_json)
        pages = await collect_pages(client)

        assert len(pages) == 2
        assert requested == [1, 2]
