import pytest
import httpx

from seobuddy.auditor import audit_page
from seobuddy.models import AuditConfig, SiteContext
from helpers import page_with_html

META_DESC = "x" * 155
WORDS = " ".join(["word"] * 400)

GOOD_HTML = f"""<!DOCTYPE html>
<html>
<head>
  <title>Best Example Page Title Here For SEO Testing</title>
  <meta name="description" content="{META_DESC}">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <link rel="canonical" href="https://example.com/">
  <meta property="og:title" content="T">
  <meta property="og:description" content="D">
  <meta property="og:image" content="https://example.com/i.png">
  <meta property="og:url" content="https://example.com/">
  <script type="application/ld+json">{{"@type":"WebSite","name":"Ex","url":"https://example.com"}}</script>
</head>
<body>
  <h1>Hello</h1>
  <h2>World</h2>
  <p>{WORDS}</p>
  <img src="/a.png" alt="diagram">
  <a href="/about">About us</a>
</body>
</html>"""


@pytest.mark.asyncio
async def test_audit_page_scores_reasonably():
    page = page_with_html(GOOD_HTML)
    config = AuditConfig()
    ctx = SiteContext()
    async with httpx.AsyncClient() as client:
        audit = await audit_page(page, ctx, config, client)
    assert audit.score >= 50
    assert "title" in audit.results
