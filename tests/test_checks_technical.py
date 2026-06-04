from seobuddy.checks import technical
from helpers import make_soup, page_with_html


def test_https_viewport(context):
    html = '<meta name="viewport" content="width=device-width">'
    soup = make_soup(html)
    page = page_with_html(html, url="https://example.com/short")
    r = technical.check(soup, page, context)
    assert r.score == 100


def test_http_penalty(context):
    soup = make_soup("<html></html>")
    page = page_with_html("", url="http://example.com/page")
    r = technical.check(soup, page, context)
    assert r.score < 100
