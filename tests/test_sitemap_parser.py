from seobuddy.site_resources import _parse_sitemap_xml

URLSET = """<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url><loc>https://example.com/</loc></url>
  <url><loc>https://example.com/about</loc></url>
</urlset>"""

INDEX = """<?xml version="1.0" encoding="UTF-8"?>
<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <sitemap><loc>https://example.com/sitemap-pages.xml</loc></sitemap>
</sitemapindex>"""


def test_parse_urlset():
    urls, children, is_index = _parse_sitemap_xml(URLSET, "example.com")
    assert not is_index
    assert not children
    assert "https://example.com/" in urls
    assert "https://example.com/about" in urls


def test_parse_sitemap_index():
    urls, children, is_index = _parse_sitemap_xml(INDEX, "example.com")
    assert is_index
    assert urls == []
    assert "https://example.com/sitemap-pages.xml" in children
