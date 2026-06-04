"""Site-wide XML sitemap audit."""

from __future__ import annotations

import random

import httpx

from seobuddy.checks.base import clamp_score, status_from_score
from seobuddy.models import CheckResult
from seobuddy.site_resources import SitemapInfo

SITE_WEIGHT = 1.0
MAX_SAMPLE_PROBES = 3
LOW_COVERAGE_PCT = 30


async def _sample_sitemap_urls(
    client: httpx.AsyncClient | None,
    urls: set[str],
    crawled: set[str],
) -> list[str]:
    if not client:
        return []
    candidates = [u for u in urls if u not in crawled]
    if not candidates:
        return []
    sample = random.sample(candidates, min(MAX_SAMPLE_PROBES, len(candidates)))
    broken: list[str] = []
    for url in sample:
        try:
            resp = await client.head(url, follow_redirects=True)
            if resp.status_code == 405:
                resp = await client.get(url, follow_redirects=True)
            if resp.status_code >= 400 or resp.status_code == 0:
                broken.append(url)
        except httpx.HTTPError:
            broken.append(url)
    return broken


async def audit_sitemap(
    sitemap: SitemapInfo,
    crawled_urls: set[str],
    client: httpx.AsyncClient | None = None,
) -> CheckResult:
    findings: list[str] = []
    suggestions: list[str] = []
    score = 100

    if not sitemap.sources:
        score = 20
        findings.append("No sitemap sources were checked")
        suggestions.append("Add Sitemap: in robots.txt or publish /sitemap.xml")
    elif not sitemap.urls:
        score = 35
        findings.append("Sitemap sources did not yield any same-host URLs")
        if sitemap.errors:
            for err in sitemap.errors[:3]:
                findings.append(err)
        suggestions.append("Fix sitemap XML and ensure <loc> URLs use your domain")
    else:
        findings.append(
            f"Sitemap lists {len(sitemap.urls)} URL(s) from {len(sitemap.sources)} file(s)"
        )
        if sitemap.errors:
            for err in sitemap.errors[:2]:
                findings.append(err)
                score -= 5

        overlap = len(sitemap.urls & crawled_urls)
        if sitemap.urls:
            pct = round(100 * overlap / len(sitemap.urls))
            findings.append(
                f"Crawl coverage: {overlap}/{len(sitemap.urls)} sitemap URLs ({pct}%)"
            )
            if pct < LOW_COVERAGE_PCT:
                score -= 20
                suggestions.append(
                    "Increase crawl depth/max-pages or ensure important URLs are linked internally"
                )

        broken = await _sample_sitemap_urls(client, sitemap.urls, crawled_urls)
        if broken:
            score -= 15
            findings.append(f"Sample sitemap URLs unreachable: {len(broken)}")
            suggestions.append("Fix broken URLs listed in the sitemap")

    if not findings:
        findings.append("Sitemap checks passed")

    score = clamp_score(score)
    return CheckResult(
        name="sitemap",
        score=score,
        weight=SITE_WEIGHT,
        status=status_from_score(score),
        findings=findings,
        suggestions=suggestions,
    )
