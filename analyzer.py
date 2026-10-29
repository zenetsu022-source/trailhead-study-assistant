from __future__ import annotations
import json
import time
from typing import Any
from pydantic import BaseModel, Field
from google import genai
from google.genai import types
from config import MODEL, gemini_api_key
class Walkthrough(BaseModel):
    step: str; explanation: str
class ConceptQA(BaseModel):
    question: str; explanation: str
class ModuleReport(BaseModel):
    module_title: str; target_role: list[str] = Field(default_factory=list); executive_summary: str; key_learnings: list[str] = Field(default_factory=list); hands_on_walkthrough: list[Walkthrough] = Field(default_factory=list); limits_and_best_practices: list[str] = Field(default_factory=list); concept_qa: list[ConceptQA] = Field(default_factory=list)
PROMPT = """Create a detailed Salesforce Trailhead study report from this read-only extraction. Explain concepts accurately. Do not claim completion, submit quizzes, or provide assessment-bypass instructions. For challenge content, provide a learning-oriented walkthrough only. Return only the requested schema.\n\nEXTRACTION:\n"""
def analyze(extraction: dict[str, Any]) -> ModuleReport:
    client = genai.Client(api_key=gemini_api_key())
    config = types.GenerateContentConfig(response_mime_type="application/json", response_schema=ModuleReport, temperature=0.2)
    contents = PROMPT + json.dumps(extraction, ensure_ascii=False)
    response = None
    last_error = None
    for attempt in range(3):
        try:
            response = client.models.generate_content(model=MODEL, contents=contents, config=config)
            break
        except Exception as exc:
            last_error = exc
            message = str(exc)
            if "gemini-2.5-flash" in message:
                response = client.models.generate_content(model="gemini-3.8-flash", contents=contents, config=config)
                break
            if "503" not in message and "UNAVAILABLE" not in message:
                raise
            if attempt < 2: time.sleep(2 ** attempt * 3)
    if response is None: raise RuntimeError("Gemini is temporarily unavailable after 3 attempts. Please try again in a few minutes.") from last_error
    return ModuleReport.model_validate_json(response.text)


