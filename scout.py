"""page-scout: a tiny Playwright "research step" for an AI agent.

Given a URL, open it in a headless browser (so JavaScript-rendered content
is included) and return a small, structured profile of the page.
"""
from __future__ import annotations

import argparse
import json
import re
from dataclasses import asdict, dataclass, field

from playwright.sync_api import sync_playwright

EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
SOCIAL_HOSTS = ("linkedin.com", "github.com", "x.com", "twitter.com", "youtube.com")


@dataclass
class PageProfile:
    url: str
    title: str = ""
    description: str = ""
    headings: list[str] = field(default_factory=list)
    emails: list[str] = field(default_factory=list)
    social_links: list[str] = field(default_factory=list)
    text_excerpt: str = ""


def scout(url: str, screenshot: str | None = None, timeout_ms: int = 15000) -> PageProfile:
    """Open `url`, extract facts, return them as a PageProfile."""
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        try:
            page.goto(url, wait_until="networkidle", timeout=timeout_ms)

            title = page.title()
            description = page.eval_on_selector(
                'meta[name="description"]', "el => el.content"
            ) if page.query_selector('meta[name="description"]') else ""
            headings = [h.strip() for h in page.locator("h1, h2").all_inner_texts() if h.strip()]
            hrefs = page.eval_on_selector_all("a[href]", "els => els.map(e => e.href)")
            body_text = page.inner_text("body")

            if screenshot:
                page.screenshot(path=screenshot, full_page=True)
        finally:
            browser.close()

    mailto = {h.removeprefix("mailto:").split("?")[0] for h in hrefs if h.startswith("mailto:")}
    emails = sorted(mailto | set(EMAIL_RE.findall(body_text)))
    social = sorted({h for h in hrefs if any(s in h for s in SOCIAL_HOSTS)})
    # excerpt = " ".join(body_text.split())[:300]
    # excerpt = body_text

    return PageProfile(url, title, description, headings, emails, social)


def main() -> None:
    ap = argparse.ArgumentParser(description="Scout a web page with Playwright.")
    ap.add_argument("url")
    ap.add_argument("--screenshot", help="save a full-page PNG to this path")
    ap.add_argument("--out", help="write JSON to this file instead of stdout")
    args = ap.parse_args()

    profile = scout(args.url, screenshot=args.screenshot)
    data = json.dumps(asdict(profile), indent=2, ensure_ascii=False)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(data)
    else:
        print(data)


if __name__ == "__main__":
    main()
