"""Safe HTML parsing for audit and link extraction."""

from __future__ import annotations

import warnings

from bs4 import BeautifulSoup, XMLParsedAsHTMLWarning

_HTML_START_MARKERS = ("<!doctype", "<html", "<!DOCTYPE", "<HTML")


def is_html_content(content_type: str, body: str) -> bool:
    """True when the response should be parsed as HTML."""
    ct = (content_type or "").lower().split(";")[0].strip()
    if ct in (
        "application/xml",
        "text/xml",
        "application/json",
        "image/svg+xml",
    ):
        return False
    if any(x in ct for x in ("application/xml", "+xml", "text/xml")):
        return False

    sample = (body or "").lstrip()[:200].lower()
    if sample.startswith("<?xml"):
        return False

    if ct in ("text/html", "application/xhtml+xml"):
        return True
    if not ct and sample.startswith("<"):
        return any(sample.startswith(m.lower()) for m in _HTML_START_MARKERS) or (
            "<html" in sample[:500]
        )
    return False


def parse_html(html: str, content_type: str = "") -> BeautifulSoup | None:
    """Parse HTML without XML-as-HTML warnings; returns None for non-HTML bodies."""
    if not html or not html.strip():
        return None
    if not is_html_content(content_type, html):
        return None

    with warnings.catch_warnings():
        warnings.simplefilter("ignore", XMLParsedAsHTMLWarning)
        return BeautifulSoup(html, "lxml")
