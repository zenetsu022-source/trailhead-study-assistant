# Salesforce Trailhead Study Assistant & Documentation Generator

A local, read-only Python pipeline that automates Brave with a persistent Playwright profile, extracts Trailhead content, synthesizes a structured study guide with Google Gemini, and exports a professional PDF. It does not submit quizzes, hands-on challenges, or certifications.

## Setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
# Optional, for authenticated/dynamic pages:
playwright install chromium
```

Create a `.env` file with `GEMINI_API_KEY=...`. Optionally set `GEMINI_MODEL`, `BRAVE_EXECUTABLE_PATH`, or `TRAILHEAD_BROWSER_PROFILE`. Never share credentials.

## Usage

```powershell
python main.py setup-browser
python main.py digest --url https://trailhead.salesforce.com/content/learn/modules/... --out-dir ./exports
```

The command writes `<Module_Name>.pdf`. Knowledge checks and challenge instructions are summarized conceptually for study and are never automatically submitted.

## Easy web UI

Install the dependencies, create a `.env` file containing `GEMINI_API_KEY=your-key`, then run:

```powershell
streamlit run app.py
```

Open the local address Streamlit prints, click **Open Brave Login** once, log in to Trailhead, close Brave, then paste a module URL and click **Generate Study Guide**. The finished PDF can be downloaded directly from the page.

## Modules

- `config.py` — environment settings and Brave path discovery.
- `scraper.py` — persistent Brave Playwright extraction.
- `analyzer.py` — Gemini structured output and Pydantic validation.
- `pdf_builder.py` — ReportLab layout, footer/page numbering, callouts, and code blocks.
- `main.py` — Typer CLI with Rich progress feedback.


