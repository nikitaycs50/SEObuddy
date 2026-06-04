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

from seobuddy import AUTHOR_URL, CREATED_BY, COPYRIGHT, GITHUB_URL, __version__
from seobuddy.checks.base import (
    CATEGORY_LABELS,
    CATEGORY_ORDER,
    CATEGORY_WEIGHTS,
    SITE_CATEGORY_LABELS,
    SITE_CHECK_ORDER,
    aggregate_category_scores,
    letter_grade,
    site_check_pages_ok,
    top_issues,
)
from seobuddy.models import AuditConfig, PageAudit, SiteAudit, format_user_agent_display
from seobuddy.url_utils import path_display as format_path

if TYPE_CHECKING:
    from collections.abc import Iterator


def branding_rich() -> str:
    return f"[dim]{CREATED_BY}[/dim]  [link={AUTHOR_URL}]{AUTHOR_URL}[/link]"


def show_branding(console: Console, *, leading_newline: bool = False) -> None:
    if leading_newline:
        console.print()
    console.print(branding_rich())


def show_about(console: Console) -> None:
    """Print project overview, workflow, and copyright."""
    intro = (
        f"[bold]🔍 SEObuddy[/bold]  v{__version__}\n\n"
        "A Python CLI that crawls a website and runs a [bold]technical SEO audit[/bold]. "
        "You get live progress and scores in the terminal, plus a Markdown report "
        "you can open in any editor or share with your team."
    )
    console.print(Panel(intro, title="About SEObuddy", border_style="blue"))

    workflow = (
        "[bold]How it works[/bold]\n\n"
        "1. Validates and normalizes your seed URL\n"
        "2. [cyan]BFS-crawls[/cyan] same-domain HTML pages with async HTTP (httpx)\n"
        "3. Fetches [cyan]robots.txt[/cyan] and [cyan]sitemap.xml[/cyan]; audits each page with "
        "[cyan]11 weighted SEO checks[/cyan] (BeautifulSoup + lxml)\n"
        "4. Renders a Rich terminal UI — progress, per-page scores, final summary\n"
        "5. Writes [cyan]yyyymmddhhmm-<hostname>-report.md[/cyan] to [cyan]--output-dir[/cyan]\n\n"
        "[bold]Defaults[/bold]\n"
        "Depth [cyan]2[/cyan]  ·  Max pages [cyan]50[/cyan]  ·  "
        "Concurrency [cyan]5[/cyan]  ·  Timeout [cyan]10s[/cyan]\n\n"
        "[bold]Crawl behavior[/bold]\n"
        "Same domain only, path deduplication, configurable depth and page cap. "
        "Static HTML only (no JavaScript rendering). Crawl respects robots.txt Disallow rules."
    )
    console.print(Panel(workflow, border_style="dim"))

    category_lines = [
        f"• {CATEGORY_LABELS[cat]} ({int(CATEGORY_WEIGHTS[cat] * 100)}%)"
        for cat in CATEGORY_ORDER
    ]
    category_lines.extend(
        f"• {SITE_CATEGORY_LABELS[key]} (site-wide)"
        for key in SITE_CHECK_ORDER
    )
    categories = "[bold]Audit categories[/bold]\n\n" + "\n".join(category_lines)
    console.print(Panel(categories, border_style="dim"))

    links = (
        f"[bold]Links[/bold]\n\n"
        f"GitHub: [link={GITHUB_URL}]{GITHUB_URL}[/link]\n"
        f"Website: [link={AUTHOR_URL}]{AUTHOR_URL}[/link]\n\n"
        f"[dim]{COPYRIGHT}[/dim]\n"
        f"[dim]{CREATED_BY}[/dim]"
    )
    console.print(Panel(links, title="Project", border_style="green"))


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
        f"User-Agent: [dim]{ua}[/dim]\n"
        f"{branding_rich()}"
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
    if site.skipped_robots:
        header += f"  ·  [dim]{site.skipped_robots} skipped (robots.txt)[/dim]"
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

    for key in SITE_CHECK_ORDER:
        r = site.site_results.get(key)
        if not r:
            continue
        cat_style = score_style(r.score)
        cat_bar = score_bar(r.score, 10)
        label = SITE_CATEGORY_LABELS.get(key, key)
        table.add_row(
            label,
            f"[{cat_style}]{cat_bar}  {r.score}/100[/{cat_style}]",
            site_check_pages_ok(r.score),
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

    show_branding(console, leading_newline=True)
