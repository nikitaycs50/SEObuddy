from seobuddy.checks import jsonld
from helpers import make_soup, page_with_html


def test_no_jsonld(context):
    soup = make_soup("<html></html>")
    r = jsonld.check(soup, page_with_html(""), context)
    assert r.score == 0


def test_valid_organization(context):
    html = """
    <script type="application/ld+json">
    {"@type": "Organization", "name": "Acme", "url": "https://acme.com"}
    </script>
    """
    soup = make_soup(html)
    r = jsonld.check(soup, page_with_html(html), context)
    assert r.score == 100


def test_invalid_json(context):
    html = '<script type="application/ld+json">{bad</script>'
    soup = make_soup(html)
    r = jsonld.check(soup, page_with_html(html), context)
    assert r.score == 0
