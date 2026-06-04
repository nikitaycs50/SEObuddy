"""Title tag SEO check."""

from __future__ import annotations

from bs4 import BeautifulSoup

from seobuddy.checks.base import CATEGORY_WEIGHTS, clamp_score, status_from_score
from seobuddy.models import CheckResult, CheckStatus, PageData, SiteContext


def check(soup: BeautifulSoup, page: PageData, context: SiteContext) -> CheckResult:
    weight = CATEGORY_WEIGHTS["title"]
    findings: list[str] = []
    suggestions: list[str] = []

    tag = soup.find("title")
    text = tag.get_text(strip=True) if tag else ""

    if not text:
        return CheckResult(
            name="title",
            score=0,
            weight=weight,
            status=CheckStatus.FAIL,
            findings=["Missing or empty <title> tag"],
            suggestions=["Add a unique, descriptive <title> tag (50–60 characters)"],
        )

    length = len(text)
    length_score = 50
    if 50 <= length <= 60:
        length_score = 100
        findings.append(f"Title length optimal ({length} chars)")
    elif 30 <= length <= 49 or 61 <= length <= 70:
        length_score = 70
        findings.append(f"Title length acceptable ({length} chars; ideal 50–60)")
        suggestions.append("Adjust title length to 50–60 characters")
    else:
        length_score = 40
        findings.append(f"Title length suboptimal ({length} chars)")
        suggestions.append("Aim for 50–60 characters in the title tag")

    score = length_score
    if text.lower() in {t.lower() for t in context.titles_seen}:
        score = min(score, 40)
        findings.append("Duplicate title used on another page")
        suggestions.append("Use a unique title for each page")

    context.titles_seen.add(text)
    score = clamp_score(score)

    return CheckResult(
        name="title",
        score=score,
        weight=weight,
        status=status_from_score(score),
        findings=findings,
        suggestions=suggestions,
    )
