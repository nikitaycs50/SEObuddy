"""Typer CLI entrypoint."""

from __future__ import annotations

import asyncio
import time
from pathlib import Path
from urllib.parse import urlparse

import httpx
import typer

from seobuddy import __version__
from seobuddy.auditor import audit_page
from seobuddy.crawler import AsyncCrawler
from seobuddy.display import (
    crawl_progress,
    make_console,
    show_banner,
    show_error,
    show_page_result,
    show_summary,
    update_crawl_progress,
)
from seobuddy.models import AuditConfig, SiteAudit, SiteContext
from seobuddy.report import write_report
from seobuddy.url_utils import hostname_from_url, normalize_url

app = typer.Typer(
    name="seobuddy",
    help="Crawl a website and produce a technical SEO audit.",
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


async def _run_audit(
    url: str,
    config: AuditConfig,
) -> SiteAudit:
    hostname = hostname_from_url(url)
    site = SiteAudit(seed_url=url, hostname=hostname)
    context = SiteContext()
    crawler = AsyncCrawler(config)
    context.fetched_urls = crawler.fetched_urls

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
        with crawl_progress(console) as (progress, task_id):
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

    if not site.pages:
        raise RuntimeError("No pages were fetched")

    site.report_path = write_report(site, config.output_dir)
    show_summary(console, site)
    return site


@app.command()
def main(
    url: str = typer.Argument(..., help="Seed URL to audit"),
    depth: int = typer.Option(2, "--depth", help="Crawl depth (0 = seed only)"),
    concurrency: int = typer.Option(5, "--concurrency", help="Parallel requests"),
    timeout: int = typer.Option(10, "--timeout", help="Request timeout (seconds)"),
    output_dir: Path = typer.Option(Path("."), "--output-dir", help="Report output directory"),
    user_agent: str = typer.Option(
        f"SEObuddy/{__version__}",
        "--user-agent",
        help="Custom User-Agent",
    ),
    no_color: bool = typer.Option(False, "--no-color", help="Disable Rich colors"),
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


if __name__ == "__main__":
    app()
