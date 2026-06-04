"""URL normalization and domain helpers."""

from __future__ import annotations

from urllib.parse import urljoin, urlparse, urlunparse


def normalize_netloc(netloc: str) -> str:
    host = netloc.lower()
    if host.startswith("www."):
        host = host[4:]
    return host


# Non-content paths often injected by CDNs (e.g. Cloudflare email obfuscation)
_SKIP_PATH_PREFIXES = ("/cdn-cgi/",)


def is_crawlable_path(path: str) -> bool:
    return not any(path.startswith(prefix) for prefix in _SKIP_PATH_PREFIXES)


def normalize_url(url: str, base: str | None = None) -> str | None:
    """Normalize URL for dedup: resolve relative, strip fragment, lowercase host."""
    if not url or url.startswith("#"):
        return None
    if url.startswith(("mailto:", "tel:", "javascript:", "data:")):
        return None

    resolved = urljoin(base or url, url)
    parsed = urlparse(resolved)
    if parsed.scheme not in ("http", "https"):
        return None
    if not is_crawlable_path(parsed.path or "/"):
        return None

    netloc = parsed.netloc.lower()
    path = parsed.path or "/"
    normalized = urlunparse(
        (parsed.scheme, netloc, path, parsed.params, parsed.query, "")
    )
    return normalized


def same_domain(url: str, seed_netloc: str) -> bool:
    parsed = urlparse(url)
    if not parsed.netloc:
        return False
    return normalize_netloc(parsed.netloc) == normalize_netloc(seed_netloc)


def path_display(url: str) -> str:
    parsed = urlparse(url)
    path = parsed.path or "/"
    if parsed.query:
        path += "?" + parsed.query
    return path


def hostname_from_url(url: str) -> str:
    parsed = urlparse(url)
    host = parsed.netloc or parsed.path
    return normalize_netloc(host.split(":")[0])
