"""Internal links and anchor text check."""

from __future__ import annotations

from urllib.parse import urlparse

from bs4 import BeautifulSoup
import httpx

from seobuddy.checks.base import CATEGORY_WEIGHTS, clamp_score, status_from_score
from seobuddy.models import AuditConfig, CheckResult, CheckStatus, PageData, SiteContext
from seobuddy.url_utils import normalize_url, same_domain

GENERIC_ANCHORS = frozenset(
    {
        "click here",
        "read more",
        "here",
        "more",
        "link",
        "learn more",
    }
)

MAX_LINK_PROBES = 20


async def _probe_url(client: httpx.AsyncClient, url: str) -> int:
    try:
        resp = await client.head(url, follow_redirects=True)
        if resp.status_code == 405:
            resp = await client.get(url, follow_redirects=True)
        return resp.status_code
    except httpx.HTTPError:
        return 0


async def check_async(
    soup: BeautifulSoup,
    page: PageData,
    context: SiteContext,
    config: AuditConfig,
    client: httpx.AsyncClient | None,
) -> CheckResult:
    weight = CATEGORY_WEIGHTS["links"]
    findings: list[str] = []
    suggestions: list[str] = []

    seed_netloc = urlparse(page.final_url).netloc

    internal_urls: list[str] = []
    generic_count = 0

    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        norm = normalize_url(href, page.final_url)
        if not norm:
            continue
        anchor = a.get_text(strip=True).lower()
        if anchor in GENERIC_ANCHORS:
            generic_count += 1
        if same_domain(norm, seed_netloc):
            internal_urls.append(norm)

    unique_internal = list(dict.fromkeys(internal_urls))[:MAX_LINK_PROBES]

    broken = 0
    checked = 0
    if client and unique_internal:
        for url in unique_internal:
            if url in context.fetched_urls:
                continue
            status = await _probe_url(client, url)
            checked += 1
            if status == 0 or status >= 400:
                broken += 1
                findings.append(f"Broken internal link: {url} (status {status or 'error'})")

    if unique_internal and not client:
        findings.append("Link probe skipped (no HTTP client)")

    if generic_count:
        findings.append(f"Generic anchor text on {generic_count} link(s)")
        suggestions.append('Use descriptive anchor text instead of "click here"')

    if not unique_internal:
        score = 80
        findings.append("No internal links to verify")
    elif checked == 0:
        # All targets already crawled
        score = 100 if generic_count == 0 else 85
    else:
        pct_ok = (checked - broken) / checked
        score = clamp_score(pct_ok * 100)
        if generic_count:
            score = clamp_score(score - min(20, generic_count * 5))

    if broken:
        suggestions.append("Fix or remove broken internal links")

    return CheckResult(
        name="links",
        score=score,
        weight=weight,
        status=status_from_score(score),
        findings=findings or ["Internal links look healthy"],
        suggestions=suggestions,
    )


def check(soup: BeautifulSoup, page: PageData, context: SiteContext) -> CheckResult:
    """Sync stub — auditor uses check_async."""
    return CheckResult(
        name="links",
        score=80,
        weight=CATEGORY_WEIGHTS["links"],
        status=CheckStatus.WARN,
        findings=["Links check requires async client"],
    )
