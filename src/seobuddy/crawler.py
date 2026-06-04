"""Async BFS crawler with depth control."""

from __future__ import annotations

import asyncio
import time
from collections import deque
from collections.abc import AsyncIterator
from urllib.parse import urlparse

import httpx

from seobuddy.html_utils import is_html_content, parse_html
from seobuddy.models import AuditConfig, PageData
from seobuddy.site_resources import RobotsInfo
from seobuddy.url_utils import crawl_dedup_key, is_crawlable_url, normalize_url, same_domain


def _is_html_response(headers: dict[str, str], body: str) -> bool:
    return is_html_content(headers.get("content-type") or "", body)


def extract_internal_links(html: str, base_url: str, seed_netloc: str) -> list[str]:
    soup = parse_html(html, "text/html")
    if not soup:
        return []
    links: list[str] = []
    for a in soup.find_all("a", href=True):
        norm = normalize_url(a["href"].strip(), base_url)
        if norm and same_domain(norm, seed_netloc) and is_crawlable_url(norm):
            links.append(norm)
    return links


class AsyncCrawler:
    def __init__(
        self,
        config: AuditConfig,
        transport: httpx.AsyncBaseTransport | None = None,
        robots: RobotsInfo | None = None,
    ):
        self.config = config
        self._transport = transport
        self._robots = robots
        self._visited: set[str] = set()
        self.fetched_urls: set[str] = set()
        self.pages_fetched = 0
        self.crawl_capped = False
        self.skipped_robots = 0

    def _try_enqueue(self, url: str, depth: int, queue: deque[tuple[str, int]]) -> None:
        if self.pages_fetched + len(queue) >= self.config.max_pages:
            return
        if self._robots and not self._robots.can_fetch(url):
            self.skipped_robots += 1
            return
        key = crawl_dedup_key(url)
        if key in self._visited:
            return
        self._visited.add(key)
        self.fetched_urls.add(url)
        queue.append((url, depth))

    async def crawl(self, start_url: str) -> AsyncIterator[PageData]:
        normalized_start = normalize_url(start_url)
        if not normalized_start:
            raise ValueError(f"Invalid URL: {start_url}")

        parsed = urlparse(normalized_start)
        seed_netloc = parsed.netloc
        max_depth = self.config.depth

        queue: deque[tuple[str, int]] = deque()
        self._try_enqueue(normalized_start, 0, queue)

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

            while queue and self.pages_fetched < self.config.max_pages:
                batch: list[tuple[str, int]] = []
                while queue and len(batch) < self.config.concurrency:
                    if self.pages_fetched + len(batch) >= self.config.max_pages:
                        break
                    batch.append(queue.popleft())

                if not batch:
                    break

                tasks = [
                    self._fetch_page(client, sem, url, depth, seed_netloc, max_depth, queue)
                    for url, depth in batch
                ]
                results = await asyncio.gather(*tasks)
                for page in results:
                    if page:
                        self.pages_fetched += 1
                        yield page
                        if self.pages_fetched >= self.config.max_pages:
                            self.crawl_capped = True
                            queue.clear()
                            return

            if queue and self.pages_fetched >= self.config.max_pages:
                self.crawl_capped = True

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
            norm_final = normalize_url(final)

            # Redirects may land on locale/utility URLs we would never enqueue
            if norm_final is None or not is_crawlable_url(norm_final):
                return None

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
                and self.pages_fetched < self.config.max_pages
            ):
                for link in extract_internal_links(body, final, seed_netloc):
                    self._try_enqueue(link, depth + 1, queue)

            return page
