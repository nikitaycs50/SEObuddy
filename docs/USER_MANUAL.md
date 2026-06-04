# SEObuddy User Manual

SEObuddy is a command-line tool that crawls your website and produces a **technical SEO audit**. You see live progress and scores in the terminal, and get a **Markdown report** you can open in any editor or share with your team.

> **Note:** This CLI is not affiliated with the commercial product at [seobuddy.com](https://seobuddy.com/).

---

## Quick start

### 1. Install

**From PyPI:**

```bash
pip install seobuddy
# or: pipx install seobuddy   # recommended for a global CLI on macOS/Linux
```

Upgrade:

```bash
pip install -U seobuddy
# or: pipx upgrade seobuddy
```

**From source** (development):

```bash
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e .
```

Confirm the command is available:

```bash
seobuddy --help
```

### 2. Run a simple audit

```bash
seobuddy https://nikitay.com
```

This uses default settings: crawl **depth 2** (homepage plus two link hops), **5** parallel requests, **10** second timeout, report written to the current directory.

### 3. Read the results

- Watch the **terminal** for per-page scores and a final summary table.
- Open the generated file `yyyymmddhhmm-<hostname>-report.md` (for example `202606041408-nikitay.com-report.md`).

---

## Verified example: nikitay.com

| URL | Result |
|-----|--------|
| `https://nikitay.com` | Works — crawls the site, prints scores, writes a report |
| `https://niktiay.com` | **Fails** — hostname does not resolve (typo: missing **k** in *nikitay*) |

Use the correct spelling: **nikitay.com**, not `niktiay.com`.

Example command and expected behavior:

```bash
seobuddy https://nikitay.com --depth 1
```

You should see:

1. A blue **SEObuddy** banner with version, URL, depth, concurrency, and the User-Agent in use.
2. A **progress bar** while pages are fetched.
3. **One line per page** with score, path, and quick checks (title, meta, Open Graph, H1).
4. A **SITE AUDIT COMPLETE** panel with overall score, category table, and top issues.
5. A **report file** in the output directory.

Sample overall outcome (scores vary over time):

- Homepage often scores higher than auxiliary URLs.
- Typical improvement areas: JSON-LD, content depth, title length, meta description length.

---

## Command reference

```text
seobuddy <URL> [OPTIONS]
```

### Arguments

| Argument | Description |
|----------|-------------|
| `URL` | Full site URL to audit (`https://` recommended). Bare domains like `nikitay.com` are accepted and normalized to `https://`. |

### Options

| Option | Default | Description |
|--------|---------|-------------|
| `--depth` | `2` | How many link hops from the seed URL to follow. `0` = only the seed page. |
| `--max-pages` | `50` | Stop after this many pages (recommended for large sites). |
| `--concurrency` | `5` | Maximum parallel HTTP requests during the crawl. |
| `--timeout` | `10` | Per-request timeout in seconds. |
| `--output-dir` | `.` | Folder where the Markdown report is saved. |
| `--user-agent` | Chrome 131 (desktop) | HTTP User-Agent on every request. Default mimics Chrome for compatibility; override if you need an identifiable bot string. |
| `--no-color` | off | Plain terminal output (no Rich colors). |

### Common recipes

**Homepage only (fast check):**

```bash
seobuddy https://nikitay.com --depth 0
```

**Deeper crawl:**

```bash
seobuddy https://nikitay.com --depth 2 --concurrency 10
```

**Save reports to a folder:**

```bash
seobuddy https://nikitay.com --output-dir ./reports
```

**Custom User-Agent (default is Chrome-like):**

```bash
seobuddy https://nikitay.com --user-agent "SEObuddy/0.2.0 (+https://nikitay.com)"
```

**Run without colors (logs, CI):**

```bash
seobuddy https://nikitay.com --no-color
```

**Alternative entry point:**

```bash
python -m seobuddy https://nikitay.com
```

---

## Understanding the terminal output

### Startup banner

Shows version, target URL, crawl depth, concurrency, and the User-Agent in use (Chrome desktop by default).

### Live progress

While crawling:

- Spinner and **current URL** being fetched.
- Progress bar and **elapsed time**.

### Per-page line

Format:

```text
█████░░░ 63/100  /  — title ✗  meta ~  og ✓  h1 ✓
```

| Symbol | Meaning |
|--------|---------|
| `█` / `░` | Visual score bar |
| `63/100` | Weighted page score |
| `/` or `/path` | URL path audited |
| `✓` | Category passed (score ≥ 80) |
| `~` | Category warning (60–79) |
| `✗` | Category failed (&lt; 60) |

### Score colors

| Score | Color |
|-------|-------|
| 80–100 | Green |
| 60–79 | Yellow |
| 40–59 | Orange |
| 0–39 | Red |

### Final summary

- **Overall score** and letter grade (A, B, C+, C, D, F).
- **Category table** — average score per check type and how many pages passed (≥ 80).
- **TOP ISSUES** — highest-impact weaknesses across the site.

### Letter grades

| Grade | Score range |
|-------|-------------|
| A | 90+ |
| B | 80–89 |
| C+ | 70–79 |
| C | 60–69 |
| D | 50–59 |
| F | Below 50 |

---

## The Markdown report

### Filename

```text
yyyymmddhhmm-<hostname>-report.md
```

Example: `202606041408-nikitay.com-report.md`

### Sections

1. **Executive Summary** — site score, date, seed URL, page count, duration, top 5 issues.
2. **Score Breakdown** — table of all categories with scores and pages OK.
3. **Page-by-Page Analysis** — collapsible `<details>` block per URL with findings and suggestions.
4. **Recommendations** — prioritized, deduplicated action items.

Open the file in VS Code, Cursor, GitHub, or any Markdown viewer. Collapsible sections render in viewers that support HTML `<details>`.

---

## What SEObuddy checks

| Category | What it looks for |
|----------|-------------------|
| **Title** | `<title>` present, ~50–60 characters, unique across crawled pages |
| **Meta description** | `meta name="description"`, ~150–160 characters, unique |
| **Open Graph** | `og:title`, `og:description`, `og:image`, `og:url` |
| **JSON-LD** | Valid `application/ld+json` with sensible schema fields |
| **Headings** | Exactly one H1, logical heading order |
| **Content** | Word count (300+), text vs HTML ratio |
| **Links** | Internal links reachable, avoid generic anchor text |
| **Images** | `alt` attributes on images |
| **Canonical** | `link rel="canonical"` present and consistent |
| **Technical** | Viewport meta, HTTPS, reasonable URL length |

Page score = weighted average of categories. Site score = average of all page scores.

---

## Large sites (Google, etc.)

SEObuddy is aimed at **your own site** or small/medium properties. Crawling `google.com` with default settings used to flood the terminal with locale redirect URLs (`/ml?continue=…`) and XML warnings.

Improvements in v0.1:

- **`--max-pages 50`** (default) caps the crawl; the summary shows *Crawl limit reached* when applicable.
- Paths like **`/ml`**, **`/intl/…`**, policies, and preferences are skipped.
- **Query-string duplicates** are not crawled separately (`?hl=de` vs `?hl=en` share one path).
- **Long URLs** are shortened in the terminal.
- **Non-HTML** and XML responses are not parsed as HTML (no XML warning spam).

For Google, prefer: `seobuddy https://google.com --depth 0` or `--max-pages 10`.

---

## Crawl behavior (what gets audited)

- Only **same-domain** links are followed (external sites are ignored).
- **Depth** controls how far from the homepage links are followed.
- Skipped automatically: `mailto:`, `tel:`, fragments-only links, non-HTML pages, CDN utility paths like `/cdn-cgi/`, duplicate URLs.
- Redirects are followed (up to 5 hops); audits use the **final URL**.

---

## Errors and exit codes

| Situation | Behavior | Exit code |
|-----------|----------|-----------|
| Successful audit | Report written, summary shown | `0` |
| Bad URL format | Clear error message | `1` |
| Host unreachable (DNS, connection) | `Could not connect to host` | `1` |
| Request timeout | Error message | `1` |

**Tips:**

- Double-check spelling (`nikitay.com` vs `niktiay.com`).
- Ensure the site is online. The default Chrome-like User-Agent works on most hosts; try `--user-agent` with a custom string if you get blocked.
- Increase `--timeout` on slow hosts: `seobuddy https://nikitay.com --timeout 30`.

---

## Troubleshooting

### `command not found: seobuddy`

**Installed from PyPI:** ensure your install path is on `PATH`:

```bash
pip install seobuddy
# or: pipx install seobuddy
pipx ensurepath   # if pipx was just installed
```

**Developing from source:** activate the virtual environment and reinstall:

```bash
source .venv/bin/activate
pip install -e .
```

### `externally-managed-environment` (macOS Homebrew Python)

Prefer `pipx install seobuddy` for a global CLI, or use a project virtual environment — do not install into system Python with plain `pip install`.

### `Could not connect to host`

- Verify the URL in a browser.
- Check for typos in the domain name.
- Try `ping nikitay.com` or `curl -I https://nikitay.com`.

### Very low content score on modern SPAs

SEObuddy analyzes **HTML returned by HTTP**. Heavy client-side rendering may show thin content even if the rendered page looks full in a browser.

### Unexpected extra pages in the crawl

Some sites inject links (e.g. email protection). SEObuddy skips common CDN paths under `/cdn-cgi/`.

---

## Privacy and etiquette

- SEObuddy only requests URLs you point it at, within the same domain and depth you set.
- Default requests use a **Chrome desktop** User-Agent for compatibility; set `--user-agent` explicitly if your policy requires an identifiable bot string.
- Crawl respects **robots.txt** `Disallow` for your User-Agent; use reasonable depth and concurrency on live sites.

---

## Further reading

- [Report Example](REPORT_EXAMPLE.md) — sample terminal summary and Markdown report (`google.com` audit).
- [Technical Manual](TECHNICAL_MANUAL.md) — architecture, code layout, scoring formulas, tests.
- [Publishing](PUBLISHING.md) — PyPI releases (maintainers).
- [README](../README.md) — project overview and development setup.

---

Licensed under the MIT License — see [LICENSE](../LICENSE).

Copyright © 2026 [NikitaY.com](https://nikitay.com/). Created by [NikitaY.com](https://nikitay.com/).
