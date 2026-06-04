"""Shared dataclasses for SEObuddy."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path


class CheckStatus(str, Enum):
    PASS = "pass"
    WARN = "warn"
    FAIL = "fail"


# Chrome desktop UA — many sites block non-browser clients.
DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
)


def format_user_agent_display(user_agent: str, max_len: int = 56) -> str:
    """Shorten long User-Agent strings for terminal output."""
    if len(user_agent) <= max_len:
        return user_agent
    return user_agent[: max_len - 1] + "…"


@dataclass
class AuditConfig:
    depth: int = 2
    concurrency: int = 5
    timeout: int = 10
    max_pages: int = 50
    output_dir: Path = field(default_factory=lambda: Path("."))
    user_agent: str = DEFAULT_USER_AGENT
    no_color: bool = False
    max_redirects: int = 5


@dataclass
class PageData:
    url: str
    final_url: str
    status_code: int
    headers: dict[str, str]
    html: str
    fetch_ms: int
    redirect_chain: list[str] = field(default_factory=list)


@dataclass
class CheckResult:
    name: str
    score: int
    weight: float
    status: CheckStatus
    findings: list[str] = field(default_factory=list)
    suggestions: list[str] = field(default_factory=list)


@dataclass
class PageAudit:
    page: PageData
    results: dict[str, CheckResult]
    score: int
    path_display: str


@dataclass
class SiteContext:
    titles_seen: set[str] = field(default_factory=set)
    metas_seen: set[str] = field(default_factory=set)
    canonicals_seen: set[str] = field(default_factory=set)
    fetched_urls: set[str] = field(default_factory=set)
    hreflang_edges: list[tuple[str, str, str]] = field(default_factory=list)
    robots: object | None = None  # RobotsInfo from site_resources
    sitemap: object | None = None  # SitemapInfo from site_resources


@dataclass
class SiteAudit:
    seed_url: str
    hostname: str
    pages: list[PageAudit] = field(default_factory=list)
    site_results: dict[str, CheckResult] = field(default_factory=dict)
    started_at: datetime = field(default_factory=datetime.now)
    elapsed_s: float = 0.0
    report_path: Path | None = None
    crawl_capped: bool = False
    skipped_robots: int = 0

    @property
    def site_score(self) -> int:
        if not self.pages:
            return 0
        return round(sum(p.score for p in self.pages) / len(self.pages))
