"""Async httpx client for Malaysia's lom.agc.gov.my (Laws of Malaysia Online) with cache.

Keyless. Each Act page is server-rendered HTML embedding a pdf.js viewer; the full text is
only in the PDF it points at. ``robots.txt`` returned HTTP 500 on every probe in this session
(a server misconfiguration, not an explicit disallow) - there is no crawl policy to violate,
but this client still uses conservative retry/backoff and caches aggressively.
"""

from __future__ import annotations

import anyio
import httpx

from .cache import HttpCache

DEFAULT_BASE_URL = "https://lom.agc.gov.my"
DEFAULT_TIMEOUT = httpx.Timeout(90.0, connect=15.0)
USER_AGENT = "my-eli-mcp/0.1.0 (+https://github.com/matematicsolutions/my-eli-mcp)"

_RETRY_STATUS = frozenset({429, 500, 502, 503, 504})
_MAX_ATTEMPTS = 3


class LomClient:
    """Async client. Use as ``async with LomClient() as c: ...``."""

    def __init__(
        self,
        base_url: str = DEFAULT_BASE_URL,
        cache: HttpCache | None = None,
        timeout: httpx.Timeout = DEFAULT_TIMEOUT,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self._cache = cache or HttpCache()
        self._http = httpx.AsyncClient(
            timeout=timeout,
            headers={"User-Agent": USER_AGENT},
            follow_redirects=True,
        )

    async def __aenter__(self) -> LomClient:
        return self

    async def __aexit__(self, *_exc: object) -> None:
        await self.aclose()

    async def aclose(self) -> None:
        await self._http.aclose()
        self._cache.close()

    async def _request(self, url: str, *, accept: str) -> httpx.Response:
        last_exc: Exception | None = None
        for attempt in range(_MAX_ATTEMPTS):
            try:
                resp = await self._http.get(url, headers={"Accept": accept})
                resp.raise_for_status()
                return resp
            except httpx.HTTPStatusError as exc:
                last_exc = exc
                if exc.response.status_code not in _RETRY_STATUS or attempt == _MAX_ATTEMPTS - 1:
                    raise
            except (httpx.TransportError, httpx.TimeoutException) as exc:
                last_exc = exc
                if attempt == _MAX_ATTEMPTS - 1:
                    raise
            await anyio.sleep(0.5 * (2**attempt))
        assert last_exc is not None
        raise last_exc

    async def get_act_page(self, act_number: int, language: str = "BI") -> str:
        """Fetch the server-rendered Act page (HTML with a pdf.js viewer)."""
        url = f"{self.base_url}/act-detail.php?language={language}&act={act_number}"
        cached = self._cache.get(url)
        if cached is not None and isinstance(cached, str):
            return cached
        resp = await self._request(url, accept="text/html")
        text = resp.text
        self._cache.set(url, text, ttl=HttpCache.ttl_for("act"))
        return text

    async def get_pdf(self, relative_path: str) -> bytes:
        """Download the official Act PDF the viewer points at (resolved against this base_url)."""
        path = relative_path.lstrip("./")
        while path.startswith("../"):
            path = path[3:]
        url = f"{self.base_url}/{path}"
        cached = self._cache.get(url)
        if cached is not None and isinstance(cached, bytes):
            return cached
        resp = await self._request(url, accept="application/pdf")
        data = resp.content
        self._cache.set(url, data, ttl=HttpCache.ttl_for("act"))
        return data
