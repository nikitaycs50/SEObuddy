"""URL normalization, crawl filtering, and domain helpers."""

from __future__ import annotations

from urllib.parse import urljoin, urlparse, urlunparse

# CDN / infra paths
_SKIP_PATH_PREFIXES = (
    "/cdn-cgi/",
    "/intl/",
)

# Paths that are rarely useful for content SEO audits
_SKIP_PATH_CONTAINS = (
    "/preferences",
    "/policies/",
    "/privacy",
    "/terms",
    "/advanced_search",
    "/websearch/",
    "/accounts/",
    "/signin",
    "/login",
    "/logout",
)

# Exact paths or prefixes (locale hubs, redirectors)
_SKIP_PATHS = (
    "/ml",
    "/url",
)

_NON_HTML_EXTENSIONS = (
    ".pdf",
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".svg",
    ".webp",
    ".ico",
    ".zip",
    ".gz",
    ".css",
    ".js",
    ".mjs",
    ".xml",
    ".json",
    ".woff",
    ".woff2",
    ".ttf",
    ".mp4",
    ".webm",
)

MAX_CRAWL_QUERY_LEN = 120
MAX_CRAWL_PATH_LEN = 200
DEFAULT_PATH_DISPLAY_LEN = 56


def normalize_netloc(netloc: str) -> str:
    host = netloc.lower()
    if host.startswith("www."):
        host = host[4:]
    return host


def is_crawlable_path(path: str) -> bool:
    if not path:
        return True
    if len(path) > MAX_CRAWL_PATH_LEN:
        return False
    lower = path.lower()
    if any(lower.startswith(p) for p in _SKIP_PATH_PREFIXES):
        return False
    if any(part in lower for part in _SKIP_PATH_CONTAINS):
        return False
    base = lower.rstrip("/") or "/"
    for skip in _SKIP_PATHS:
        if base == skip or base.startswith(skip + "/"):
            return False
    if any(lower.endswith(ext) for ext in _NON_HTML_EXTENSIONS):
        return False
    return True


def is_crawlable_url(url: str) -> bool:
    """Whether a normalized URL should be fetched or enqueued."""
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        return False
    path = parsed.path or "/"
    if not is_crawlable_path(path):
        return False
    if parsed.query and len(parsed.query) > MAX_CRAWL_QUERY_LEN:
        return False
    return True


def crawl_dedup_key(url: str) -> str:
    """Identity for visited set: host + path, no query or fragment."""
    parsed = urlparse(url)
    path = parsed.path or "/"
    return urlunparse((parsed.scheme, parsed.netloc.lower(), path, "", "", ""))


def normalize_url(url: str, base: str | None = None) -> str | None:
    """Normalize URL for fetch: resolve relative, strip fragment, lowercase host."""
    if not url or url.startswith("#"):
        return None
    if url.startswith(("mailto:", "tel:", "javascript:", "data:")):
        return None

    resolved = urljoin(base or url, url)
    parsed = urlparse(resolved)
    if parsed.scheme not in ("http", "https"):
        return None

    netloc = parsed.netloc.lower()
    path = parsed.path or "/"
    normalized = urlunparse(
        (parsed.scheme, netloc, path, parsed.params, parsed.query, "")
    )
    if not is_crawlable_url(normalized):
        return None
    return normalized


def same_domain(url: str, seed_netloc: str) -> bool:
    parsed = urlparse(url)
    if not parsed.netloc:
        return False
    return normalize_netloc(parsed.netloc) == normalize_netloc(seed_netloc)


def path_display(url: str, max_len: int = DEFAULT_PATH_DISPLAY_LEN) -> str:
    parsed = urlparse(url)
    path = parsed.path or "/"
    if parsed.query:
        q = parsed.query
        if len(q) > 40:
            q = q[:37] + "..."
        path += "?" + q
    if len(path) <= max_len:
        return path
    keep = max_len - 1
    head = keep // 2
    tail = keep - head
    return path[:head] + "…" + path[-tail:]


def hostname_from_url(url: str) -> str:
    parsed = urlparse(url)
    host = parsed.netloc or parsed.path
    return normalize_netloc(host.split(":")[0])
