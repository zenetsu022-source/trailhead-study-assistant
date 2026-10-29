from __future__ import annotations
import json
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
    response = client.models.generate_content(model=MODEL, contents=PROMPT + json.dumps(extraction, ensure_ascii=False), config=types.GenerateContentConfig(response_mime_type="application/json", response_schema=ModuleReport, temperature=0.2))
    return ModuleReport.model_validate_json(response.text)


