from typing import Literal

from langfuse import observe
from pydantic import BaseModel


class FlaggedSentence(BaseModel):
    sentence_id: str
    text: str
    # Keys must be exactly: lexical, structural, tonal, rhythmic
    labels: dict[str, list[str]]
    tier: int  # 1 | 2 | 3
    severity: Literal["low", "medium", "high"]
    is_flagged: bool
    suggested_fix: str


class AuditReport(BaseModel):
    article_id: str
    model: str
    verdict: Literal["patch", "structural_rewrite_needed"]
    flag_count: int
    category_count: int
    tier_1_hits: list[str]
    tier_2_clusters: list[list[str]]
    flagged_sentences: list[FlaggedSentence]


class AuditorAgent:
    """Agent 1 — detects AI writing tells and returns a structured AuditReport."""

    def __init__(self, model: str) -> None:
        self.model = model

    @observe()
    def run(self, text: str, article_id: str) -> AuditReport:
        """Analyze text for AI tells. Returns structured audit report.

        Args:
            text: Full article text.
            article_id: Unique identifier for this article (used in sentence IDs).

        Returns:
            AuditReport with all flagged sentences and verdict.
        """
        raise NotImplementedError
