"""Image alt text and lazy loading check."""

from __future__ import annotations

from bs4 import BeautifulSoup

from seobuddy.checks.base import CATEGORY_WEIGHTS, clamp_score, status_from_score
from seobuddy.models import CheckResult, CheckStatus, PageData, SiteContext


def check(soup: BeautifulSoup, page: PageData, context: SiteContext) -> CheckResult:
    weight = CATEGORY_WEIGHTS["images"]
    findings: list[str] = []
    suggestions: list[str] = []

    imgs = soup.find_all("img")
    if not imgs:
        return CheckResult(
            name="images",
            score=100,
            weight=weight,
            status=CheckStatus.PASS,
            findings=["No images on page"],
        )

    with_alt = sum(1 for img in imgs if (img.get("alt") or "").strip())
    missing = len(imgs) - with_alt
    pct = with_alt / len(imgs) * 100
    score = clamp_score(pct)

    if missing:
        findings.append(f"{missing}/{len(imgs)} images missing alt text")
        suggestions.append("Add descriptive alt attributes to all images")

    lazy = any((img.get("loading") or "").lower() == "lazy" for img in imgs)
    if lazy:
        findings.append("Lazy loading detected on at least one image")

    if not missing:
        findings.append("All images have alt text")

    return CheckResult(
        name="images",
        score=score,
        weight=weight,
        status=status_from_score(score),
        findings=findings,
        suggestions=suggestions,
    )
