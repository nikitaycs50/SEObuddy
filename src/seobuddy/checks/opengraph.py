"""Open Graph meta tags check."""

from __future__ import annotations

from bs4 import BeautifulSoup

from seobuddy.checks.base import CATEGORY_WEIGHTS, clamp_score, status_from_score
from seobuddy.models import CheckResult, CheckStatus, PageData, SiteContext

OG_TAGS = ("og:title", "og:description", "og:image", "og:url")


def check(soup: BeautifulSoup, page: PageData, context: SiteContext) -> CheckResult:
    weight = CATEGORY_WEIGHTS["opengraph"]
    findings: list[str] = []
    suggestions: list[str] = []
    score = 0

    for prop in OG_TAGS:
        tag = soup.find("meta", property=prop) or soup.find("meta", attrs={"name": prop})
        content = (tag.get("content") or "").strip() if tag else ""
        if content:
            score += 25
            findings.append(f"{prop} present")
        else:
            findings.append(f"Missing {prop}")
            suggestions.append(f"Add meta property='{prop}'")

    score = clamp_score(score)
    return CheckResult(
        name="opengraph",
        score=score,
        weight=weight,
        status=status_from_score(score),
        findings=findings,
        suggestions=suggestions,
    )
