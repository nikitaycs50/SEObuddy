from seobuddy.checks import meta
from helpers import make_soup, page_with_html


def test_missing_meta(context):
    soup = make_soup("<html></html>")
    page = page_with_html("<html></html>")
    r = meta.check(soup, page, context)
    assert r.score == 0


def test_optimal_meta(context):
    desc = "x" * 155
    html = f'<meta name="description" content="{desc}">'
    soup = make_soup(f"<html><head>{html}</head></html>")
    page = page_with_html(html)
    r = meta.check(soup, page, context)
    assert r.score == 100
