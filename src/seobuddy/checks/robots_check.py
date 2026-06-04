"""Site-wide robots.txt audit."""

from __future__ import annotations

from seobuddy.checks.base import clamp_score, status_from_score
from seobuddy.models import CheckResult
from seobuddy.site_resources import RobotsInfo

SITE_WEIGHT = 1.0


def audit_robots(robots: RobotsInfo, seed_url: str) -> CheckResult:
    findings: list[str] = []
    suggestions: list[str] = []
    score = 100

    if robots.fetch_error:
        score = 20
        findings.append(f"Could not fetch robots.txt: {robots.fetch_error}")
        suggestions.append("Ensure /robots.txt is reachable over HTTPS")
    elif robots.status_code != 200:
        score = 30
        findings.append(f"robots.txt returned HTTP {robots.status_code}")
        suggestions.append("Publish a valid robots.txt at /robots.txt")
    elif not robots.raw_text.strip():
        score = 50
        findings.append("robots.txt is empty")
        suggestions.append("Add User-agent rules and optional Sitemap directive")
    else:
        findings.append("robots.txt is present and parseable")
        if not robots.sitemap_directives:
            score -= 15
            findings.append("No Sitemap: directive in robots.txt")
            suggestions.append("Add Sitemap: https://example.com/sitemap.xml")

    if robots.available and not robots.can_fetch(seed_url):
        score = min(score, 25)
        findings.append("Seed URL is disallowed for this User-Agent in robots.txt")
        suggestions.append(
            "Allow the seed path in robots.txt or use a User-Agent that is permitted"
        )

    score = clamp_score(score)
    return CheckResult(
        name="robots",
        score=score,
        weight=SITE_WEIGHT,
        status=status_from_score(score),
        findings=findings,
        suggestions=suggestions,
    )
