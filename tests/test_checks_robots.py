from seobuddy.checks.robots_check import audit_robots
from seobuddy.site_resources import RobotsInfo


def test_audit_robots_missing():
    robots = RobotsInfo(url="https://example.com/robots.txt", status_code=404)
    result = audit_robots(robots, "https://example.com/")
    assert result.score < 80
    assert any("404" in f for f in result.findings)


def test_audit_robots_seed_disallowed():
    robots = RobotsInfo(
        url="https://example.com/robots.txt",
        status_code=200,
        raw_text="User-agent: *\nDisallow: /\n",
        user_agent="*",
    )
    result = audit_robots(robots, "https://example.com/")
    assert result.score < 80
    assert any("disallowed" in f.lower() for f in result.findings)


def test_audit_robots_ok():
    robots = RobotsInfo(
        url="https://example.com/robots.txt",
        status_code=200,
        raw_text="User-agent: *\nAllow: /\nSitemap: https://example.com/sitemap.xml\n",
        user_agent="*",
    )
    result = audit_robots(robots, "https://example.com/")
    assert result.score >= 80
