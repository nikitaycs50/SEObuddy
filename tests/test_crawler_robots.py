import pytest
import httpx

from seobuddy.crawler import AsyncCrawler
from seobuddy.models import AuditConfig
from seobuddy.site_resources import RobotsInfo


@pytest.mark.asyncio
async def test_crawler_skips_disallowed_paths():
    pages = {
        "https://example.com/": (
            200,
            '<html><a href="https://example.com/private">Private</a>'
            '<a href="https://example.com/ok">OK</a></html>',
            "text/html",
        ),
        "https://example.com/ok": (200, "<html>ok</html>", "text/html"),
    }

    async def mock_handler(request: httpx.Request) -> httpx.Response:
        url = str(request.url)
        if url in pages:
            status, body, ct = pages[url]
            return httpx.Response(status, text=body, headers={"content-type": ct})
        return httpx.Response(404)

    robots = RobotsInfo(
        url="https://example.com/robots.txt",
        status_code=200,
        raw_text="User-agent: *\nDisallow: /private\n",
        user_agent="*",
    )
    transport = httpx.MockTransport(mock_handler)
    config = AuditConfig(depth=2, concurrency=2, timeout=5)
    crawler = AsyncCrawler(config, transport=transport, robots=robots)

    collected = []
    async for page in crawler.crawl("https://example.com/"):
        collected.append(page)

    urls = {p.final_url for p in collected}
    assert "https://example.com/" in urls
    assert "https://example.com/ok" in urls
    assert not any("/private" in u for u in urls)
    assert crawler.skipped_robots >= 1
