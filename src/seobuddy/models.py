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


@dataclass
class AuditConfig:
    depth: int = 2
    concurrency: int = 5
    timeout: int = 10
    output_dir: Path = field(default_factory=lambda: Path("."))
    user_agent: str = "SEObuddy/0.1.0"
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


@dataclass
class SiteAudit:
    seed_url: str
    hostname: str
    pages: list[PageAudit] = field(default_factory=list)
    started_at: datetime = field(default_factory=datetime.now)
    elapsed_s: float = 0.0
    report_path: Path | None = None

    @property
    def site_score(self) -> int:
        if not self.pages:
            return 0
        return round(sum(p.score for p in self.pages) / len(self.pages))
