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


def test_import_ui():
    from src.ui.app import main
    assert callable(main)


def test_import_review():
    from review import app
    assert app is not None


def test_import_detectors_lexical():
    from src.detectors.lexical import PythonLexicalDetector
    assert PythonLexicalDetector is not None


def test_import_detectors_llm_lexical():
    from src.detectors.llm_lexical import LLMLexicalAgent
    assert LLMLexicalAgent is not None


def test_import_detectors_llm_structural():
    from src.detectors.llm_structural import LLMStructuralAgent
    assert LLMStructuralAgent is not None


def test_import_detectors_llm_tonal():
    from src.detectors.llm_tonal import LLMTonalAgent
    assert LLMTonalAgent is not None


def test_import_detectors_llm_rhythmic():
    from src.detectors.llm_rhythmic import LLMRhythmicAgent
    assert LLMRhythmicAgent is not None


def test_import_schemas_package():
    from src.schemas import (
        SentenceHit,
        LexicalSummary,
        LexicalWordReport,
        SubAgentFinding,
        SubAgentReport,
        FlaggedSentence,
        AuditReport,
        RewriteResult,
        RewriteReport,
    )
    assert all([
        SentenceHit, LexicalSummary, LexicalWordReport,
        SubAgentFinding, SubAgentReport, FlaggedSentence,
        AuditReport, RewriteResult, RewriteReport,
    ])
