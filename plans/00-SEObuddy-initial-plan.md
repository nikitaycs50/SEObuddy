# SEObuddy — Implementation Plan

## Context

Build a new Python CLI tool called **SEObuddy** that crawls a website up to N levels deep (default 2) and produces a technical SEO audit. Output: a beautiful terminal UI (Rich pseudo-graphics, progress bars, scores) plus a timestamped Markdown report file.

Stack: Python 3.11+, `httpx` for async HTTP, `BeautifulSoup4` + `lxml` for parsing, `rich` for terminal UI, `typer` for CLI, `pyproject.toml` installable package.

---

## Project Structure

```
seobuddy/
├── pyproject.toml
├── src/
│   └── seobuddy/
│       ├── __init__.py
│       ├── __main__.py        # python -m seobuddy entry
│       ├── cli.py             # typer app, main entrypoint
│       ├── crawler.py         # async BFS crawler, depth control, dedup
│       ├── auditor.py         # orchestrates all checks for one page
│       ├── report.py          # Markdown report generator
│       ├── display.py         # all Rich terminal UI (panels, tables, bars)
│       └── checks/
│           ├── base.py        # CheckResult dataclass, score helpers
│           ├── title.py
│           ├── meta.py
│           ├── opengraph.py
│           ├── jsonld.py
│           ├── headings.py
│           ├── content.py
│           ├── links.py
│           ├── images.py
│           ├── canonical.py
│           └── technical.py   # robots meta, viewport, HTTPS, URL structure
```

---

## Dependencies (pyproject.toml)

```toml
[project]
name = "seobuddy"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
    "typer[all]>=0.12",
    "httpx[http2]>=0.27",
    "beautifulsoup4>=4.12",
    "lxml>=5.0",
    "rich>=13.7",
]

[project.scripts]
seobuddy = "seobuddy.cli:app"
```

---

## CLI Interface (`cli.py`)

```
seobuddy <URL> [OPTIONS]

Options:
  --depth INTEGER     Crawl depth  [default: 2]
  --concurrency INT   Parallel requests  [default: 5]
  --timeout INT       Request timeout seconds  [default: 10]
  --output-dir PATH   Where to write report  [default: ./]
  --user-agent TEXT   Custom UA string
  --no-color          Disable Rich colors
```

---

## Crawler (`crawler.py`)

- `AsyncCrawler` class using `httpx.AsyncClient`
- BFS queue with visited set (normalized URLs)
- Respects `depth` parameter — depth 0 = seed URL only, depth 2 = seed + 2 hops
- Only follows same-domain internal links
- Skips: anchors `#`, mailto, tel, non-HTML content types, already-visited
- Emits pages one at a time via async generator so display can update live
- Captures: URL, status code, response headers, HTML body, fetch time ms
- Handles redirects (follows up to 5), records final URL

---

## Audit Checks (`checks/`)

Each check returns `CheckResult(name, score, weight, status, findings, suggestions)`.

| Category | Weight | Key checks |
|---|---|---|
| **title** | 15% | presence, 50-60 char length, not duplicate |
| **meta** | 10% | description presence, 150-160 chars, not duplicate |
| **opengraph** | 10% | og:title, og:description, og:image, og:url all present |
| **jsonld** | 10% | valid JSON, schema type detected, required fields |
| **headings** | 10% | single H1, non-empty, no hierarchy gaps (H1→H3) |
| **content** | 15% | word count ≥300 (thin=0, ok=60, good=80, great=100), text/HTML ratio ≥15% |
| **links** | 10% | no broken internal links, descriptive anchors (not "click here") |
| **images** | 10% | all `<img>` have non-empty alt text, lazy loading present |
| **canonical** | 5% | canonical tag present, points to self (or known canonical) |
| **technical** | 5% | viewport meta present, HTTPS, URL length <75, no spaces in URL |

Score per category: 0–100.
Page score = weighted average of all categories.
Site score = average of all page scores.

---

## Terminal Display (`display.py`)

### Startup
```
╔═══════════════════════════════════════════╗
║  🔍 SEObuddy  v0.1.0                     ║
║  Auditing: https://example.com            ║
║  Depth: 2  |  Concurrency: 5             ║
╚═══════════════════════════════════════════╝
```

### Live crawl progress
- `rich.progress.Progress` with:
  - SpinnerColumn
  - TextColumn (current URL being fetched)
  - BarColumn
  - TaskProgressColumn `[n/total]`
  - TimeElapsedColumn

### Per-page result (printed as each page finishes)
- One-liner: `[score color] ██ 87/100  /about  — title ✓  meta ✗  og ✓  h1 ✓`

### Final summary panel
```
┌─────────────────────────────────────────────────────┐
│  SITE AUDIT COMPLETE  ·  example.com                │
│  12 pages  ·  8.3s  ·  Report: 202406041530-...md  │
├─────────────────────────────────────────────────────┤
│  OVERALL SCORE                                      │
│                                                     │
│       ████████████████░░░░  73/100  C+              │
│                                                     │
├──────────────┬───────────────────────┬──────────────┤
│  Category    │  Score                │  Pages OK    │
├──────────────┼───────────────────────┼──────────────┤
│  Title       │  ██████████  95/100   │  11/12       │
│  Meta Desc   │  ████░░░░░░  42/100   │   5/12       │
│  Open Graph  │  ███████░░░  68/100   │   8/12       │
│  JSON-LD     │  ██░░░░░░░░  20/100   │   2/12       │
│  Headings    │  █████████░  88/100   │  10/12       │
│  Content     │  ███████░░░  72/100   │   9/12       │
│  Links       │  ████████░░  80/100   │  10/12       │
│  Images      │  █████░░░░░  51/100   │   6/12       │
│  Canonical   │  ██████████  91/100   │  11/12       │
│  Technical   │  ████████░░  82/100   │  10/12       │
└──────────────┴───────────────────────┴──────────────┘

  TOP ISSUES (by impact)
  ① JSON-LD missing on 10/12 pages          → add structured data
  ② Meta description absent on 7/12 pages   → write unique descriptions
  ③ Images missing alt text (34 images)     → add descriptive alt attributes
```

Score colors: ≥80 green, 60-79 yellow, 40-59 orange, <40 red.

---

## Report File (`report.py`)

Filename: `yyyymmddhhmm-<hostname>-report.md`
Example: `202406041530-example.com-report.md`

Sections:
1. **Executive Summary** — score, date, URL, pages crawled, top 5 issues
2. **Score Breakdown** — table of categories with scores and pass/fail counts
3. **Page-by-Page Analysis** — collapsible `<details>` block per URL with all findings
4. **Recommendations** — sorted by impact (highest weight × worst score first), actionable bullet points

---

## Implementation Order

1. `pyproject.toml` + package scaffold (`__init__`, `__main__`, `cli.py` stub)
2. `checks/base.py` — `CheckResult` dataclass, scoring helpers
3. All 10 check modules (independent, test individually)
4. `auditor.py` — runs all checks on a parsed BeautifulSoup page
5. `crawler.py` — async BFS crawler
6. `display.py` — Rich UI components
7. `report.py` — Markdown generator
8. `cli.py` — wire everything together

---

## Verification

```bash
pip install -e .
seobuddy https://example.com --depth 2
# expect: live progress, per-page lines, final table, .md file written
seobuddy https://example.com --depth 0
# expect: single page audit only
seobuddy https://nonexistent.invalid
# expect: graceful error, no crash
```

Check report file exists at `./yyyymmddhhmm-example.com-report.md` and contains all sections.
