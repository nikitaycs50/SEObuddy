"""Scoring helpers and category metadata."""

from __future__ import annotations

from seobuddy.models import CheckResult, CheckStatus, PageAudit

# Display order and labels for reports/UI
CATEGORY_ORDER = [
    "title",
    "meta",
    "opengraph",
    "jsonld",
    "headings",
    "content",
    "links",
    "images",
    "canonical",
    "technical",
]

CATEGORY_LABELS = {
    "title": "Title",
    "meta": "Meta Desc",
    "opengraph": "Open Graph",
    "jsonld": "JSON-LD",
    "headings": "Headings",
    "content": "Content",
    "links": "Links",
    "images": "Images",
    "canonical": "Canonical",
    "technical": "Technical",
}

CATEGORY_WEIGHTS = {
    "title": 0.15,
    "meta": 0.10,
    "opengraph": 0.10,
    "jsonld": 0.10,
    "headings": 0.10,
    "content": 0.15,
    "links": 0.10,
    "images": 0.10,
    "canonical": 0.05,
    "technical": 0.05,
}


def clamp_score(value: float) -> int:
    return max(0, min(100, round(value)))


def status_from_score(score: int) -> CheckStatus:
    if score >= 80:
        return CheckStatus.PASS
    if score >= 60:
        return CheckStatus.WARN
    return CheckStatus.FAIL


def weighted_page_score(results: dict[str, CheckResult]) -> int:
    total = 0.0
    for key, weight in CATEGORY_WEIGHTS.items():
        result = results.get(key)
        if result:
            total += result.score * weight
    return clamp_score(total)


def letter_grade(score: int) -> str:
    if score >= 90:
        return "A"
    if score >= 80:
        return "B"
    if score >= 70:
        return "C+"
    if score >= 60:
        return "C"
    if score >= 50:
        return "D"
    return "F"


def aggregate_category_scores(
    pages: list[PageAudit],
) -> dict[str, dict[str, int]]:
    """Per-category mean score and pages_ok count (score >= 80)."""
    agg: dict[str, dict[str, int]] = {}
    for cat in CATEGORY_ORDER:
        scores = []
        ok = 0
        for page in pages:
            r = page.results.get(cat)
            if r:
                scores.append(r.score)
                if r.score >= 80:
                    ok += 1
        agg[cat] = {
            "score": round(sum(scores) / len(scores)) if scores else 0,
            "pages_ok": ok,
            "pages_total": len(pages),
        }
    return agg


def top_issues(pages: list[PageAudit], limit: int = 5) -> list[str]:
    """Human-readable top issues sorted by impact."""
    if not pages:
        return []

    agg = aggregate_category_scores(pages)
    impacts: list[tuple[float, str]] = []

    for cat in CATEGORY_ORDER:
        data = agg[cat]
        cat_score = data["score"]
        weight = CATEGORY_WEIGHTS[cat]
        impact = weight * (100 - cat_score)
        label = CATEGORY_LABELS[cat]
        ok = data["pages_ok"]
        total = data["pages_total"]
        if cat_score < 80:
            line = f"{label} weak (avg {cat_score}/100, {ok}/{total} pages OK)"
            impacts.append((impact, line))

    impacts.sort(key=lambda x: x[0], reverse=True)
    lines = []
    for i, (_, line) in enumerate(impacts[:limit], 1):
        circled = "①②③④⑤"[i - 1] if i <= 5 else str(i)
        lines.append(f"{circled} {line}")
    return lines


def collect_recommendations(pages: list[PageAudit]) -> list[str]:
    """Deduplicated suggestions sorted by category impact."""
    agg = aggregate_category_scores(pages)
    seen: set[str] = set()
    items: list[tuple[float, str]] = []

    for cat in CATEGORY_ORDER:
        data = agg[cat]
        impact = CATEGORY_WEIGHTS[cat] * (100 - data["score"])
        for page in pages:
            r = page.results.get(cat)
            if r:
                for s in r.suggestions:
                    if s not in seen:
                        seen.add(s)
                        items.append((impact, s))

    items.sort(key=lambda x: x[0], reverse=True)
    return [s for _, s in items]
