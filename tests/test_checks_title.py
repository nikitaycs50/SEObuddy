from seobuddy.checks import title
from helpers import make_soup, page_with_html


def test_missing_title(context):
    soup = make_soup("<html><body></body></html>")
    page = page_with_html("<html></html>")
    r = title.check(soup, page, context)
    assert r.score == 0
    assert "Missing" in r.findings[0]


def test_optimal_title(context):
    t = "A" * 55
    soup = make_soup(f"<html><head><title>{t}</title></head></html>")
    page = page_with_html(f"<title>{t}</title>")
    r = title.check(soup, page, context)
    assert r.score == 100


def test_duplicate_title(context):
    t = "Duplicate Page Title Here For Testing SEO Buddy"
    soup = make_soup(f"<html><head><title>{t}</title></head></html>")
    page = page_with_html(f"<title>{t}</title>")
    context.titles_seen.add(t)
    r = title.check(soup, page, context)
    assert r.score <= 40
