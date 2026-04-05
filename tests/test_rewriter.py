from unittest.mock import patch

from src.schemas import FlaggedSentence, RewriteReport, RewriteResult


def _make_flagged(sid: str, text: str) -> FlaggedSentence:
    return FlaggedSentence(
        sentence_id=sid,
        text=text,
        labels={"lexical": ["delve"], "structural": [], "tonal": [], "rhythmic": []},
        severity="high",
        is_flagged=True,
        suggested_fixes={"lexical": "Explore the complex field."},
    )


def test_rewriter_returns_rewrite_report():
    from src.agents.rewriter import RewriterAgent

    agent = RewriterAgent(model="mistral")
    flagged = [_make_flagged("art_001_s000", "Delve into the complex field.")]
    original_text = "Delve into the complex field. It covers many topics."

    mock_result = RewriteResult(
        sentence_id="art_001_s000",
        original="Delve into the complex field.",
        rewritten="Explore the complex field.",
        change_summary="Replaced 'delve' with 'explore'.",
    )

    with patch.object(agent, "_call_llm", return_value=mock_result):
        result = agent.run(flagged, "art_001", original_text)

    assert isinstance(result, RewriteReport)
    assert result.article_id == "art_001"
    assert result.model == "mistral"
    assert len(result.rewrites) == 1
    assert result.rewrites[0].rewritten == "Explore the complex field."
    assert "Explore the complex field." in result.full_rewritten_text
    assert "Delve into the complex field." not in result.full_rewritten_text


def test_rewriter_returns_empty_report_for_no_flags():
    from src.agents.rewriter import RewriterAgent

    agent = RewriterAgent(model="mistral")
    original_text = "The build passed. No issues found."

    result = agent.run([], "art_001", original_text)

    assert isinstance(result, RewriteReport)
    assert result.rewrites == []
    assert result.full_rewritten_text == original_text


def test_rewriter_substitutes_multiple_sentences():
    from src.agents.rewriter import RewriterAgent

    agent = RewriterAgent(model="mistral")
    flagged = [
        _make_flagged("art_001_s000", "Delve into this."),
        _make_flagged("art_001_s001", "Leverage these tools."),
    ]
    original_text = "Delve into this. Leverage these tools. The end."

    mock_results = [
        RewriteResult(
            sentence_id="art_001_s000",
            original="Delve into this.",
            rewritten="Explore this.",
            change_summary="Replaced 'delve'.",
        ),
        RewriteResult(
            sentence_id="art_001_s001",
            original="Leverage these tools.",
            rewritten="Use these tools.",
            change_summary="Replaced 'leverage'.",
        ),
    ]

    with patch.object(agent, "_call_llm", side_effect=mock_results):
        result = agent.run(flagged, "art_001", original_text)

    assert len(result.rewrites) == 2
    assert "Explore this." in result.full_rewritten_text
    assert "Use these tools." in result.full_rewritten_text
    assert "Delve into this." not in result.full_rewritten_text
    assert "Leverage these tools." not in result.full_rewritten_text
