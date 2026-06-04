from seobuddy.checks import headings
from helpers import make_soup, page_with_html


def test_single_h1(context):
    soup = make_soup("<html><h1>Main</h1><h2>Sub</h2></html>")
    r = headings.check(soup, page_with_html(""), context)
    assert r.score >= 80


def test_no_h1(context):
    soup = make_soup("<html><h2>Only h2</h2></html>")
    r = headings.check(soup, page_with_html(""), context)
    assert r.score < 80
