"""Canonical URL check."""

from __future__ import annotations

from urllib.parse import urlparse

from bs4 import BeautifulSoup

from seobuddy.checks.base import CATEGORY_WEIGHTS, clamp_score, status_from_score
from seobuddy.models import CheckResult, CheckStatus, PageData, SiteContext
from seobuddy.url_utils import normalize_url


def check(soup: BeautifulSoup, page: PageData, context: SiteContext) -> CheckResult:
    weight = CATEGORY_WEIGHTS["canonical"]
    findings: list[str] = []
    suggestions: list[str] = []

    tag = soup.find("link", rel=lambda r: r and "canonical" in r.lower())
    href = (tag.get("href") or "").strip() if tag else ""

    if not href:
        return CheckResult(
            name="canonical",
            score=0,
            weight=weight,
            status=CheckStatus.FAIL,
            findings=["Missing canonical link tag"],
            suggestions=["Add <link rel='canonical' href='...'> pointing to preferred URL"],
        )

    parsed = urlparse(href)
    if not parsed.scheme:
        return CheckResult(
            name="canonical",
            score=40,
            weight=weight,
            status=CheckStatus.WARN,
            findings=["Canonical URL is not absolute"],
            suggestions=["Use absolute URL in canonical tag"],
        )

    norm_canonical = normalize_url(href) or href
    norm_page = normalize_url(page.final_url) or page.final_url

    if norm_canonical == norm_page:
        score = 100
        findings.append("Canonical points to this page")
    else:
        score = 70
        findings.append(f"Canonical points elsewhere: {href}")
        suggestions.append("Ensure canonical matches preferred URL for this content")

    context.canonicals_seen.add(norm_canonical)
    score = clamp_score(score)

    return CheckResult(
        name="canonical",
        score=score,
        weight=weight,
        status=status_from_score(score),
        findings=findings,
        suggestions=suggestions,
    )
