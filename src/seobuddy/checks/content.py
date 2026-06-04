"""Content quality check (word count, text/HTML ratio)."""

from __future__ import annotations

from bs4 import BeautifulSoup

from seobuddy.checks.base import CATEGORY_WEIGHTS, clamp_score, status_from_score
from seobuddy.models import CheckResult, CheckStatus, PageData, SiteContext


def _word_count(soup: BeautifulSoup) -> int:
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()
    text = soup.get_text(separator=" ", strip=True)
    words = [w for w in text.split() if w]
    return len(words)


def check(soup: BeautifulSoup, page: PageData, context: SiteContext) -> CheckResult:
    weight = CATEGORY_WEIGHTS["content"]
    findings: list[str] = []
    suggestions: list[str] = []

    # Parse copy so word-count decompose does not mutate caller's soup
    from bs4 import BeautifulSoup as BS

    words = _word_count(BS(str(soup), "lxml"))

    if words < 300:
        word_score = 0
        findings.append(f"Thin content ({words} words; minimum 300)")
        suggestions.append("Add substantive content (300+ words)")
    elif words < 500:
        word_score = 60
        findings.append(f"Moderate content ({words} words)")
    elif words < 800:
        word_score = 80
        findings.append(f"Good content depth ({words} words)")
    else:
        word_score = 100
        findings.append(f"Strong content depth ({words} words)")

    html_len = len(page.html or "")
    visible = soup.get_text(separator=" ", strip=True)
    ratio = (len(visible) / html_len * 100) if html_len else 0

    ratio_score = 100 if ratio >= 15 else max(0, int(ratio / 15 * 100))
    if ratio < 15:
        findings.append(f"Low text/HTML ratio ({ratio:.1f}%; aim ≥15%)")
        suggestions.append("Reduce boilerplate markup; increase visible text")

    score = clamp_score((word_score + ratio_score) / 2)

    return CheckResult(
        name="content",
        score=score,
        weight=weight,
        status=status_from_score(score),
        findings=findings,
        suggestions=suggestions,
    )
