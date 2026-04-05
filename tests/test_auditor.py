from src.agents.auditor import AuditorAgent


def test_preprocess_assigns_stable_sentence_ids():
    agent = AuditorAgent(model="mistral")
    text = "First sentence. Second sentence. Third sentence."
    sentences, paragraphs = agent._preprocess(text, "art_001")
    assert "art_001_s000" in sentences
    assert "art_001_s001" in sentences
    assert "art_001_s002" in sentences
    assert sentences["art_001_s000"] == "First sentence."


def test_preprocess_groups_sentences_by_paragraph():
    agent = AuditorAgent(model="mistral")
    text = "Para one sentence one. Para one sentence two.\n\nPara two sentence one."
    sentences, paragraphs = agent._preprocess(text, "art_001")
    assert len(paragraphs) == 2
    assert len(paragraphs[0]) == 2
    assert len(paragraphs[1]) == 1


def test_preprocess_handles_single_sentence():
    agent = AuditorAgent(model="mistral")
    text = "Just one sentence."
    sentences, paragraphs = agent._preprocess(text, "art_001")
    assert len(sentences) == 1
    assert len(paragraphs) == 1
    assert paragraphs[0] == ["art_001_s000"]


def test_preprocess_ids_are_globally_sequential_across_paragraphs():
    agent = AuditorAgent(model="mistral")
    text = "First.\n\nSecond. Third."
    sentences, paragraphs = agent._preprocess(text, "art_001")
    # Para 1: s000; Para 2: s001, s002 — IDs do not reset per paragraph
    assert "art_001_s000" in paragraphs[0]
    assert "art_001_s001" in paragraphs[1]
    assert "art_001_s002" in paragraphs[1]


from unittest.mock import patch
from src.agents.auditor import (
    AuditorAgent,
    AuditReport,
    FlaggedSentence,
    LexicalSummary,
    LexicalWordReport,
    SentenceHit,
    SubAgentFinding,
    SubAgentReport,
)


def _empty_lexical_report() -> LexicalWordReport:
    return LexicalWordReport(
        lexical_summary=LexicalSummary(tier_1_hits=[], tier_2_clusters=[], tier_3_density=0.0),
        sentence_hits=[],
    )


def _empty_sub_report(category: str) -> SubAgentReport:
    return SubAgentReport(category=category, findings=[])  # type: ignore[arg-type]


def test_auditor_run_returns_audit_report():
    agent = AuditorAgent(model="mistral")
    with patch.object(agent._lexical_detector, "run", return_value=_empty_lexical_report()), \
         patch.object(agent._llm_lexical, "run", return_value=_empty_sub_report("lexical")), \
         patch.object(agent._llm_structural, "run", return_value=_empty_sub_report("structural")), \
         patch.object(agent._llm_tonal, "run", return_value=_empty_sub_report("tonal")), \
         patch.object(agent._llm_rhythmic, "run", return_value=_empty_sub_report("rhythmic")):
        result = agent.run("Clean article text.", "art_001")
    assert isinstance(result, AuditReport)
    assert result.article_id == "art_001"
    assert result.model == "mistral"
    assert result.flag_count == 0
    assert result.verdict == "patch"


def test_auditor_merges_lexical_hit_into_flagged_sentence():
    agent = AuditorAgent(model="mistral")
    lexical_report = LexicalWordReport(
        lexical_summary=LexicalSummary(tier_1_hits=["delve"], tier_2_clusters=[], tier_3_density=0.0),
        sentence_hits=[SentenceHit(sentence_id="art_001_s000", text="We should delve into this.", matched_words=["delve"], tier=1)],
    )
    with patch.object(agent._lexical_detector, "run", return_value=lexical_report), \
         patch.object(agent._llm_lexical, "run", return_value=_empty_sub_report("lexical")), \
         patch.object(agent._llm_structural, "run", return_value=_empty_sub_report("structural")), \
         patch.object(agent._llm_tonal, "run", return_value=_empty_sub_report("tonal")), \
         patch.object(agent._llm_rhythmic, "run", return_value=_empty_sub_report("rhythmic")):
        result = agent.run("We should delve into this.", "art_001")
    assert result.flag_count == 1
    assert result.flagged_sentences[0].sentence_id == "art_001_s000"
    assert "delve" in result.flagged_sentences[0].labels["lexical"]
    assert result.flagged_sentences[0].severity == "high"


def test_auditor_merges_llm_finding_into_flagged_sentence():
    agent = AuditorAgent(model="mistral")
    llm_finding = SubAgentFinding(
        sentence_id="art_001_s000",
        text="In conclusion, we explored speed, reliability, and scalability.",
        patterns_found=["restated conclusion"],
        severity="high",
        suggested_fix="Replace with a specific closing insight.",
    )
    structural_report = SubAgentReport(category="structural", findings=[llm_finding])
    with patch.object(agent._lexical_detector, "run", return_value=_empty_lexical_report()), \
         patch.object(agent._llm_lexical, "run", return_value=_empty_sub_report("lexical")), \
         patch.object(agent._llm_structural, "run", return_value=structural_report), \
         patch.object(agent._llm_tonal, "run", return_value=_empty_sub_report("tonal")), \
         patch.object(agent._llm_rhythmic, "run", return_value=_empty_sub_report("rhythmic")):
        result = agent.run("In conclusion, we explored speed, reliability, and scalability.", "art_001")
    assert result.flag_count == 1
    assert "restated conclusion" in result.flagged_sentences[0].labels["structural"]
    assert result.flagged_sentences[0].suggested_fixes["structural"] == "Replace with a specific closing insight."


def test_verdict_patch_when_below_thresholds():
    agent = AuditorAgent(model="mistral")
    verdict = agent._compute_verdict(
        lexical_summary=LexicalSummary(tier_1_hits=["delve", "leverage"], tier_2_clusters=[], tier_3_density=0.0),
        sub_reports={
            "rhythmic": _empty_sub_report("rhythmic"),
            "structural": _empty_sub_report("structural"),
        },
        flagged_sentences=[],
        category_count=1,
    )
    assert verdict == "patch"


def test_verdict_structural_rewrite_when_all_conditions_met():
    agent = AuditorAgent(model="mistral")
    rhythmic_report = SubAgentReport(
        category="rhythmic",
        findings=[SubAgentFinding(
            sentence_id="art_001_s000",
            text="This sentence demonstrates mechanical padding in order to fill space.",
            patterns_found=["mechanical padding"],
            severity="medium",
            suggested_fix="Cut 'in order to' — write 'to fill space'.",
        )],
    )
    verdict = agent._compute_verdict(
        lexical_summary=LexicalSummary(
            tier_1_hits=["delve", "leverage", "utilize", "commence", "facilitate"],
            tier_2_clusters=[["nuanced", "robust"]],
            tier_3_density=0.04,
        ),
        sub_reports={
            "rhythmic": rhythmic_report,
            "structural": _empty_sub_report("structural"),
        },
        flagged_sentences=[],
        category_count=3,
    )
    assert verdict == "structural_rewrite_needed"
