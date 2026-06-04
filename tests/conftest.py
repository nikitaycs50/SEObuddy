"""Shared pytest fixtures."""

from __future__ import annotations

import pytest

from seobuddy.models import PageData, SiteContext


@pytest.fixture
def context() -> SiteContext:
    return SiteContext()


@pytest.fixture
def sample_page() -> PageData:
    return PageData(
        url="https://example.com/",
        final_url="https://example.com/",
        status_code=200,
        headers={"content-type": "text/html; charset=utf-8"},
        html="",
        fetch_ms=10,
    )
