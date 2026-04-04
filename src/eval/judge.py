from langfuse import observe

from src.agents.rewriter import RewriteResult


class LLMJudge:
    """LLM-as-judge for rewrite quality. Uses Mistral locally — no external APIs."""

    def __init__(self, model: str = "mistral") -> None:
        self.model = model

    @observe()
    def score(self, result: RewriteResult) -> int:
        """Score a single rewrite on a 1-5 scale.

        Criteria:
            5 — All tells removed; original intent and voice fully preserved.
            4 — Tells removed; minor voice drift.
            3 — Most tells removed; some awkwardness.
            2 — Partial removal; notable voice loss.
            1 — Tells remain or meaning changed.

        Args:
            result: A RewriteResult from RewriterAgent.

        Returns:
            Integer score 1 (poor) to 5 (excellent).
        """
        raise NotImplementedError
