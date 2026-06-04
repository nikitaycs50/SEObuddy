"""JSON-LD structured data check."""

from __future__ import annotations

import json

from bs4 import BeautifulSoup

from seobuddy.checks.base import CATEGORY_WEIGHTS, clamp_score, status_from_score
from seobuddy.models import CheckResult, CheckStatus, PageData, SiteContext

REQUIRED_FIELDS = {
    "Organization": ["name", "url"],
    "WebSite": ["name", "url"],
    "Article": ["headline", "url"],
    "NewsArticle": ["headline", "url"],
    "BlogPosting": ["headline", "url"],
}


def _schema_types(obj: dict) -> list[str]:
    t = obj.get("@type")
    if isinstance(t, list):
        return [str(x) for x in t]
    if t:
        return [str(t)]
    return []


def _validate_object(obj: dict) -> tuple[int, list[str]]:
    """Score a single JSON-LD object (0–100)."""
    findings: list[str] = []
    types = _schema_types(obj)
    if not types:
        return 50, ["JSON-LD block without @type"]

    best = 0
    for schema_type in types:
        required = REQUIRED_FIELDS.get(schema_type)
        if required:
            missing = [f for f in required if not obj.get(f)]
            if not missing:
                best = max(best, 100)
                findings.append(f"Valid {schema_type} with required fields")
            else:
                best = max(best, 50)
                findings.append(f"{schema_type} missing: {', '.join(missing)}")
        else:
            best = max(best, 70)
            findings.append(f"Detected @type {schema_type}")

    return best, findings


def check(soup: BeautifulSoup, page: PageData, context: SiteContext) -> CheckResult:
    weight = CATEGORY_WEIGHTS["jsonld"]
    findings: list[str] = []
    suggestions: list[str] = []

    scripts = soup.find_all("script", type="application/ld+json")
    if not scripts:
        return CheckResult(
            name="jsonld",
            score=0,
            weight=weight,
            status=CheckStatus.FAIL,
            findings=["No JSON-LD structured data found"],
            suggestions=["Add schema.org JSON-LD (Organization, WebSite, or Article)"],
        )

    scores: list[int] = []
    for script in scripts:
        raw = script.string or script.get_text() or ""
        try:
            data = json.loads(raw)
        except json.JSONDecodeError as e:
            findings.append(f"Invalid JSON-LD: {e}")
            scores.append(0)
            suggestions.append("Fix JSON syntax in application/ld+json script")
            continue

        items = data if isinstance(data, list) else [data]
        for obj in items:
            if isinstance(obj, dict):
                s, f = _validate_object(obj)
                scores.append(s)
                findings.extend(f)

    score = clamp_score(max(scores) if scores else 0)
    if score < 80 and not suggestions:
        suggestions.append("Add valid schema.org JSON-LD with required properties")

    return CheckResult(
        name="jsonld",
        score=score,
        weight=weight,
        status=status_from_score(score),
        findings=findings or ["JSON-LD present"],
        suggestions=suggestions,
    )
