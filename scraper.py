"""Read-only Playwright scraper using a persistent Brave profile."""
from __future__ import annotations
import re
from dataclasses import dataclass, asdict
from typing import Any
from playwright.sync_api import sync_playwright
from config import PROFILE_DIR, brave_executable

@dataclass
class Unit:
    title: str
    objectives: list[str]
    content: str
    code_snippets: list[str]

@dataclass
class Module:
    url: str
    title: str
    description: str
    estimated_time: str
    units: list[Unit]
    review_questions: list[str]

def _text(node) -> str:
    return re.sub(r"\s+", " ", node.get_text(" ", strip=True)) if node else ""

def extract(url: str, headless: bool = True) -> dict[str, Any]:
    with sync_playwright() as pw:
        context = pw.chromium.launch_persistent_context(str(PROFILE_DIR), executable_path=brave_executable(), headless=headless, viewport={"width": 1440, "height": 1000})
        page = context.pages[0] if context.pages else context.new_page(); page.goto(url, wait_until="domcontentloaded", timeout=60000); page.wait_for_timeout(1500)
        text = re.sub(r"\s+", " ", page.locator("body").inner_text())
        vals = lambda selector: [re.sub(r"\s+", " ", x.strip()) for x in page.locator(selector).all_inner_texts() if x.strip()]
        title = page.locator("h1").first.inner_text() if page.locator("h1").count() else page.title()
        data = {"url": url, "title": title.strip(), "description": page.locator("meta[name='description']").get_attribute("content") or "", "badge_metadata": " | ".join(vals("[class*='badge'], [data-testid*='badge']")), "estimated_time": next(iter(re.findall(r"\b\d+\s*(?:min|minutes|hour|hours)\b", text, re.I)), "Not stated"), "body_text": text[:50000], "headings": vals("h1,h2,h3,h4"), "diagrams_tables": vals("table,figure"), "code_snippets": [x.strip() for x in page.locator("pre,code").all_inner_texts() if x.strip()], "practice_challenges": vals("[class*='challenge'], [data-testid*='challenge']"), "knowledge_checks": [x for x in vals("li,p") if x.endswith("?") or "knowledge check" in x.lower()]}
        context.close(); return data

def setup_browser() -> None:
    with sync_playwright() as pw:
        context = pw.chromium.launch_persistent_context(str(PROFILE_DIR), executable_path=brave_executable(), headless=False)
        page = context.pages[0] if context.pages else context.new_page(); page.goto("https://trailhead.salesforce.com/", wait_until="domcontentloaded")
        print("Log in to Trailhead in Brave, then close the browser window.")
        try: page.wait_for_event("close", timeout=300000)
        except Exception: context.close()

def parse_module(html: str, url: str) -> Module:
    soup = BeautifulSoup(html, "html.parser")
    title = _text(soup.select_one("h1")) or _text(soup.title) or "Untitled Trailhead Module"
    description = _text(soup.select_one("meta[name='description']"))
    if not description:
        description = _text(soup.select_one("[class*='description'], [data-testid*='description']"))
    page_text = _text(soup)
    time_match = re.search(r"(?:estimated|about)?\s*(\d+\s*(?:min|minutes|hour|hours))", page_text, re.I)
    estimated = time_match.group(1) if time_match else "Not stated"
    units: list[Unit] = []
    headings = soup.select("h2, h3")
    for heading in headings:
        unit_title = _text(heading)
        if not unit_title or unit_title.lower() in {"overview", "resources"}:
            continue
        content_nodes = []
        for sibling in heading.find_all_next():
            if sibling.name in {"h2", "h3"} and sibling is not heading:
                break
            if sibling.name in {"p", "li", "pre", "code"}:
                content_nodes.append(sibling)
        content = "\n".join(_text(n) for n in content_nodes[:120])
        objectives = [_text(x) for x in heading.find_all_next("li")[:8] if "learn" in _text(x).lower() or "understand" in _text(x).lower()]
        snippets = [n.get_text("\n", strip=True) for n in content_nodes if n.name in {"pre", "code"}]
        units.append(Unit(unit_title, objectives, content[:12000], snippets[:10]))
    questions = []
    for node in soup.select("li, p"):
        text = _text(node)
        if "check your knowledge" in text.lower() or text.endswith("?"):
            questions.append(text)
    return Module(url, title, description, estimated, units, list(dict.fromkeys(questions))[:30])

def scrape(url: str, cookies: dict[str, str] | None = None) -> dict[str, Any]:
    return asdict(parse_module(fetch_html(url, cookies), url))


