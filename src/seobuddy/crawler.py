"""Async BFS crawler with depth control."""

from __future__ import annotations

import asyncio
import time
from collections import deque
from collections.abc import AsyncIterator
from urllib.parse import urlparse

import httpx
from bs4 import BeautifulSoup

from seobuddy.models import AuditConfig, PageData
from seobuddy.url_utils import normalize_url, same_domain


def _is_html_response(headers: dict[str, str], body: str) -> bool:
    ct = (headers.get("content-type") or "").lower()
    if "text/html" in ct or "application/xhtml" in ct:
        return True
    if not ct and body.lstrip()[:1] in ("<",):
        return True
    return False


def extract_internal_links(html: str, base_url: str, seed_netloc: str) -> list[str]:
    soup = BeautifulSoup(html, "lxml")
    links: list[str] = []
    for a in soup.find_all("a", href=True):
        norm = normalize_url(a["href"].strip(), base_url)
        if norm and same_domain(norm, seed_netloc):
            links.append(norm)
    return links


class AsyncCrawler:
    def __init__(
        self,
        config: AuditConfig,
        transport: httpx.AsyncBaseTransport | None = None,
    ):
        self.config = config
        self._transport = transport
        self._visited: set[str] = set()
        self.fetched_urls: set[str] = set()

    async def crawl(self, start_url: str) -> AsyncIterator[PageData]:
        normalized_start = normalize_url(start_url)
        if not normalized_start:
            raise ValueError(f"Invalid URL: {start_url}")

        parsed = urlparse(normalized_start)
        seed_netloc = parsed.netloc
        max_depth = self.config.depth

        queue: deque[tuple[str, int]] = deque([(normalized_start, 0)])
        self._visited.add(normalized_start)
        self.fetched_urls.add(normalized_start)

        timeout = httpx.Timeout(self.config.timeout)
        headers = {"User-Agent": self.config.user_agent}

        client_kwargs: dict = {
            "follow_redirects": True,
            "max_redirects": self.config.max_redirects,
            "timeout": timeout,
            "headers": headers,
        }
        if self._transport is not None:
            client_kwargs["transport"] = self._transport

        async with httpx.AsyncClient(**client_kwargs) as client:
            sem = asyncio.Semaphore(self.config.concurrency)

            while queue:
                batch: list[tuple[str, int]] = []
                while queue and len(batch) < self.config.concurrency:
                    batch.append(queue.popleft())

                tasks = [
                    self._fetch_page(client, sem, url, depth, seed_netloc, max_depth, queue)
                    for url, depth in batch
                ]
                results = await asyncio.gather(*tasks)
                for page in results:
                    if page:
                        yield page

    async def _fetch_page(
        self,
        client: httpx.AsyncClient,
        sem: asyncio.Semaphore,
        url: str,
        depth: int,
        seed_netloc: str,
        max_depth: int,
        queue: deque[tuple[str, int]],
    ) -> PageData | None:
        async with sem:
            start = time.perf_counter()
            redirect_chain: list[str] = []
            try:
                resp = await client.get(url)
                redirect_chain = [str(r.url) for r in resp.history]
            except httpx.ConnectError:
                raise
            except httpx.HTTPError:
                elapsed = int((time.perf_counter() - start) * 1000)
                return PageData(
                    url=url,
                    final_url=url,
                    status_code=0,
                    headers={},
                    html="",
                    fetch_ms=elapsed,
                    redirect_chain=redirect_chain,
                )

            elapsed = int((time.perf_counter() - start) * 1000)
            hdrs = {k.lower(): v for k, v in resp.headers.items()}
            body = resp.text if resp.status_code < 400 else ""
            final = str(resp.url)
            norm_final = normalize_url(final) or final
            self.fetched_urls.add(norm_final)

            page = PageData(
                url=url,
                final_url=final,
                status_code=resp.status_code,
                headers=hdrs,
                html=body,
                fetch_ms=elapsed,
                redirect_chain=redirect_chain,
            )

            if (
                depth < max_depth
                and resp.status_code < 400
                and body
                and _is_html_response(hdrs, body)
            ):
                for link in extract_internal_links(body, final, seed_netloc):
                    if link not in self._visited:
                        self._visited.add(link)
                        self.fetched_urls.add(link)
                        queue.append((link, depth + 1))

            return page
