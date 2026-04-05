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
        from src.detectors.lexical import PythonLexicalDetector
        from src.detectors.llm_lexical import LLMLexicalAgent
        from src.detectors.llm_rhythmic import LLMRhythmicAgent
        from src.detectors.llm_structural import LLMStructuralAgent
        from src.detectors.llm_tonal import LLMTonalAgent

        self.model = model
        self._lexical_detector = PythonLexicalDetector()
        self._llm_lexical = LLMLexicalAgent(model=model)
        self._llm_structural = LLMStructuralAgent(model=model)
        self._llm_tonal = LLMTonalAgent(model=model)
        self._llm_rhythmic = LLMRhythmicAgent(model=model)

    def _preprocess(
        self, text: str, article_id: str
    ) -> tuple[dict[str, str], list[list[str]]]:
        """Split article into sentences with stable IDs, grouped by paragraph."""
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

    def _merge(
        self,
        lexical_report: LexicalWordReport,
        sub_reports: dict[str, SubAgentReport],
    ) -> list[FlaggedSentence]:
        SEVERITY_RANK = {"low": 0, "medium": 1, "high": 2}
        all_findings: dict[str, dict] = {}

        # Collect lexical word hits
        for hit in lexical_report.sentence_hits:
            sid = hit.sentence_id
            if sid not in all_findings:
                all_findings[sid] = {
                    "text": hit.text,
                    "labels": {"lexical": [], "structural": [], "tonal": [], "rhythmic": []},
                    "suggested_fixes": {},
                    "severity": "low",
                }
            all_findings[sid]["labels"]["lexical"].extend(hit.matched_words)
            tier_severity = "high" if hit.tier == 1 else "medium"
            if SEVERITY_RANK[tier_severity] > SEVERITY_RANK[all_findings[sid]["severity"]]:
                all_findings[sid]["severity"] = tier_severity

        # Collect LLM sub-agent findings
        for category, report in sub_reports.items():
            for finding in report.findings:
                sid = finding.sentence_id
                if sid not in all_findings:
                    all_findings[sid] = {
                        "text": finding.text,
                        "labels": {"lexical": [], "structural": [], "tonal": [], "rhythmic": []},
                        "suggested_fixes": {},
                        "severity": "low",
                    }
                all_findings[sid]["labels"][category].extend(finding.patterns_found)
                all_findings[sid]["suggested_fixes"][category] = finding.suggested_fix
                if SEVERITY_RANK[finding.severity] > SEVERITY_RANK[all_findings[sid]["severity"]]:
                    all_findings[sid]["severity"] = finding.severity

        return [
            FlaggedSentence(
                sentence_id=sid,
                text=data["text"],
                labels=data["labels"],
                suggested_fixes=data["suggested_fixes"],
                severity=data["severity"],
                is_flagged=True,
            )
            for sid, data in all_findings.items()
        ]

    def _compute_verdict(
        self,
        lexical_summary: LexicalSummary,
        sub_reports: dict[str, SubAgentReport],
        flagged_sentences: list[FlaggedSentence],
        category_count: int,
    ) -> Literal["patch", "structural_rewrite_needed"]:
        from config.settings import settings

        rhythmic_flagged = len(
            sub_reports.get("rhythmic", SubAgentReport(category="rhythmic", findings=[])).findings
        ) > 0
        structural_flagged = len(
            sub_reports.get("structural", SubAgentReport(category="structural", findings=[])).findings
        ) > 0

        if (
            len(lexical_summary.tier_1_hits) >= settings.rewrite_vocab_threshold
            and category_count >= settings.rewrite_category_threshold
            and (rhythmic_flagged or structural_flagged)
        ):
            return "structural_rewrite_needed"
        return "patch"

    @observe()
    def run(self, text: str, article_id: str) -> AuditReport:
        sentences, paragraphs = self._preprocess(text, article_id)

        lexical_report = self._lexical_detector.run(sentences, paragraphs)
        llm_reports: dict[str, SubAgentReport] = {
            "lexical": self._llm_lexical.run(sentences),
            "structural": self._llm_structural.run(sentences),
            "tonal": self._llm_tonal.run(sentences),
            "rhythmic": self._llm_rhythmic.run(sentences),
        }

        flagged_sentences = self._merge(lexical_report, llm_reports)

        triggered_categories = {
            cat
            for fs in flagged_sentences
            for cat, patterns in fs.labels.items()
            if patterns
        }
        category_count = len(triggered_categories)

        verdict = self._compute_verdict(
            lexical_summary=lexical_report.lexical_summary,
            sub_reports=llm_reports,
            flagged_sentences=flagged_sentences,
            category_count=category_count,
        )

        return AuditReport(
            article_id=article_id,
            model=self.model,
            verdict=verdict,
            flag_count=len(flagged_sentences),
            category_count=category_count,
            lexical_summary=lexical_report.lexical_summary,
            sub_reports=llm_reports,
            flagged_sentences=flagged_sentences,
        )
