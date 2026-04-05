from langfuse import observe

from src.schemas import FlaggedSentence, RewriteResult, RewriteReport


class RewriterAgent:
    """Agent 2 — rewrites flagged sentences individually, preserving author voice."""

    def __init__(self, model: str) -> None:
        self.model = model

    @observe()
    def run(self, flagged_sentences: list[FlaggedSentence], article_id: str) -> RewriteReport:
        """Rewrite each flagged sentence. Returns full rewrite report.

        Args:
            flagged_sentences: Sentences flagged by AuditorAgent.
            article_id: Article identifier, carried through to output.

        Returns:
            RewriteReport with per-sentence rewrites and full rewritten article text.
        """
        raise NotImplementedError
