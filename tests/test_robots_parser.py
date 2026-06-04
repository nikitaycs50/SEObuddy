from seobuddy.site_resources import RobotsInfo, _extract_sitemap_directives


def test_extract_sitemap_directives():
    text = "User-agent: *\nDisallow: /private\nSitemap: https://example.com/sitemap.xml\n"
    assert _extract_sitemap_directives(text) == ["https://example.com/sitemap.xml"]


def test_robots_can_fetch_disallow():
    robots = RobotsInfo(
        url="https://example.com/robots.txt",
        status_code=200,
        raw_text="User-agent: *\nDisallow: /private\n",
        user_agent="TestBot",
    )
    assert robots.can_fetch("https://example.com/")
    assert not robots.can_fetch("https://example.com/private/page")


def test_robots_unavailable_allows_all():
    robots = RobotsInfo(
        url="https://example.com/robots.txt",
        status_code=404,
        raw_text="",
        user_agent="TestBot",
    )
    assert robots.can_fetch("https://example.com/anything")
