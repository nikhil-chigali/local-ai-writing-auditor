from typing import Literal

from pydantic import BaseModel

from .lexical import LexicalSummary


class SubAgentFinding(BaseModel):
    sentence_id: str
    text: str
    patterns_found: list[str]
    severity: Literal["low", "medium", "high"]
    suggested_fix: str


class SubAgentReport(BaseModel):
    category: Literal["lexical", "structural", "tonal", "rhythmic"]
    findings: list[SubAgentFinding]


class FlaggedSentence(BaseModel):
    sentence_id: str
    text: str
    labels: dict[str, list[str]]     # {category: [pattern names]}
    suggested_fixes: dict[str, str]  # {category: suggested fix}
    severity: Literal["low", "medium", "high"]
    is_flagged: bool


class AuditReport(BaseModel):
    article_id: str
    model: str
    verdict: Literal["patch", "structural_rewrite_needed"]
    flag_count: int
    category_count: int
    lexical_summary: LexicalSummary
    sub_reports: dict[str, SubAgentReport]
    flagged_sentences: list[FlaggedSentence]
