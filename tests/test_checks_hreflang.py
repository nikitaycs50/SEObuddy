from bs4 import BeautifulSoup

from seobuddy.checks.hreflang import check, validate_hreflang_reciprocity
from seobuddy.models import PageAudit, PageData, SiteContext
from helpers import page_with_html


def test_hreflang_none_passes():
    html = "<html><head><title>T</title></head><body></body></html>"
    soup = BeautifulSoup(html, "lxml")
    page = page_with_html(html)
    ctx = SiteContext()
    result = check(soup, page, ctx)
    assert result.score == 100
    assert "No hreflang" in result.findings[0]


def test_hreflang_missing_x_default():
    html = """<html><head>
      <link rel="alternate" hreflang="en" href="https://example.com/en">
      <link rel="alternate" hreflang="de" href="https://example.com/de">
    </head></html>"""
    soup = BeautifulSoup(html, "lxml")
    page = page_with_html(html, final_url="https://example.com/")
    ctx = SiteContext()
    result = check(soup, page, ctx)
    assert any("x-default" in f for f in result.findings)


def test_hreflang_reciprocity():
    html_a = """<html><head>
      <link rel="alternate" hreflang="en" href="https://example.com/en">
      <link rel="alternate" hreflang="x-default" href="https://example.com/">
      <link rel="alternate" hreflang="en" href="https://example.com/">
    </head></html>"""
    html_b = """<html><head>
      <link rel="alternate" hreflang="de" href="https://example.com/de">
    </head></html>"""
    ctx = SiteContext()
    pa = PageAudit(
        page=page_with_html(html_a, final_url="https://example.com/"),
        results={},
        score=0,
        path_display="/",
    )
    pb = PageAudit(
        page=page_with_html(html_b, final_url="https://example.com/en"),
        results={},
        score=0,
        path_display="/en",
    )
    from seobuddy.checks.hreflang import check

    pa.results["hreflang"] = check(BeautifulSoup(html_a, "lxml"), pa.page, ctx)
    pb.results["hreflang"] = check(BeautifulSoup(html_b, "lxml"), pb.page, ctx)
    validate_hreflang_reciprocity(ctx, [pa, pb])
    assert any("return hreflang" in f for f in pa.results["hreflang"].findings)
