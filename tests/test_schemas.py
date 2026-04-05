def test_flagged_sentence_schema():
    from src.schemas import FlaggedSentence
    s = FlaggedSentence(
        sentence_id="test_001_s01",
        text="Delve into the nuanced landscape.",
        labels={"lexical": ["delve", "nuanced", "landscape"], "structural": [], "tonal": [], "rhythmic": []},
        severity="high",
        is_flagged=True,
        suggested_fixes={"lexical": "Explore the complex terrain."},
    )
    assert s.severity == "high"
    assert "lexical" in s.suggested_fixes


def test_audit_report_schema():
    from src.schemas import AuditReport, LexicalSummary
    report = AuditReport(
        article_id="test_001",
        model="mistral",
        verdict="patch",
        flag_count=2,
        category_count=1,
        lexical_summary=LexicalSummary(
            tier_1_hits=["delve"],
            tier_2_clusters=[],
            tier_3_density=0.0,
        ),
        sub_reports={},
        flagged_sentences=[],
    )
    assert report.verdict == "patch"
    assert report.lexical_summary.tier_1_hits == ["delve"]


def test_sub_agent_report_schema():
    from src.schemas import SubAgentReport, SubAgentFinding
    report = SubAgentReport(
        category="lexical",
        findings=[
            SubAgentFinding(
                sentence_id="test_001_s01",
                text="Developers, engineers, practitioners all agreed.",
                patterns_found=["synonym rotation"],
                severity="medium",
                suggested_fix="Repeat 'developers' throughout.",
            )
        ],
    )
    assert report.category == "lexical"
    assert len(report.findings) == 1


def test_lexical_word_report_schema():
    from src.schemas import LexicalWordReport, LexicalSummary, SentenceHit
    report = LexicalWordReport(
        lexical_summary=LexicalSummary(
            tier_1_hits=["delve"],
            tier_2_clusters=[["nuanced", "robust"]],
            tier_3_density=0.02,
        ),
        sentence_hits=[
            SentenceHit(
                sentence_id="test_001_s01",
                text="Delve into this.",
                matched_words=["delve"],
                tier=1,
            )
        ],
    )
    assert report.lexical_summary.tier_1_hits == ["delve"]
    assert report.sentence_hits[0].tier == 1


def test_rewrite_result_schema():
    from src.schemas import RewriteResult
    r = RewriteResult(
        sentence_id="test_001_s01",
        original="Delve into the nuanced landscape.",
        rewritten="Explore the complex terrain.",
        change_summary="Replaced 'delve' and 'nuanced landscape'.",
    )
    assert r.sentence_id == "test_001_s01"


def test_rewrite_report_schema():
    from src.schemas import RewriteReport
    report = RewriteReport(
        article_id="test_001",
        model="mistral",
        rewrites=[],
        full_rewritten_text="Clean article text.",
    )
    assert report.model == "mistral"
