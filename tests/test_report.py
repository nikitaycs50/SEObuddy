from datetime import datetime
from pathlib import Path

from seobuddy.checks.robots_check import audit_robots
from seobuddy.checks.sitemap_check import audit_sitemap
from seobuddy.models import PageAudit, SiteAudit
from seobuddy.report import report_filename, write_report
from seobuddy.site_resources import RobotsInfo, SitemapInfo
from helpers import page_with_html
from seobuddy.auditor import audit_page
from seobuddy.models import AuditConfig, SiteContext
import pytest


def test_report_filename():
    name = report_filename("example.com", datetime(2024, 6, 4, 15, 30))
    assert name == "202406041530-example.com-report.md"


@pytest.mark.asyncio
async def test_write_report_sections(tmp_path: Path):
    page = page_with_html("<html><head><title>Test Title Here For Page</title></head><body><h1>x</h1></body></html>")
    ctx = SiteContext()
    audit = await audit_page(page, ctx, AuditConfig())
    robots = RobotsInfo(
        url="https://example.com/robots.txt",
        status_code=200,
        raw_text="User-agent: *\nAllow: /\n",
        user_agent="*",
    )
    site = SiteAudit(
        seed_url="https://example.com/",
        hostname="example.com",
        pages=[audit],
        site_results={
            "robots": audit_robots(robots, "https://example.com/"),
            "sitemap": await audit_sitemap(
                SitemapInfo(urls={"https://example.com/"}),
                {"https://example.com/"},
            ),
        },
        started_at=datetime(2024, 6, 4, 15, 30),
        elapsed_s=1.0,
    )
    path = write_report(site, tmp_path)
    text = path.read_text()
    assert "Executive Summary" in text
    assert "Score Breakdown" in text
    assert "| Robots.txt |" in text
    assert "| Sitemap |" in text
    assert "Site-wide Checks" not in text
    assert "Page-by-Page" in text
    assert "Recommendations" in text
    assert "Created by NikitaY.com" in text
