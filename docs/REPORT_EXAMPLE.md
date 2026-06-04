# SEObuddy Report Example

This document shows **sample output** from a real audit run. It is for documentation only — not generated on every install.

## Command

```bash
seobuddy https://google.com --depth 2
```

**Report file written:** `202606041412-google.com-report.md` (in the working directory)

---

## Terminal — final summary

After the crawl finishes, SEObuddy prints a Rich summary panel like this:

```text
╭───────────────────────────────────────────────────────────────────────────────╮
│ SITE AUDIT COMPLETE  ·  google.com                                            │
│ 19 pages  ·  7.2s  ·  Report: 202606041412-google.com-report.md             │
╰───────────────────────────────────────────────────────────────────────────────╯
╭───────────────────────────────────────────────────────────────────────────────╮
│ OVERALL SCORE                                                                 │
│                                                                               │
│        █████████░░░░░░░░░░░  47/100  F                                        │
╰───────────────────────────────────────────────────────────────────────────────╯
┏━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━┓
┃ Category   ┃ Score              ┃ Pages OK ┃
┡━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━┩
│ Title      │ ████░░░░░░  47/100 │     2/19 │
│ Meta Desc  │ ░░░░░░░░░░  9/100  │     0/19 │
│ Open Graph │ ░░░░░░░░░░  9/100  │     1/19 │
│ JSON-LD    │ ░░░░░░░░░░  9/100  │     1/19 │
│ Headings   │ ██████░░░░  66/100 │    11/19 │
│ Content    │ ████░░░░░░  47/100 │     2/19 │
│ Links      │ █████████░  92/100 │    18/19 │
│ Images     │ ████████░░  85/100 │    16/19 │
│ Canonical  │ █░░░░░░░░░  17/100 │     1/19 │
│ Technical  │ █████████░  92/100 │    14/19 │
└────────────┴────────────────────┴──────────┘

TOP ISSUES (by impact)
  ① Meta Desc weak (avg 9/100, 0/19 pages OK)
  ② Open Graph weak (avg 9/100, 1/19 pages OK)
  ③ JSON-LD weak (avg 9/100, 1/19 pages OK)
  ④ Title weak (avg 47/100, 2/19 pages OK)
  ⑤ Content weak (avg 47/100, 2/19 pages OK)
```

During the crawl you also see a startup banner, a progress bar with the current URL, and **one line per page** (score bar, path, quick check icons: `✓` / `~` / `✗`).

---

## Markdown report — structure

The file on disk mirrors the terminal summary and adds per-page detail. Filename pattern:

```text
yyyymmddhhmm-<hostname>-report.md
```

Below is the **full executive summary and score breakdown** from this run, plus **two sample pages** (lowest homepage score and highest-scoring page). The real report contains all **19** collapsible page sections and a full recommendations list.

---

# SEObuddy SEO Audit Report

## 1. Executive Summary

- **Overall score:** 47/100 (F)
- **Date:** 2026-06-04 14:12
- **Seed URL:** https://google.com/
- **Pages crawled:** 19
- **Duration:** 7.2s

### Top issues

- ① Meta Desc weak (avg 9/100, 0/19 pages OK)
- ② Open Graph weak (avg 9/100, 1/19 pages OK)
- ③ JSON-LD weak (avg 9/100, 1/19 pages OK)
- ④ Title weak (avg 47/100, 2/19 pages OK)
- ⑤ Content weak (avg 47/100, 2/19 pages OK)

## 2. Score Breakdown

| Category | Score | Pages OK |
|----------|------:|---------:|
| Title | 47/100 | 2/19 |
| Meta Desc | 9/100 | 0/19 |
| Open Graph | 9/100 | 1/19 |
| JSON-LD | 9/100 | 1/19 |
| Headings | 66/100 | 11/19 |
| Content | 47/100 | 2/19 |
| Links | 92/100 | 18/19 |
| Images | 85/100 | 16/19 |
| Canonical | 17/100 | 1/19 |
| Technical | 92/100 | 14/19 |

## 3. Page-by-Page Analysis (samples)

<details>
<summary>/ — 32/100 (homepage)</summary>

- **URL:** https://www.google.com/
- **Status:** 200

### Title (40/100)
- Title length suboptimal (6 chars)

Suggestions:
- Aim for 50–60 characters in the title tag

### Meta Desc (0/100)
- Missing meta description

Suggestions:
- Add meta name='description' (150–160 characters)

### Open Graph (0/100)
- Missing og:title
- Missing og:description
- Missing og:image
- Missing og:url

### JSON-LD (0/100)
- No JSON-LD structured data found

### Headings (20/100)
- No H1 heading found

### Content (0/100)
- Thin content (29 words; minimum 300)
- Low text/HTML ratio (0.3%; aim ≥15%)

### Links (100/100)
- Internal links look healthy

### Images (100/100)
- All images have alt text

### Canonical (0/100)
- Missing canonical link tag

### Technical (75/100)
- Missing viewport meta tag

</details>

<details>
<summary>/ — 77/100 (best page in this crawl: about.google)</summary>

- **URL:** https://about.google/
- **Status:** 200

### Title (40/100)
- Title length suboptimal (77 chars)

### Meta Desc (70/100)
- Meta description length acceptable (144 chars)

### Open Graph (100/100)
- og:title present
- og:description present
- og:image present
- og:url present

### JSON-LD (100/100)
- Valid WebSite with required fields

### Headings (100/100)
- Single H1 present

### Content (34/100)
- Moderate content (315 words)
- Low text/HTML ratio (1.4%; aim ≥15%)

### Links (90/100)
- Generic anchor text on 2 link(s)

### Images (100/100)
- All images have alt text

### Canonical (100/100)
- Canonical points to this page

### Technical (100/100)
- Technical basics look good

</details>

> **Note:** This crawl also included consent pages, policy URLs, support articles, and other same-domain paths. Scores vary widely by page type. Large sites with minimal HTML (search homepages) often score low on meta, Open Graph, and content checks even when the product is healthy in a browser.

## 4. Recommendations (excerpt)

Prioritized, deduplicated actions from the full report:

- Add meta name='description' (150–160 characters)
- Add meta property='og:title'
- Add meta property='og:description'
- Add meta property='og:image'
- Add meta property='og:url'
- Add schema.org JSON-LD (Organization, WebSite, or Article)
- Aim for 50–60 characters in the title tag
- Use a unique title for each page
- Add substantive content (300+ words)
- Reduce boilerplate markup; increase visible text
- Add `<link rel='canonical' href='...'>` pointing to preferred URL
- Add exactly one H1 with primary page topic
- Add descriptive alt attributes to all images
- Fix or remove broken internal links
- Add `<meta name='viewport' content='width=device-width, initial-scale=1'>`
- Use HTTPS for all pages

---

## Reading this example

| Output | Where |
|--------|--------|
| Live progress & per-page lines | Terminal only |
| Final panels & TOP ISSUES | Terminal (matches report §1–2) |
| Full per-page findings | Markdown report §3 (`<details>` blocks) |
| Full action list | Markdown report §4 |

See also [User Manual](USER_MANUAL.md) and [Technical Manual](TECHNICAL_MANUAL.md).

---

Copyright © 2026 [NikitaY.com](https://nikitay.com/). Created by [NikitaY.com](https://nikitay.com/).
