import json

import instructor
from langfuse import observe
from pydantic import BaseModel

from src.schemas import SubAgentFinding, SubAgentReport


class _FindingsList(BaseModel):
    findings: list[SubAgentFinding]


_PROMPT = """\
You are an AI writing auditor. Analyze the following sentences for STRUCTURAL AI writing patterns.

Detect ONLY these three patterns:

1. THREE-PART LIST DEFAULT: Using exactly three items as a reflexive structure, not because three is
   genuinely the right number. Example: "This covers speed, reliability, and scalability" when listing
   three as a default rather than because there are genuinely three distinct things.

2. RESTATED CONCLUSION: The closing sentence restates what was already said rather than adding a new
   insight. Example: "In conclusion, we have explored X, Y, and Z and seen their importance."

3. GENERIC CLOSER: Ending with a vague forward-looking statement instead of a specific insight.
   Examples: "The future looks bright", "Only time will tell", "As we move forward",
   "One thing is certain", "The possibilities are endless".

Sentences to analyze (sentence_id → text):
{sentences_json}

Return findings ONLY for sentences that clearly exhibit these patterns.
If no patterns are found, return an empty findings list.
For severity: "high" = clear violation, "medium" = likely violation, "low" = possible.

Return JSON directly — do not wrap in any outer key:
{{"findings": [...]}}
"""


class LLMStructuralAgent:
    """Detects structural AI writing patterns via Ollama."""

    def __init__(self, model: str) -> None:
        self.model = model
        self.client = instructor.from_provider(f"ollama/{model}", mode=instructor.Mode.JSON)

    def _call_llm(self, sentences: dict[str, str]) -> list[SubAgentFinding]:
        prompt = _PROMPT.format(sentences_json=json.dumps(sentences, indent=2))
        result = self.client.chat.completions.create(
            model=self.model,
            response_model=_FindingsList,
            messages=[{"role": "user", "content": prompt}],
        )
        return result.findings

    @observe()
    def run(self, sentences: dict[str, str]) -> SubAgentReport:
        findings = self._call_llm(sentences)
        return SubAgentReport(category="structural", findings=findings)
