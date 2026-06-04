import pytest
import httpx

from seobuddy.crawler import AsyncCrawler, extract_internal_links
from seobuddy.models import AuditConfig
from seobuddy.url_utils import normalize_url


def test_normalize_strips_fragment():
    assert normalize_url("https://Example.com/path#frag") == "https://example.com/path"


def test_extract_internal_links():
    html = '<a href="/about">About</a><a href="https://other.com/x">X</a>'
    links = extract_internal_links(html, "https://example.com/", "example.com")
    assert "https://example.com/about" in links
    assert not any("other.com" in l for l in links)


@pytest.mark.asyncio
async def test_crawler_depth_and_dedup():
    pages = {
        "https://example.com/": (
            200,
            '<html><a href="https://example.com/about">About</a></html>',
            "text/html",
        ),
        "https://example.com/about": (200, "<html>about</html>", "text/html"),
    }

    async def mock_handler(request: httpx.Request) -> httpx.Response:
        url = str(request.url)
        if url in pages:
            status, body, ct = pages[url]
            return httpx.Response(status, text=body, headers={"content-type": ct})
        return httpx.Response(404)

    transport = httpx.MockTransport(mock_handler)
    config = AuditConfig(depth=1, concurrency=2, timeout=5)
    crawler = AsyncCrawler(config, transport=transport)

    collected = []
    async for page in crawler.crawl("https://example.com/"):
        collected.append(page)

    urls = {p.url for p in collected}
    assert "https://example.com/" in urls
    assert "https://example.com/about" in urls
    assert len(collected) == 2
