"""TheSportsDB HTTP Client.

Simple rate-limited HTTP client — no $ref resolution, direct REST.
"""

import asyncio
import logging
import time
from dataclasses import dataclass, field
from typing import Any, cast

import httpx

from src.providers.tsdb.config import TSDBClientConfig, build_url

logger = logging.getLogger(__name__)


@dataclass
class TSDBClient:
    """Simple REST client for TheSportsDB v1 API."""

    config: TSDBClientConfig = field(default_factory=TSDBClientConfig)
    _http: httpx.AsyncClient | None = field(default=None, init=False, repr=False)
    _last_request_time: float = field(default=0.0, init=False, repr=False)
    _min_interval: float = field(init=False)

    def __post_init__(self) -> None:
        self._min_interval = 60.0 / self.config.rate_limit_per_minute

    async def start(self) -> None:
        if self._http is None:
            self._http = httpx.AsyncClient(
                timeout=httpx.Timeout(self.config.request_timeout),
                headers={"User-Agent": self.config.user_agent},
            )

    async def close(self) -> None:
        if self._http:
            await self._http.aclose()
            self._http = None

    async def _rate_limit(self) -> None:
        elapsed = time.monotonic() - self._last_request_time
        if elapsed < self._min_interval:
            await asyncio.sleep(self._min_interval - elapsed)
        self._last_request_time = time.monotonic()

    async def get(self, path: str, params: dict[str, Any] | None = None) -> httpx.Response:
        if self._http is None:
            raise RuntimeError("TSDBClient not started")
        url = build_url(self.config, path)
        for attempt in range(self.config.max_retries + 1):
            try:
                await self._rate_limit()
                response = await self._http.get(url, params=params)
                if response.is_success:
                    return response
                if response.status_code == 429:
                    wait = self.config.retry_backoff_base ** attempt
                    logger.warning(f"TSDB rate limited, waiting {wait}s (attempt {attempt + 1})")
                    if attempt < self.config.max_retries:
                        await asyncio.sleep(wait)
                        continue
                if response.status_code in self.config.retry_status_codes and attempt < self.config.max_retries:
                    await asyncio.sleep(self.config.retry_backoff_base ** attempt)
                    continue
                response.raise_for_status()
            except (httpx.TimeoutException, httpx.ConnectError):
                if attempt < self.config.max_retries:
                    await asyncio.sleep(self.config.retry_backoff_base ** attempt)
                    continue
                raise
        raise httpx.HTTPError(f"TSDB: all {self.config.max_retries + 1} attempts failed")

    async def get_json(self, path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        response = await self.get(path, params)
        return cast(dict[str, Any], response.json())
