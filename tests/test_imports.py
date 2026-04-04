def test_import_settings():
    from config.settings import settings
    assert settings is not None


def test_import_taxonomy():
    from config.taxonomy import TIER_1, TIER_2, TIER_3, PATTERNS
    assert isinstance(TIER_1, list)
    assert isinstance(TIER_2, list)
    assert isinstance(TIER_3, list)
    assert isinstance(PATTERNS, dict)


def test_import_auditor():
    from src.agents.auditor import AuditorAgent, AuditReport, FlaggedSentence
    assert AuditorAgent is not None


def test_import_rewriter():
    from src.agents.rewriter import RewriterAgent, RewriteResult, RewriteReport
    assert RewriterAgent is not None


def test_import_metrics():
    from src.eval.metrics import compute_metrics
    assert callable(compute_metrics)


def test_import_judge():
    from src.eval.judge import LLMJudge
    assert LLMJudge is not None
