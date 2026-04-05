import re
from typing import Literal

from langfuse import observe
from pydantic import BaseModel


class SentenceHit(BaseModel):
    sentence_id: str
    text: str
    matched_words: list[str]
    tier: int  # 1, 2, or 3


class LexicalSummary(BaseModel):
    tier_1_hits: list[str]            # all tier-1 words found (article-level)
    tier_2_clusters: list[list[str]]  # paragraph-level clusters
    tier_3_density: float             # ratio: tier-3 words / total words


class LexicalWordReport(BaseModel):
    lexical_summary: LexicalSummary
    sentence_hits: list[SentenceHit]


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


class AuditorAgent:
    """Orchestrates the phased auditor sub-pipeline. No direct Ollama calls."""

    def __init__(self, model: str) -> None:
        self.model = model

    def _preprocess(
        self, text: str, article_id: str
    ) -> tuple[dict[str, str], list[list[str]]]:
        """Split article into sentences with stable IDs, grouped by paragraph.

        Returns:
            sentences: {sentence_id: sentence_text}
            paragraphs: [[sentence_id, ...], ...] — one list per paragraph
        """
        raw_paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
        if not raw_paragraphs:
            raw_paragraphs = [text.strip()]

        sentences: dict[str, str] = {}
        paragraphs: list[list[str]] = []
        global_idx = 0

        for para in raw_paragraphs:
            raw_sents = re.split(r"(?<=[.!?])\s+(?=[A-Z])", para.strip())
            raw_sents = [s.strip() for s in raw_sents if s.strip()]

            para_ids: list[str] = []
            for sent in raw_sents:
                sid = f"{article_id}_s{str(global_idx).zfill(3)}"
                sentences[sid] = sent
                para_ids.append(sid)
                global_idx += 1

            if para_ids:
                paragraphs.append(para_ids)

        return sentences, paragraphs

    @observe()
    def run(self, text: str, article_id: str) -> AuditReport:
        raise NotImplementedError
