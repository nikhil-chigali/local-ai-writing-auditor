import instructor
from langfuse import observe
from loguru import logger
from pydantic import BaseModel

from src.schemas import FlaggedSentence, RewriteReport, RewriteResult

_PROMPT = """\
You are a writing editor. Rewrite the following sentence to remove AI writing tells \
while preserving the author's intent, voice, and meaning.

Original sentence: {sentence}
Tell categories detected: {labels}
Suggested fix hint: {suggested_fix}

Rules:
- Only fix the specific tells identified — do not rewrite unrelated parts
- Preserve the author's voice and approximate sentence length
- Do not add new phrases; replace or remove existing ones
- If the suggested fix is good, use it as a starting point

Return a RewriteResult with:
- sentence_id: {sentence_id}
- original: the original sentence (copy it exactly)
- rewritten: your rewritten version
- change_summary: one plain-language sentence explaining what changed and why
"""


class _RewriteResultWrapper(BaseModel):
    result: RewriteResult


class RewriterAgent:
    """Agent 2 — rewrites flagged sentences individually, preserving author voice."""

    def __init__(self, model: str) -> None:
        self.model = model
        self.client = instructor.from_provider(f"ollama/{model}", mode=instructor.Mode.JSON)

    def _call_llm(self, sentence: FlaggedSentence) -> RewriteResult:
        active_labels = {k: v for k, v in sentence.labels.items() if v}
        suggested_fix = " | ".join(
            f"{cat}: {fix}" for cat, fix in sentence.suggested_fixes.items()
        ) or "none"

        prompt = _PROMPT.format(
            sentence=sentence.text,
            labels=active_labels,
            suggested_fix=suggested_fix,
            sentence_id=sentence.sentence_id,
        )
        wrapper = self.client.chat.completions.create(
            model=self.model,
            response_model=_RewriteResultWrapper,
            messages=[{"role": "user", "content": prompt}],
        )
        return wrapper.result

    @observe()
    def run(
        self,
        flagged_sentences: list[FlaggedSentence],
        article_id: str,
        original_text: str,
    ) -> RewriteReport:
        """Rewrite each flagged sentence. Returns full rewrite report.

        Args:
            flagged_sentences: Sentences flagged by AuditorAgent.
            article_id: Article identifier, carried through to output.
            original_text: Full original article text (used to build full_rewritten_text).

        Returns:
            RewriteReport with per-sentence rewrites and full rewritten article text.
        """
        if not flagged_sentences:
            return RewriteReport(
                article_id=article_id,
                model=self.model,
                rewrites=[],
                full_rewritten_text=original_text,
            )

        rewrites: list[RewriteResult] = []
        for sentence in flagged_sentences:
            rewrite = self._call_llm(sentence)
            rewrites.append(rewrite)

        rewritten_text = original_text
        for rewrite in rewrites:
            rewritten_text = rewritten_text.replace(rewrite.original, rewrite.rewritten, 1)

        for rewrite in rewrites:
            if rewrite.original not in original_text:
                logger.warning(
                    "Rewrite original not found in text — substitution skipped: sentence_id={} original={!r}",
                    rewrite.sentence_id,
                    rewrite.original,
                )

        return RewriteReport(
            article_id=article_id,
            model=self.model,
            rewrites=rewrites,
            full_rewritten_text=rewritten_text,
        )
