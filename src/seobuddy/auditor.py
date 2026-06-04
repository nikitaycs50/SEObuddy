"""Orchestrates all SEO checks for a single page."""

from __future__ import annotations

import httpx
from bs4 import BeautifulSoup

from seobuddy.checks import (
    canonical,
    content,
    headings,
    images,
    jsonld,
    links,
    meta,
    opengraph,
    technical,
    title,
)
from seobuddy.checks.base import CATEGORY_ORDER, weighted_page_score
from seobuddy.html_utils import is_html_content, parse_html
from seobuddy.models import AuditConfig, CheckResult, CheckStatus, PageAudit, PageData, SiteContext
from seobuddy.url_utils import path_display


def _empty_result(name: str, weight: float) -> CheckResult:
    from seobuddy.checks.base import CATEGORY_WEIGHTS

    w = CATEGORY_WEIGHTS.get(name, weight)
    return CheckResult(
        name=name,
        score=0,
        weight=w,
        status=CheckStatus.FAIL,
        findings=["No HTML content to analyze"],
        suggestions=[],
    )


def _minimal_soup() -> BeautifulSoup:
    return BeautifulSoup("<html></html>", "lxml")


async def audit_page(
    page: PageData,
    context: SiteContext,
    config: AuditConfig,
    client: httpx.AsyncClient | None = None,
) -> PageAudit:
    html = page.html or ""
    content_type = page.headers.get("content-type") or ""
    is_html = page.status_code < 400 and html.strip() and is_html_content(content_type, html)

    soup = parse_html(html, content_type) if is_html else None
    results: dict[str, CheckResult] = {}

    if not soup:
        from seobuddy.checks.base import CATEGORY_WEIGHTS

        for cat in CATEGORY_ORDER:
            if cat == "technical":
                results[cat] = technical.check(_minimal_soup(), page, context)
            else:
                results[cat] = _empty_result(cat, CATEGORY_WEIGHTS[cat])
    else:
        results["title"] = title.check(soup, page, context)
        results["meta"] = meta.check(soup, page, context)
        results["opengraph"] = opengraph.check(soup, page, context)
        results["jsonld"] = jsonld.check(soup, page, context)
        results["headings"] = headings.check(soup, page, context)
        results["content"] = content.check(soup, page, context)
        results["links"] = await links.check_async(soup, page, context, config, client)
        results["images"] = images.check(soup, page, context)
        results["canonical"] = canonical.check(soup, page, context)
        results["technical"] = technical.check(soup, page, context)

    score = weighted_page_score(results)
    return PageAudit(
        page=page,
        results=results,
        score=score,
        path_display=path_display(page.final_url),
    )
