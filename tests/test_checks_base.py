from seobuddy.checks.base import letter_grade, weighted_page_score
from seobuddy.models import CheckResult, CheckStatus


def test_letter_grade():
    assert letter_grade(73) == "C+"
    assert letter_grade(90) == "A"


def test_weighted_page_score():
    results = {
        "title": CheckResult("title", 100, 0.15, CheckStatus.PASS),
        "meta": CheckResult("meta", 100, 0.10, CheckStatus.PASS),
        "opengraph": CheckResult("opengraph", 100, 0.10, CheckStatus.PASS),
        "jsonld": CheckResult("jsonld", 100, 0.10, CheckStatus.PASS),
        "headings": CheckResult("headings", 100, 0.10, CheckStatus.PASS),
        "content": CheckResult("content", 100, 0.15, CheckStatus.PASS),
        "links": CheckResult("links", 100, 0.10, CheckStatus.PASS),
        "images": CheckResult("images", 100, 0.10, CheckStatus.PASS),
        "canonical": CheckResult("canonical", 100, 0.05, CheckStatus.PASS),
        "technical": CheckResult("technical", 100, 0.05, CheckStatus.PASS),
    }
    assert weighted_page_score(results) == 100
