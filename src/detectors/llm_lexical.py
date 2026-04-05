import json

import instructor
from langfuse import observe
from openai import OpenAI
from pydantic import BaseModel

from src.schemas import SubAgentFinding, SubAgentReport


class _FindingsList(BaseModel):
    findings: list[SubAgentFinding]


_PROMPT = """\
You are an AI writing auditor. Analyze the following sentences for LEXICAL AI writing patterns.

Detect ONLY these two patterns:

1. SYNONYM ROTATION: Using different words for the same concept within the same paragraph to avoid
   repetition. Example: "developers... engineers... practitioners... builders" all meaning the same
   thing in one paragraph.

2. SIGNIFICANCE INFLATION: Phrases that inflate routine events into major milestones without
   justification. Examples: "watershed moment", "paradigm-shifting", "unprecedented achievement",
   "marking a pivotal moment".

Sentences to analyze (sentence_id → text):
{sentences_json}

Return findings ONLY for sentences that clearly exhibit these patterns.
If a sentence is clean, do not include it.
Return an empty findings list if nothing is found.
For severity: "high" = clear violation, "medium" = likely violation, "low" = possible.
"""


class LLMLexicalAgent:
    """Detects synonym rotation and significance inflation via Ollama."""

    def __init__(self, model: str) -> None:
        self.model = model

    def _call_llm(self, sentences: dict[str, str]) -> list[SubAgentFinding]:
        client = instructor.from_openai(
            OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")
        )
        prompt = _PROMPT.format(sentences_json=json.dumps(sentences, indent=2))
        result = client.chat.completions.create(
            model=self.model,
            response_model=_FindingsList,
            messages=[{"role": "user", "content": prompt}],
        )
        return result.findings

    @observe()
    def run(self, sentences: dict[str, str]) -> SubAgentReport:
        findings = self._call_llm(sentences)
        return SubAgentReport(category="lexical", findings=findings)
