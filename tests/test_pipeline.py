from unittest.mock import call, patch

from src.schemas.audit import AuditReport
from src.schemas.lexical import LexicalSummary
from src.schemas.rewrite import RewriteReport


def _empty_audit(article_id: str) -> AuditReport:
    return AuditReport(
        article_id=article_id,
        model="mistral",
        verdict="patch",
        flag_count=0,
        category_count=0,
        lexical_summary=LexicalSummary(tier_1_hits=[], tier_2_clusters=[], tier_3_density=0.0),
        sub_reports={},
        flagged_sentences=[],
    )


def _empty_rewrite(article_id: str) -> RewriteReport:
    return RewriteReport(
        article_id=article_id,
        model="mistral",
        rewrites=[],
        full_rewritten_text="Rewritten article text.",
    )


def test_run_detect_only_returns_pipeline_result():
    from src.pipeline import PipelineResult, run_detect_only

    text = "Clean article text."
    mock_audit = _empty_audit("placeholder")

    with patch("src.pipeline.AuditorAgent") as MockAuditor:
        mock_instance = MockAuditor.return_value
        mock_instance.run.return_value = mock_audit

        result = run_detect_only(text=text, model="mistral")

    assert isinstance(result, PipelineResult)
    assert result.pass1 is mock_audit
    assert result.rewrite is None
    assert result.pass2 is None
    assert isinstance(result.article_id, str)
    assert len(result.article_id) == 8


def test_run_detect_only_calls_auditor_once():
    from src.pipeline import run_detect_only

    text = "Clean article text."
    mock_audit = _empty_audit("placeholder")

    with patch("src.pipeline.AuditorAgent") as MockAuditor:
        mock_instance = MockAuditor.return_value
        mock_instance.run.return_value = mock_audit

        result = run_detect_only(text=text, model="mistral")

    MockAuditor.assert_called_once_with(model="mistral")
    mock_instance.run.assert_called_once_with(text=text, article_id=result.article_id)


def test_run_full_pipeline_returns_all_fields_populated():
    from src.pipeline import PipelineResult, run_full_pipeline

    text = "Clean article text."
    mock_pass1 = _empty_audit("placeholder")
    mock_rewrite = _empty_rewrite("placeholder")
    mock_pass2 = _empty_audit("placeholder")

    with patch("src.pipeline.AuditorAgent") as MockAuditor, \
         patch("src.pipeline.RewriterAgent") as MockRewriter:

        mock_auditor_instance = MockAuditor.return_value
        mock_auditor_instance.run.side_effect = [mock_pass1, mock_pass2]

        mock_rewriter_instance = MockRewriter.return_value
        mock_rewriter_instance.run.return_value = mock_rewrite

        result = run_full_pipeline(text=text, model="mistral")

    assert isinstance(result, PipelineResult)
    assert result.pass1 is mock_pass1
    assert result.rewrite is mock_rewrite
    assert result.pass2 is mock_pass2
    assert isinstance(result.article_id, str)
    assert len(result.article_id) == 8


def test_run_full_pipeline_calls_auditor_twice_rewriter_once():
    from src.pipeline import run_full_pipeline

    text = "Clean article text."
    mock_pass1 = _empty_audit("placeholder")
    mock_rewrite = _empty_rewrite("placeholder")
    mock_pass2 = _empty_audit("placeholder")

    with patch("src.pipeline.AuditorAgent") as MockAuditor, \
         patch("src.pipeline.RewriterAgent") as MockRewriter:

        mock_auditor_instance = MockAuditor.return_value
        mock_auditor_instance.run.side_effect = [mock_pass1, mock_pass2]

        mock_rewriter_instance = MockRewriter.return_value
        mock_rewriter_instance.run.return_value = mock_rewrite

        result = run_full_pipeline(text=text, model="mistral")

    MockAuditor.assert_called_once_with(model="mistral")
    MockRewriter.assert_called_once_with(model="mistral")
    calls = mock_auditor_instance.run.call_args_list
    assert calls[0] == call(text=text, article_id=result.article_id)
    assert calls[1] == call(text=mock_rewrite.full_rewritten_text, article_id=f"{result.article_id}_pass2")
    mock_rewriter_instance.run.assert_called_once_with(
        flagged_sentences=mock_pass1.flagged_sentences,
        article_id=result.article_id,
        original_text=text,
    )
