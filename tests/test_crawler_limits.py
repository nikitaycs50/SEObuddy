import pytest
import httpx

from seobuddy.crawler import AsyncCrawler
from seobuddy.models import AuditConfig


@pytest.mark.asyncio
async def test_max_pages_cap():
    bodies: dict[str, str] = {}
    for i in range(8):
        next_href = f"/p{i+1}" if i < 7 else ""
        bodies[f"https://example.com/p{i}"] = (
            f'<html><a href="{next_href}">next</a></html>' if next_href else "<html>done</html>"
        )

    async def mock_handler(request: httpx.Request) -> httpx.Response:
        url = str(request.url)
        if url in bodies:
            return httpx.Response(200, text=bodies[url], headers={"content-type": "text/html"})
        return httpx.Response(404)

    transport = httpx.MockTransport(mock_handler)
    config = AuditConfig(depth=10, max_pages=3, concurrency=1, timeout=5)
    crawler = AsyncCrawler(config, transport=transport)

    collected = []
    async for page in crawler.crawl("https://example.com/p0"):
        collected.append(page)

    assert len(collected) == 3
    assert crawler.crawl_capped is True
