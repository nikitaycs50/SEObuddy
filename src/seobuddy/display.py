"""Rich terminal UI for SEObuddy."""

from __future__ import annotations

from contextlib import contextmanager
from typing import TYPE_CHECKING

from rich.console import Console
from rich.panel import Panel
from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TaskProgressColumn,
    TextColumn,
    TimeElapsedColumn,
)
from rich.table import Table
from rich.text import Text

from seobuddy import __version__
from seobuddy.checks.base import (
    CATEGORY_LABELS,
    CATEGORY_ORDER,
    aggregate_category_scores,
    letter_grade,
    top_issues,
)
from seobuddy.models import AuditConfig, PageAudit, SiteAudit, format_user_agent_display
from seobuddy.url_utils import path_display as format_path

if TYPE_CHECKING:
    from collections.abc import Iterator


def make_console(config: AuditConfig) -> Console:
    return Console(no_color=config.no_color, force_terminal=not config.no_color)


def score_style(score: int) -> str:
    if score >= 80:
        return "green"
    if score >= 60:
        return "yellow"
    if score >= 40:
        return "orange3"
    return "red"


def score_bar(score: int, width: int = 12) -> str:
    filled = int(score / 100 * width)
    return "█" * filled + "░" * (width - filled)


def show_banner(console: Console, config: AuditConfig, url: str) -> None:
    ua = format_user_agent_display(config.user_agent)
    body = (
        f"[bold]🔍 SEObuddy[/bold]  v{__version__}\n"
        f"Auditing: [cyan]{url}[/cyan]\n"
        f"Depth: {config.depth}  |  Concurrency: {config.concurrency}  |  "
        f"Max pages: {config.max_pages}\n"
        f"User-Agent: [dim]{ua}[/dim]"
    )
    console.print(Panel(body, title="SEObuddy", border_style="blue"))


def show_error(console: Console, message: str) -> None:
    console.print(f"[bold red]Error:[/bold red] {message}")


@contextmanager
def crawl_progress(console: Console, total: int | None = None) -> Iterator[tuple[Progress, int]]:
    progress = Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        TimeElapsedColumn(),
        console=console,
        transient=False,
    )
    with progress:
        task_id = progress.add_task("Crawling…", total=total)
        yield progress, task_id


def update_crawl_progress(
    progress: Progress,
    task_id: int,
    url: str,
    completed: int,
    total: int | None,
) -> None:
    desc = format_path(url, max_len=52)
    progress.update(
        task_id,
        description=desc,
        completed=completed,
        total=total if total is not None else completed,
    )


def _category_icons(page: PageAudit) -> str:
    short = {
        "title": "title",
        "meta": "meta",
        "opengraph": "og",
        "headings": "h1",
    }
    parts = []
    for key, label in short.items():
        r = page.results.get(key)
        icon = "✓" if r and r.status.value == "pass" else "✗"
        if r and r.score >= 60 and r.status.value != "pass":
            icon = "~"
        parts.append(f"{label} {icon}")
    return "  ".join(parts)


def show_page_result(console: Console, page: PageAudit) -> None:
    style = score_style(page.score)
    bar = score_bar(page.score, 8)
    icons = _category_icons(page)
    path = page.path_display
    line = Text()
    line.append(f"{bar} {page.score}/100", style=style)
    line.append(f"  {path}  — {icons}", style="dim")
    console.print(line)


def show_summary(console: Console, site: SiteAudit) -> None:
    score = site.site_score
    grade = letter_grade(score)
    style = score_style(score)
    bar = score_bar(score, 20)

    header = (
        f"[bold]SITE AUDIT COMPLETE[/bold]  ·  {site.hostname}\n"
        f"{len(site.pages)} pages  ·  {site.elapsed_s:.1f}s"
    )
    if site.crawl_capped:
        header += "  ·  [yellow]Crawl limit reached[/yellow]"
    if site.report_path:
        header += f"\nReport: {site.report_path.name}"

    agg = aggregate_category_scores(site.pages)
    table = Table(show_header=True, header_style="bold")
    table.add_column("Category", style="cyan")
    table.add_column("Score")
    table.add_column("Pages OK", justify="right")

    for cat in CATEGORY_ORDER:
        data = agg[cat]
        cat_style = score_style(data["score"])
        cat_bar = score_bar(data["score"], 10)
        table.add_row(
            CATEGORY_LABELS[cat],
            f"[{cat_style}]{cat_bar}  {data['score']}/100[/{cat_style}]",
            f"{data['pages_ok']}/{data['pages_total']}",
        )

    console.print()
    console.print(Panel(header, border_style="green"))
    console.print(
        Panel(
            f"[bold]OVERALL SCORE[/bold]\n\n"
            f"       [{style}]{bar}[/{style}]  [{style}]{score}/100[/{style}]  {grade}",
            border_style=style,
        )
    )
    console.print(table)

    issues = top_issues(site.pages, limit=5)
    if issues:
        console.print("\n[bold]TOP ISSUES (by impact)[/bold]")
        for line in issues:
            console.print(f"  {line}")
