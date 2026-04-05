import json

import instructor
from langfuse import observe
from openai import OpenAI
from pydantic import BaseModel

from src.schemas import SubAgentFinding, SubAgentReport


class _FindingsList(BaseModel):
    findings: list[SubAgentFinding]


_PROMPT = """\
You are an AI writing auditor. Analyze the following sentences for RHYTHMIC AI writing patterns.

Detect ONLY these two patterns:

1. MECHANICAL PADDING: Filler phrases that add words without meaning.
   Examples: "it is important to note that", "in order to", "it goes without saying",
   "needless to say", "as a matter of fact", "it is worth mentioning that",
   "it should be noted that", "one must consider that".

2. OVER-POLISHED UNIFORMITY: Sentences that form part of a conspicuously uniform passage — every
   sentence is the same length (15-25 words), follows the same subject-verb-object structure, and
   has no fragments, no asides, no variety. AI text is metronomic. Human text is not.
   Flag representative sentences from the uniform passage — not every sentence, just enough to
   identify the pattern. Do not flag individual long sentences — only flag when the passage as a
   whole is uniform.

Sentences to analyze (sentence_id → text):
{sentences_json}

Return findings ONLY for sentences that clearly exhibit these patterns.
If no patterns are found, return an empty findings list.
For severity: "high" = clear violation, "medium" = likely violation, "low" = possible.
"""


class LLMRhythmicAgent:
    """Detects rhythmic AI writing patterns via Ollama."""

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
        return SubAgentReport(category="rhythmic", findings=findings)
