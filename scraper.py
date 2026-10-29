"""Read-only Trailhead extraction with Brave-local and hosted HTTP fallback."""
from __future__ import annotations
import re
from typing import Any
import httpx
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
from config import PROFILE_DIR, brave_executable

def _clean(value: str | None) -> str: return re.sub(r"\s+", " ", value or "").strip()
def _soup_data(html: str, url: str) -> dict[str, Any]:
    soup = BeautifulSoup(html, "html.parser"); body = _clean(soup.get_text(" ", strip=True)); vals = lambda selector: [_clean(x.get_text(" ", strip=True)) for x in soup.select(selector) if _clean(x.get_text(" ", strip=True))]
    return {"url": url, "title": _clean(soup.select_one("h1").get_text() if soup.select_one("h1") else soup.title.get_text() if soup.title else "Trailhead module"), "description": soup.select_one("meta[name='description']").get("content", "") if soup.select_one("meta[name='description']") else "", "badge_metadata": " | ".join(vals("[class*='badge'], [data-testid*='badge']")), "estimated_time": next(iter(re.findall(r"\b\d+\s*(?:min|minutes|hour|hours)\b", body, re.I)), "Not stated"), "body_text": body[:50000], "headings": vals("h1,h2,h3,h4"), "diagrams_tables": vals("table,figure"), "code_snippets": [x.get_text("\n", strip=True) for x in soup.select("pre,code") if x.get_text(strip=True)], "practice_challenges": vals("[class*='challenge'], [data-testid*='challenge']"), "knowledge_checks": [x for x in vals("li,p") if x.endswith("?") or "knowledge check" in x.lower()]}

def _brave_extract(url: str, headless: bool) -> dict[str, Any]:
    with sync_playwright() as pw:
        context = pw.chromium.launch_persistent_context(str(PROFILE_DIR), executable_path=brave_executable(), headless=headless, viewport={"width": 1440, "height": 1000})
        page = context.pages[0] if context.pages else context.new_page(); page.goto(url, wait_until="domcontentloaded", timeout=60000); page.wait_for_timeout(1500)
        result = _soup_data(page.content(), url); context.close(); return result

def _http_extract(url: str) -> dict[str, Any]:
    response = httpx.get(url, follow_redirects=True, timeout=30, headers={"User-Agent": "TrailheadStudyAssistant/1.0"}); response.raise_for_status(); return _soup_data(response.text, url)

def extract(url: str, headless: bool = True) -> dict[str, Any]:
    try: return _brave_extract(url, headless)
    except Exception as brave_error:
        try:
            data = _http_extract(url); data["extraction_note"] = f"Brave was unavailable; used public HTML fallback: {type(brave_error).__name__}"; return data
        except Exception: raise RuntimeError("Could not extract the page. Local mode needs Brave; hosted mode needs a publicly accessible Trailhead URL.") from brave_error

def setup_browser() -> None:
    with sync_playwright() as pw:
        context = pw.chromium.launch_persistent_context(str(PROFILE_DIR), executable_path=brave_executable(), headless=False)
        page = context.pages[0] if context.pages else context.new_page(); page.goto("https://trailhead.salesforce.com/", wait_until="domcontentloaded"); print("Log in to Trailhead in Brave, then close the browser window.")
        try: page.wait_for_event("close", timeout=300000)
        except Exception: context.close()

