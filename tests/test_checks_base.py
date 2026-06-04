from seobuddy.checks.base import (
    CATEGORY_ORDER,
    CATEGORY_WEIGHTS,
    letter_grade,
    site_check_pages_ok,
    weighted_page_score,
)
from seobuddy.models import CheckResult, CheckStatus


def test_letter_grade():
    assert letter_grade(73) == "C+"
    assert letter_grade(90) == "A"


def test_site_check_pages_ok():
    assert site_check_pages_ok(100) == "1/1"
    assert site_check_pages_ok(79) == "0/1"


def test_category_weights_sum_to_one():
    assert len(CATEGORY_ORDER) == 11
    assert abs(sum(CATEGORY_WEIGHTS.values()) - 1.0) < 1e-9


def test_weighted_page_score():
    results = {
        cat: CheckResult(cat, 100, CATEGORY_WEIGHTS[cat], CheckStatus.PASS)
        for cat in CATEGORY_ORDER
    }
    assert weighted_page_score(results) == 100
