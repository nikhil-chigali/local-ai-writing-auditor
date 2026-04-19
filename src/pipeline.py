# src/pipeline.py
import hashlib
from dataclasses import dataclass

from src.agents.auditor import AuditorAgent
from src.agents.rewriter import RewriterAgent
from src.schemas.audit import AuditReport
from src.schemas.rewrite import RewriteReport


@dataclass(frozen=True)
class PipelineResult:
    article_id: str
    pass1: AuditReport
    rewrite: RewriteReport | None
    pass2: AuditReport | None


def _article_id(text: str) -> str:
    return hashlib.md5(text.encode()).hexdigest()[:8]


def run_detect_only(text: str, model: str) -> PipelineResult:
    article_id = _article_id(text)
    auditor = AuditorAgent(model=model)
    pass1 = auditor.run(text=text, article_id=article_id)
    return PipelineResult(article_id=article_id, pass1=pass1, rewrite=None, pass2=None)


def run_full_pipeline(text: str, model: str) -> PipelineResult:
    article_id = _article_id(text)
    auditor = AuditorAgent(model=model)
    rewriter = RewriterAgent(model=model)
    pass1 = auditor.run(text=text, article_id=article_id)
    rewrite = rewriter.run(
        flagged_sentences=pass1.flagged_sentences,
        article_id=article_id,
        original_text=text,
    )
    pass2 = auditor.run(
        text=rewrite.full_rewritten_text,
        article_id=f"{article_id}_pass2",
    )
    return PipelineResult(article_id=article_id, pass1=pass1, rewrite=rewrite, pass2=pass2)
