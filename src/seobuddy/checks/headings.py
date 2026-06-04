"""Heading hierarchy check."""

from __future__ import annotations

import re

from bs4 import BeautifulSoup

from seobuddy.checks.base import CATEGORY_WEIGHTS, clamp_score, status_from_score
from seobuddy.models import CheckResult, CheckStatus, PageData, SiteContext


def check(soup: BeautifulSoup, page: PageData, context: SiteContext) -> CheckResult:
    weight = CATEGORY_WEIGHTS["headings"]
    findings: list[str] = []
    suggestions: list[str] = []
    score = 100

    h1s = [h for h in soup.find_all("h1") if h.get_text(strip=True)]
    if len(h1s) == 0:
        score = 20
        findings.append("No H1 heading found")
        suggestions.append("Add exactly one H1 with primary page topic")
    elif len(h1s) > 1:
        score = 40
        findings.append(f"Multiple H1 headings ({len(h1s)})")
        suggestions.append("Use a single H1 per page")
    else:
        findings.append("Single H1 present")

    # Hierarchy: collect heading levels in document order
    headings = soup.find_all(re.compile(r"^h[1-6]$", re.I))
    levels = []
    for h in headings:
        if h.name:
            levels.append(int(h.name[1]))

    gap_penalty = 0
    prev = 0
    for level in levels:
        if prev and level > prev + 1:
            gap_penalty += 20
            findings.append(f"Heading hierarchy skip (H{prev} → H{level})")
        prev = level

    score = clamp_score(max(0, score - gap_penalty))
    if gap_penalty and not suggestions:
        suggestions.append("Maintain sequential heading levels (e.g. H1 → H2 → H3)")

    return CheckResult(
        name="headings",
        score=score,
        weight=weight,
        status=status_from_score(score),
        findings=findings,
        suggestions=suggestions,
    )
