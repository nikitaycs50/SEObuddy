from seobuddy.url_utils import (
    crawl_dedup_key,
    is_crawlable_url,
    normalize_url,
    path_display,
)


def test_crawl_dedup_ignores_query():
    a = "https://google.com/ml?hl=de&continue=x"
    b = "https://google.com/ml?hl=en&continue=y"
    assert crawl_dedup_key(a) == crawl_dedup_key(b)


def test_skip_ml_path():
    assert normalize_url("https://google.com/ml?continue=https://x") is None


def test_skip_long_query():
    q = "x" * 150
    assert normalize_url(f"https://example.com/page?{q}") is None


def test_skip_policy_paths():
    assert normalize_url("https://google.com/intl/de/policies/privacy/") is None


def test_path_display_truncates():
    long_path = "/ml?" + "a" * 200
    display = path_display(f"https://google.com{long_path}", max_len=40)
    assert len(display) <= 40
    assert "…" in display
