from seobuddy.checks import opengraph
from helpers import make_soup, page_with_html


def test_no_og(context):
    soup = make_soup("<html></html>")
    r = opengraph.check(soup, page_with_html(""), context)
    assert r.score == 0


def test_all_og(context):
    html = """
    <meta property="og:title" content="T">
    <meta property="og:description" content="D">
    <meta property="og:image" content="https://x.com/i.png">
    <meta property="og:url" content="https://x.com">
    """
    soup = make_soup(html)
    r = opengraph.check(soup, page_with_html(html), context)
    assert r.score == 100
