import pytest

from seobuddy.checks.sitemap_check import audit_sitemap
from seobuddy.site_resources import SitemapInfo


@pytest.mark.asyncio
async def test_audit_sitemap_empty():
    info = SitemapInfo(sources=["https://example.com/sitemap.xml"], errors=["HTTP 404"])
    result = await audit_sitemap(info, set())
    assert result.score < 80


@pytest.mark.asyncio
async def test_audit_sitemap_coverage():
    info = SitemapInfo(
        sources=["https://example.com/sitemap.xml"],
        urls={"https://example.com/", "https://example.com/about"},
    )
    crawled = {"https://example.com/"}
    result = await audit_sitemap(info, crawled, client=None)
    assert any("coverage" in f.lower() for f in result.findings)
    assert result.score == 100
