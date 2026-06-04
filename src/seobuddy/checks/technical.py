"""Technical SEO check (viewport, HTTPS, URL structure)."""

from __future__ import annotations

from urllib.parse import urlparse

from bs4 import BeautifulSoup

from seobuddy.checks.base import CATEGORY_WEIGHTS, clamp_score, status_from_score
from seobuddy.models import CheckResult, CheckStatus, PageData, SiteContext


def check(soup: BeautifulSoup, page: PageData, context: SiteContext) -> CheckResult:
    weight = CATEGORY_WEIGHTS["technical"]
    findings: list[str] = []
    suggestions: list[str] = []
    score = 100

    viewport = soup.find("meta", attrs={"name": "viewport"})
    if not viewport or not (viewport.get("content") or "").strip():
        score -= 25
        findings.append("Missing viewport meta tag")
        suggestions.append("Add <meta name='viewport' content='width=device-width, initial-scale=1'>")

    parsed = urlparse(page.final_url)
    if parsed.scheme != "https":
        score -= 25
        findings.append("Page not served over HTTPS")
        suggestions.append("Use HTTPS for all pages")

    path = parsed.path or "/"
    if len(path) > 75:
        score -= 25
        findings.append(f"URL path long ({len(path)} chars; aim <75)")
        suggestions.append("Shorten URL paths where possible")

    if " " in path or "%20" in path.lower():
        score -= 25
        findings.append("Spaces in URL path")
        suggestions.append("Use hyphens instead of spaces in URLs")

    if not findings:
        findings.append("Technical basics look good")

    score = clamp_score(score)
    return CheckResult(
        name="technical",
        score=score,
        weight=weight,
        status=status_from_score(score),
        findings=findings,
        suggestions=suggestions,
    )
