"""Markdown report generator."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from seobuddy.checks.base import (
    CATEGORY_LABELS,
    CATEGORY_ORDER,
    aggregate_category_scores,
    collect_recommendations,
    letter_grade,
    top_issues,
)
from seobuddy import AUTHOR_NAME, AUTHOR_URL, CREATED_BY
from seobuddy.models import SiteAudit


def _sanitize_hostname(hostname: str) -> str:
    return "".join(c if c.isalnum() or c in ".-" else "-" for c in hostname)


def report_filename(hostname: str, when: datetime | None = None) -> str:
    dt = when or datetime.now()
    stamp = dt.strftime("%Y%m%d%H%M")
    host = _sanitize_hostname(hostname)
    return f"{stamp}-{host}-report.md"


def write_report(site: SiteAudit, output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / report_filename(site.hostname, site.started_at)
    path.write_text(_build_markdown(site), encoding="utf-8")
    return path


def _build_markdown(site: SiteAudit) -> str:
    lines: list[str] = []
    score = site.site_score
    grade = letter_grade(score)
    issues = top_issues(site.pages, limit=5)
    agg = aggregate_category_scores(site.pages)

    lines.append("# SEObuddy SEO Audit Report")
    lines.append("")
    lines.append("## 1. Executive Summary")
    lines.append("")
    lines.append(f"- **Overall score:** {score}/100 ({grade})")
    lines.append(f"- **Date:** {site.started_at.strftime('%Y-%m-%d %H:%M')}")
    lines.append(f"- **Seed URL:** {site.seed_url}")
    lines.append(f"- **Pages crawled:** {len(site.pages)}")
    if site.crawl_capped:
        lines.append("- **Crawl note:** Stopped at max-pages limit (more URLs were skipped)")
    lines.append(f"- **Duration:** {site.elapsed_s:.1f}s")
    lines.append("")
    lines.append("### Top issues")
    lines.append("")
    if issues:
        for issue in issues:
            lines.append(f"- {issue}")
    else:
        lines.append("- No major issues detected")
    lines.append("")

    lines.append("## 2. Score Breakdown")
    lines.append("")
    lines.append("| Category | Score | Pages OK |")
    lines.append("|----------|------:|---------:|")
    for cat in CATEGORY_ORDER:
        data = agg[cat]
        lines.append(
            f"| {CATEGORY_LABELS[cat]} | {data['score']}/100 | "
            f"{data['pages_ok']}/{data['pages_total']} |"
        )
    lines.append("")

    lines.append("## 3. Page-by-Page Analysis")
    lines.append("")
    for page in site.pages:
        summary = f"{page.path_display} — {page.score}/100"
        lines.append(f"<details>")
        lines.append(f"<summary>{summary}</summary>")
        lines.append("")
        lines.append(f"- **URL:** {page.page.final_url}")
        lines.append(f"- **Status:** {page.page.status_code}")
        lines.append("")
        for cat in CATEGORY_ORDER:
            r = page.results.get(cat)
            if not r:
                continue
            lines.append(f"### {CATEGORY_LABELS[cat]} ({r.score}/100)")
            if r.findings:
                for f in r.findings:
                    lines.append(f"- {f}")
            if r.suggestions:
                lines.append("")
                lines.append("Suggestions:")
                for s in r.suggestions:
                    lines.append(f"- {s}")
            lines.append("")
        lines.append("</details>")
        lines.append("")

    lines.append("## 4. Recommendations")
    lines.append("")
    recs = collect_recommendations(site.pages)
    if recs:
        for r in recs:
            lines.append(f"- {r}")
    else:
        lines.append("- Continue monitoring; no critical recommendations.")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append(f"*{CREATED_BY} — [{AUTHOR_NAME}]({AUTHOR_URL})*")

    return "\n".join(lines)
