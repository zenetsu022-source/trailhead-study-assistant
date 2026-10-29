from __future__ import annotations
import os, platform
from pathlib import Path
from dotenv import load_dotenv
load_dotenv()
ROOT = Path(__file__).resolve().parent
PROFILE_DIR = Path(os.getenv("TRAILHEAD_BROWSER_PROFILE", ROOT / ".brave-profile"))
MODEL = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")
def brave_executable() -> str:
    override = os.getenv("BRAVE_EXECUTABLE_PATH")
    if override: return override
    candidates = {"Windows": r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe", "Darwin": "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser", "Linux": "/usr/bin/brave-browser"}
    path = candidates.get(platform.system(), "")
    if not Path(path).exists(): raise FileNotFoundError(f"Brave executable not found at {path!r}. Set BRAVE_EXECUTABLE_PATH.")
    return path
def gemini_api_key() -> str:
    key = os.getenv("GEMINI_API_KEY")
    if not key: raise RuntimeError("GEMINI_API_KEY is missing.")
    return key

