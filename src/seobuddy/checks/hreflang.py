"""Hreflang alternate link audit."""

from __future__ import annotations

import re
from urllib.parse import urlparse

from bs4 import BeautifulSoup

from seobuddy.checks.base import CATEGORY_WEIGHTS, clamp_score, status_from_score
from seobuddy.models import CheckResult, PageAudit, PageData, SiteContext
from seobuddy.url_utils import crawl_dedup_key, normalize_url

HREFLANG_RE = re.compile(
    r"^[a-z]{2,3}(?:-[A-Za-z0-9]{2,8})*$|^x-default$",
    re.IGNORECASE,
)
MAX_EDGES = 200


def _page_key(url: str) -> str:
    return crawl_dedup_key(url)


def _extract_alternates(soup: BeautifulSoup, page_url: str) -> list[tuple[str, str]]:
    alternates: list[tuple[str, str]] = []
    for link in soup.find_all("link", rel=lambda v: v and "alternate" in v):
        hreflang = (link.get("hreflang") or "").strip()
        href = (link.get("href") or "").strip()
        if not hreflang or not href:
            continue
        target = normalize_url(href, page_url) or href
        alternates.append((hreflang.lower(), target))
    return alternates


def check(soup: BeautifulSoup, page: PageData, context: SiteContext) -> CheckResult:
    weight = CATEGORY_WEIGHTS["hreflang"]
    findings: list[str] = []
    suggestions: list[str] = []
    score = 100

    alternates = _extract_alternates(soup, page.final_url)
    if not alternates:
        findings.append("No hreflang alternates")
        return CheckResult(
            name="hreflang",
            score=100,
            weight=weight,
            status=status_from_score(100),
            findings=findings,
            suggestions=suggestions,
        )

    from_key = _page_key(page.final_url)
    codes_seen: dict[str, str] = {}
    has_x_default = False
    lang_codes: set[str] = set()
    self_ref = False

    for code, target in alternates:
        if len(context.hreflang_edges) < MAX_EDGES:
            context.hreflang_edges.append((from_key, code, _page_key(target)))

        if not HREFLANG_RE.match(code):
            score -= 25
            findings.append(f"Invalid hreflang code: {code}")
            suggestions.append("Use BCP 47 tags (e.g. en, en-US) or x-default")

        if code in codes_seen and codes_seen[code] != target:
            score -= 20
            findings.append(f"Duplicate hreflang '{code}' with different hrefs")
        codes_seen[code] = target

        if code == "x-default":
            has_x_default = True
        else:
            lang_codes.add(code)

        parsed = urlparse(target)
        if not parsed.scheme:
            score -= 15
            findings.append(f"Non-absolute hreflang href: {target[:60]}")
            suggestions.append("Use absolute URLs in hreflang link tags")

        if _page_key(target) == from_key:
            self_ref = True

    if len(lang_codes) >= 2 and not has_x_default:
        score -= 20
        findings.append("Missing x-default with multiple language alternates")
        suggestions.append("Add <link rel='alternate' hreflang='x-default' href='...'>")

    if not self_ref:
        score -= 15
        findings.append("Page does not self-reference in hreflang cluster")
        suggestions.append("Include a self-referencing hreflang link for this URL")

    if not findings:
        findings.append(f"Hreflang cluster OK ({len(alternates)} alternate(s))")

    score = clamp_score(score)
    return CheckResult(
        name="hreflang",
        score=score,
        weight=weight,
        status=status_from_score(score),
        findings=findings,
        suggestions=suggestions,
    )


def validate_hreflang_reciprocity(
    context: SiteContext,
    pages: list[PageAudit],
) -> None:
    """Augment page hreflang results when return links are missing."""
    edges = context.hreflang_edges[:MAX_EDGES]
    if not edges:
        return

    by_from: dict[str, list[tuple[str, str]]] = {}
    for from_key, code, to_key in edges:
        by_from.setdefault(from_key, []).append((code, to_key))

    page_by_key: dict[str, PageAudit] = {}
    for pa in pages:
        page_by_key[_page_key(pa.page.final_url)] = pa

    missing: list[tuple[str, str, str]] = []
    for from_key, code, to_key in edges:
        if code == "x-default":
            continue
        back = by_from.get(to_key, [])
        if not any(c == code and t == from_key for c, t in back):
            missing.append((from_key, code, to_key))

    if not missing:
        return

    for from_key, code, to_key in missing[:10]:
        pa = page_by_key.get(from_key)
        if not pa:
            continue
        r = pa.results.get("hreflang")
        if not r:
            continue
        msg = f"Missing return hreflang '{code}' from {to_key}"
        if msg not in r.findings:
            r.findings.append(msg)
            r.suggestions.append(
                "Ensure each hreflang target page links back with the same hreflang code"
            )
            r.score = clamp_score(r.score - 15)
            r.status = status_from_score(r.score)
