import json

import instructor
from langfuse import observe
from openai import OpenAI
from pydantic import BaseModel

from src.schemas import SubAgentFinding, SubAgentReport


class _FindingsList(BaseModel):
    findings: list[SubAgentFinding]


_PROMPT = """\
You are an AI writing auditor. Analyze the following sentences for TONAL AI writing patterns.

Detect ONLY these four patterns:

1. EXCESSIVE HEDGING: Unnecessary qualifiers that weaken a clear claim.
   Examples: "it could be argued", "one might say", "perhaps", "it is possible that",
   "it seems", "to some extent".

2. SYCOPHANTIC OPENER: Phrases that praise the reader or question before answering.
   Examples: "Great question!", "Certainly!", "Absolutely!", "That's a fascinating point",
   "Excellent observation!".

3. FORCED VARIATION: The writer's voice lacks a settled identity — verb choices, tone descriptors,
   and attributive phrases shift unnaturally within the same passage. Unlike synonym rotation (a
   lexical pattern about nouns), this is about tonal inconsistency: one sentence is formal, the next
   is casual; one uses active voice confidently, the next hedges. The overall effect is a voice that
   feels assembled rather than authored.

4. RELENTLESSLY NEUTRAL VOICE: Text that aggressively avoids all opinion, preference, or stance.
   Flag only when the piece clearly calls for voice (personal essay, opinion piece, blog post with
   first-person framing) yet contains zero stated opinions, reactions, or preferences across the
   full passage. Do not flag individual neutral sentences — flag only when the entire passage is
   conspicuously opinion-free.

Sentences to analyze (sentence_id → text):
{sentences_json}

Return findings ONLY for sentences that clearly exhibit these patterns.
If no patterns are found, return an empty findings list.
For severity: "high" = clear violation, "medium" = likely violation, "low" = possible.
"""


class LLMTonalAgent:
    """Detects tonal AI writing patterns via Ollama."""

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
        return SubAgentReport(category="tonal", findings=findings)
