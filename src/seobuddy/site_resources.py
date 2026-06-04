"""Fetch and parse robots.txt and XML sitemaps."""

from __future__ import annotations

import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser

import httpx

from seobuddy.models import AuditConfig
from seobuddy.url_utils import hostname_from_url, normalize_url, same_domain
from urllib.parse import urlparse, urlunparse

MAX_SITEMAP_FILES = 5
MAX_SITEMAP_URLS = 5000


@dataclass
class RobotsInfo:
    url: str
    status_code: int = 0
    raw_text: str = ""
    fetch_error: str | None = None
    sitemap_directives: list[str] = field(default_factory=list)
    _parser: RobotFileParser | None = field(default=None, repr=False)
    user_agent: str = ""

    def _ensure_parser(self) -> RobotFileParser:
        if self._parser is None:
            parser = RobotFileParser()
            parser.parse(self.raw_text.splitlines() if self.raw_text else [])
            self._parser = parser
        return self._parser

    def can_fetch(self, url: str) -> bool:
        if self.status_code != 200 or not self.raw_text.strip():
            return True
        ua = self.user_agent or "*"
        return self._ensure_parser().can_fetch(ua, url)

    @property
    def available(self) -> bool:
        return self.status_code == 200 and bool(self.raw_text.strip())


@dataclass
class SitemapInfo:
    sources: list[str] = field(default_factory=list)
    urls: set[str] = field(default_factory=set)
    errors: list[str] = field(default_factory=list)

    @property
    def reachable(self) -> bool:
        return bool(self.urls) and not any("404" in e for e in self.errors[:1])


def _robots_url(seed_url: str) -> str:
    parsed = urlparse(seed_url)
    return f"{parsed.scheme}://{parsed.netloc}/robots.txt"


def _default_sitemap_url(seed_url: str) -> str:
    parsed = urlparse(seed_url)
    return f"{parsed.scheme}://{parsed.netloc}/sitemap.xml"


def _extract_sitemap_directives(text: str) -> list[str]:
    urls: list[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.lower().startswith("sitemap:"):
            loc = stripped.split(":", 1)[1].strip()
            if loc:
                urls.append(loc)
    return urls


def _build_robots(
    url: str,
    status_code: int,
    raw_text: str,
    user_agent: str,
    fetch_error: str | None = None,
) -> RobotsInfo:
    return RobotsInfo(
        url=url,
        status_code=status_code,
        raw_text=raw_text,
        fetch_error=fetch_error,
        sitemap_directives=_extract_sitemap_directives(raw_text),
        user_agent=user_agent,
    )


async def fetch_robots(
    client: httpx.AsyncClient,
    seed_url: str,
    config: AuditConfig,
) -> RobotsInfo:
    url = _robots_url(seed_url)
    try:
        resp = await client.get(url, follow_redirects=True)
        text = resp.text if resp.status_code == 200 else ""
        return _build_robots(url, resp.status_code, text, config.user_agent)
    except httpx.HTTPError as e:
        return _build_robots(url, 0, "", config.user_agent, fetch_error=str(e))


def _normalize_sitemap_loc(loc: str, seed_netloc: str) -> str | None:
    """Normalize sitemap loc without HTML crawl filters (e.g. .xml paths)."""
    parsed = urlparse(loc.strip())
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        return None
    normalized = urlunparse(
        (parsed.scheme, parsed.netloc.lower(), parsed.path or "/", "", "", "")
    )
    if not same_domain(normalized, seed_netloc):
        return None
    return normalized


def _local_tag(tag: str) -> str:
    if "}" in tag:
        return tag.rsplit("}", 1)[-1]
    return tag


def _find_locs(root: ET.Element) -> list[str]:
    locs: list[str] = []
    for elem in root.iter():
        if _local_tag(elem.tag) == "loc" and elem.text:
            locs.append(elem.text.strip())
    return locs


def _is_sitemap_index(root: ET.Element) -> bool:
    return _local_tag(root.tag) == "sitemapindex"


def _parse_sitemap_xml(body: str, seed_netloc: str) -> tuple[list[str], list[str], bool]:
    """Return (page_urls, child_sitemap_urls, is_index)."""
    try:
        root = ET.fromstring(body)
    except ET.ParseError as e:
        return [], [], False

    locs = _find_locs(root)
    if _is_sitemap_index(root):
        child_urls: list[str] = []
        for loc in locs:
            norm = _normalize_sitemap_loc(loc, seed_netloc)
            if norm:
                child_urls.append(norm)
        return [], child_urls, True

    page_urls: list[str] = []
    for loc in locs:
        norm = _normalize_sitemap_loc(loc, seed_netloc)
        if norm:
            page_urls.append(norm)
    return page_urls, [], False


async def _fetch_sitemap_body(
    client: httpx.AsyncClient,
    url: str,
) -> tuple[int, str]:
    try:
        resp = await client.get(url, follow_redirects=True)
        if resp.status_code != 200:
            return resp.status_code, ""
        return 200, resp.text
    except httpx.HTTPError:
        return 0, ""


async def _load_sitemap(
    client: httpx.AsyncClient,
    url: str,
    seed_netloc: str,
    info: SitemapInfo,
    files_fetched: int,
) -> int:
    if files_fetched >= MAX_SITEMAP_FILES:
        return files_fetched
    if url in info.sources:
        return files_fetched

    status, body = await _fetch_sitemap_body(client, url)
    info.sources.append(url)
    if status != 200 or not body.strip():
        info.errors.append(f"Sitemap {url}: HTTP {status or 'error'}")
        return files_fetched + 1

    page_urls, child_urls, is_index = _parse_sitemap_xml(body, seed_netloc)
    if is_index:
        files_fetched += 1
        for child in child_urls:
            if files_fetched >= MAX_SITEMAP_FILES:
                info.errors.append("Sitemap index: child limit reached")
                break
            if len(info.urls) >= MAX_SITEMAP_URLS:
                break
            files_fetched = await _load_sitemap(
                client, child, seed_netloc, info, files_fetched
            )
        return files_fetched

    for u in page_urls:
        if len(info.urls) >= MAX_SITEMAP_URLS:
            info.errors.append(f"Sitemap URL cap ({MAX_SITEMAP_URLS}) reached")
            break
        info.urls.add(u)
    return files_fetched + 1


async def fetch_sitemap(
    client: httpx.AsyncClient,
    seed_url: str,
    robots: RobotsInfo,
) -> SitemapInfo:
    seed_netloc = hostname_from_url(seed_url)
    info = SitemapInfo()
    candidates = list(robots.sitemap_directives)
    if not candidates:
        candidates.append(_default_sitemap_url(seed_url))

    files_fetched = 0
    for url in candidates:
        norm = _normalize_sitemap_loc(url, seed_netloc) or normalize_url(url) or url
        if files_fetched >= MAX_SITEMAP_FILES:
            break
        files_fetched = await _load_sitemap(
            client, norm, seed_netloc, info, files_fetched
        )

    if not info.urls and not info.errors:
        info.errors.append("No URLs found in sitemap sources")
    return info


async def fetch_site_resources(
    client: httpx.AsyncClient,
    seed_url: str,
    config: AuditConfig,
) -> tuple[RobotsInfo, SitemapInfo]:
    robots = await fetch_robots(client, seed_url, config)
    sitemap = await fetch_sitemap(client, seed_url, robots)
    return robots, sitemap
