"""Typer CLI entrypoint."""

from __future__ import annotations

import asyncio
import sys
import time
from pathlib import Path
from urllib.parse import urlparse

import httpx
import typer
from rich.console import Console

from seobuddy import CLI_EPILOG, __version__
from seobuddy.auditor import audit_page
from seobuddy.checks.hreflang import validate_hreflang_reciprocity
from seobuddy.checks.robots_check import audit_robots
from seobuddy.checks.sitemap_check import audit_sitemap
from seobuddy.crawler import AsyncCrawler
from seobuddy.site_resources import fetch_site_resources
from seobuddy.display import (
    crawl_progress,
    make_console,
    show_about,
    show_banner,
    show_branding,
    show_error,
    show_page_result,
    show_summary,
    update_crawl_progress,
)
from seobuddy.models import DEFAULT_USER_AGENT, AuditConfig, SiteAudit, SiteContext
from seobuddy.report import write_report
from seobuddy.url_utils import hostname_from_url, normalize_url

app = typer.Typer(
    name="seobuddy",
    help=f"Crawl a website and produce a technical SEO audit (v{__version__}).",
    add_completion=False,
)


def _validate_url(url: str) -> str:
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        if not parsed.scheme and parsed.path:
            url = "https://" + url
            parsed = urlparse(url)
        else:
            raise typer.BadParameter("URL must use http or https scheme")
    if not parsed.netloc:
        raise typer.BadParameter("URL must include a hostname")
    normalized = normalize_url(url)
    if not normalized:
        raise typer.BadParameter("Invalid URL")
    return normalized


def _about_callback(value: bool) -> None:
    if value:
        no_color = "--no-color" in sys.argv
        show_about(make_console(AuditConfig(no_color=no_color)))
        raise typer.Exit()


async def _run_audit(
    url: str,
    config: AuditConfig,
) -> SiteAudit:
    hostname = hostname_from_url(url)
    site = SiteAudit(seed_url=url, hostname=hostname)
    context = SiteContext()
    console = make_console(config)
    show_banner(console, config, url)

    start = time.perf_counter()
    completed = 0

    timeout = httpx.Timeout(config.timeout)
    headers = {"User-Agent": config.user_agent}

    async with httpx.AsyncClient(
        follow_redirects=True,
        max_redirects=config.max_redirects,
        timeout=timeout,
        headers=headers,
    ) as link_client:
        robots, sitemap = await fetch_site_resources(link_client, url, config)
        context.robots = robots
        context.sitemap = sitemap

        site.site_results["robots"] = audit_robots(robots, url)
        site.site_results["sitemap"] = await audit_sitemap(
            sitemap,
            set(),
            link_client,
        )

        crawler = AsyncCrawler(config, robots=robots)
        context.fetched_urls = crawler.fetched_urls

        with crawl_progress(console, total=config.max_pages) as (progress, task_id):
            async for page in crawler.crawl(url):
                context.fetched_urls = crawler.fetched_urls

                if page.status_code == 0:
                    raise httpx.ConnectError(
                        f"Could not fetch {page.url}"
                    )

                page_audit = await audit_page(page, context, config, link_client)
                site.pages.append(page_audit)
                completed += 1

                update_crawl_progress(
                    progress,
                    task_id,
                    page.final_url,
                    completed,
                    None,
                )
                show_page_result(console, page_audit)

        site.elapsed_s = time.perf_counter() - start
        site.crawl_capped = crawler.crawl_capped
        site.skipped_robots = crawler.skipped_robots

        if not site.pages:
            if robots.available and not robots.can_fetch(url):
                raise RuntimeError(
                    "No pages were fetched: seed URL is disallowed in robots.txt "
                    f"for User-Agent {config.user_agent!r}"
                )
            raise RuntimeError("No pages were fetched")

        crawled: set[str] = set()
        for p in site.pages:
            crawled.add(p.page.final_url)
            norm = normalize_url(p.page.final_url) or normalize_url(p.page.url)
            if norm:
                crawled.add(norm)
        site.site_results["sitemap"] = await audit_sitemap(
            sitemap,
            crawled,
            link_client,
        )
        validate_hreflang_reciprocity(context, site.pages)

    site.report_path = write_report(site, config.output_dir)
    show_summary(console, site)
    return site


@app.command(epilog=CLI_EPILOG)
def main(
    url: str = typer.Argument(..., help="Seed URL to audit"),
    depth: int = typer.Option(2, "--depth", help="Crawl depth (0 = seed only)"),
    max_pages: int = typer.Option(
        50, "--max-pages", help="Maximum pages to crawl (stops when reached)"
    ),
    concurrency: int = typer.Option(5, "--concurrency", help="Parallel requests"),
    timeout: int = typer.Option(10, "--timeout", help="Request timeout (seconds)"),
    output_dir: Path = typer.Option(Path("."), "--output-dir", help="Report output directory"),
    user_agent: str = typer.Option(
        DEFAULT_USER_AGENT,
        "--user-agent",
        help="HTTP User-Agent (default: Chrome desktop for site compatibility)",
    ),
    no_color: bool = typer.Option(False, "--no-color", help="Disable Rich colors"),
    about: bool = typer.Option(
        False,
        "--about",
        help="Show how SEObuddy works, copyright, and project links",
        callback=_about_callback,
        is_eager=True,
    ),
) -> None:
    """Crawl URL and run technical SEO audit."""
    console = make_console(AuditConfig(no_color=no_color))

    try:
        validated = _validate_url(url)
    except typer.BadParameter as e:
        show_error(console, str(e))
        raise typer.Exit(1) from e

    config = AuditConfig(
        depth=depth,
        max_pages=max_pages,
        concurrency=concurrency,
        timeout=timeout,
        output_dir=output_dir,
        user_agent=user_agent,
        no_color=no_color,
    )

    try:
        asyncio.run(_run_audit(validated, config))
    except httpx.ConnectError as e:
        show_error(console, f"Could not connect to host: {e}")
        raise typer.Exit(1) from e
    except httpx.TimeoutException as e:
        show_error(console, f"Request timed out: {e}")
        raise typer.Exit(1) from e
    except ValueError as e:
        show_error(console, str(e))
        raise typer.Exit(1) from e
    except RuntimeError as e:
        show_error(console, str(e))
        raise typer.Exit(1) from e


def run() -> None:
    """Console script entrypoint (branding footer on CLI usage errors)."""
    try:
        app()
    except SystemExit as exc:
        if exc.code == 2:
            show_branding(Console(stderr=True), leading_newline=True)
        raise


if __name__ == "__main__":
    run()
