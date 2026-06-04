"""Meta description SEO check."""

from __future__ import annotations

from bs4 import BeautifulSoup

from seobuddy.checks.base import CATEGORY_WEIGHTS, clamp_score, status_from_score
from seobuddy.models import CheckResult, CheckStatus, PageData, SiteContext


def check(soup: BeautifulSoup, page: PageData, context: SiteContext) -> CheckResult:
    weight = CATEGORY_WEIGHTS["meta"]
    findings: list[str] = []
    suggestions: list[str] = []

    tag = soup.find("meta", attrs={"name": "description"})
    content = (tag.get("content") or "").strip() if tag else ""

    if not content:
        return CheckResult(
            name="meta",
            score=0,
            weight=weight,
            status=CheckStatus.FAIL,
            findings=["Missing meta description"],
            suggestions=["Add meta name='description' (150–160 characters)"],
        )

    length = len(content)
    length_score = 50
    if 150 <= length <= 160:
        length_score = 100
        findings.append(f"Meta description length optimal ({length} chars)")
    elif 120 <= length <= 149 or 161 <= length <= 180:
        length_score = 70
        findings.append(f"Meta description length acceptable ({length} chars)")
        suggestions.append("Adjust meta description to 150–160 characters")
    else:
        length_score = 40
        findings.append(f"Meta description length suboptimal ({length} chars)")
        suggestions.append("Aim for 150–160 characters in meta description")

    score = length_score
    if content.lower() in {m.lower() for m in context.metas_seen}:
        score = min(score, 40)
        findings.append("Duplicate meta description on another page")
        suggestions.append("Write a unique meta description per page")

    context.metas_seen.add(content)
    score = clamp_score(score)

    return CheckResult(
        name="meta",
        score=score,
        weight=weight,
        status=status_from_score(score),
        findings=findings,
        suggestions=suggestions,
    )
