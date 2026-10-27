# page-scout

A tiny Playwright tool that acts as the **research step** of an AI agent:
give it a URL, it opens the page in a real (headless) browser and returns a
small structured profile (title, description, headings, emails, social links,
text excerpt) as JSON.

## Why Playwright and not `requests`?

Many sites build their content with JavaScript. A plain HTTP request sees an
almost empty page; a browser sees what a visitor sees. The test fixture
demonstrates this: the "Our team" section and one email address only appear
after a script runs.

## Architecture

```
 URL ──► scout()                                   ──► PageProfile ──► JSON
          │
          ├─ 1. Playwright launches headless Chromium
          ├─ 2. goto(url), wait until the network is idle (JS has run)
          ├─ 3. extract: title, <meta description>, h1/h2, links, body text
          ├─ 4. close the browser (always, via try/finally)
          └─ 5. clean up in plain Python: regex emails, filter social links
```

- `scout.py`: one function `scout(url)` plus a small CLI. Browser work
  (steps 1-4) is separated from data cleanup (step 5), so step 5 can be
  tested without a browser later.
- `PageProfile`: a dataclass, so the output has a fixed schema an LLM
  or database can consume.
- `tests/`: pytest starts a local HTTP server that serves
  `tests/fixtures/company.html`, so tests never depend on the internet.

## Run it

```bash
pip install -r requirements.txt
playwright install chromium

python scout.py https://example.com
python scout.py https://example.com --screenshot page.png --out profile.json
pytest
```

## Where an agent would use it

Outreach / research agent: for each target company, `scout()` gathers facts
with their source URL, then an LLM step (e.g. in LangGraph) validates them and
drafts a personalised first message. Next steps: crawl a few subpages
(`/about`, `/team`), add retries and rate limiting, respect robots.txt, and
let an LLM turn the profile into a structured company summary.

## Limits

Sites may forbid automated access in their terms or robots.txt; check before
scraping, and prefer official APIs when they exist. Personal data (such as
email addresses) falls under GDPR.
