from __future__ import annotations
import re
from pathlib import Path
import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from config import MODEL
from scraper import extract, setup_browser
from analyzer import analyze
from pdf_builder import build_pdf
app = typer.Typer(help="Brave + Gemini Trailhead study assistant (read-only)"); console = Console()
def slug(value: str) -> str: return re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")[:80] or "trailhead_module"
@app.command("setup-browser")
def setup(): setup_browser()
@app.command()
def digest(url: str = typer.Option(...), out_dir: Path = typer.Option(Path("./exports"), "--out-dir")):
    with Progress(SpinnerColumn(), TextColumn("{task.description}"), console=console) as p:
        task = p.add_task("Extracting through Brave...", total=None); data = extract(url); p.update(task, description="Extracted module content"); p.update(task, description=f"Generating structured Gemini report ({MODEL})..."); report = analyze(data); p.update(task, description="Gemini report validated"); out = build_pdf(data, report, out_dir / f"{slug(report.module_title)}.pdf"); p.update(task, description=f"PDF saved to {out}")
    console.print(f"[green]Created:[/green] {out}")
if __name__ == "__main__": app()


