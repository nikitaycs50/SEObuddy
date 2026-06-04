"""Test helpers."""

from __future__ import annotations

from bs4 import BeautifulSoup

from seobuddy.models import PageData


def make_soup(html: str) -> BeautifulSoup:
    return BeautifulSoup(html, "lxml")


def page_with_html(html: str, url: str = "https://example.com/") -> PageData:
    return PageData(
        url=url,
        final_url=url,
        status_code=200,
        headers={"content-type": "text/html"},
        html=html,
        fetch_ms=5,
    )
