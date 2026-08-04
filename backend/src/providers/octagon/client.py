"""Octagon API HTTP Client.

Minimal REST client — no auth, no $ref resolution, no pagination.
All data comes back in single responses.
"""

import logging
from dataclasses import dataclass, field
from typing import Any

import httpx

from src.providers.octagon.config import OctagonClientConfig

logger = logging.getLogger(__name__)


@dataclass
class OctagonClient:
    config: OctagonClientConfig = field(default_factory=OctagonClientConfig)
    _http: httpx.AsyncClient | None = field(default=None, init=False, repr=False)

    async def start(self) -> None:
        if self._http is None:
            self._http = httpx.AsyncClient(
                base_url=self.config.base_url,
                timeout=httpx.Timeout(self.config.request_timeout),
                headers={"User-Agent": self.config.user_agent},
            )

    async def close(self) -> None:
        if self._http:
            await self._http.aclose()
            self._http = None

    async def get(self, path: str) -> httpx.Response:
        if self._http is None:
            raise RuntimeError("OctagonClient not started")
        for attempt in range(self.config.max_retries + 1):
            try:
                response = await self._http.get(path)
                if response.is_success:
                    return response
                if response.status_code in (429, 500, 502, 503) and attempt < self.config.max_retries:
                    import asyncio
                    await asyncio.sleep(self.config.retry_backoff_base ** attempt)
                    continue
                response.raise_for_status()
            except (httpx.TimeoutException, httpx.ConnectError):
                if attempt < self.config.max_retries:
                    import asyncio
                    await asyncio.sleep(self.config.retry_backoff_base ** attempt)
                    continue
                raise
        raise httpx.HTTPError(f"Octagon: all {self.config.max_retries + 1} attempts failed")

    async def get_json(self, path: str) -> Any:
        response = await self.get(path)
        return response.json()
