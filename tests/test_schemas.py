def test_flagged_sentence_schema():
    from src.agents.auditor import FlaggedSentence
    s = FlaggedSentence(
        sentence_id="test_001_s01",
        text="Delve into the nuanced landscape.",
        labels={"lexical": ["delve", "nuanced", "landscape"], "structural": [], "tonal": [], "rhythmic": []},
        tier=1,
        severity="high",
        is_flagged=True,
        suggested_fix="Explore the complex terrain.",
    )
    assert s.severity == "high"
    assert s.tier == 1


def test_audit_report_schema():
    from src.agents.auditor import AuditReport
    report = AuditReport(
        article_id="test_001",
        model="mistral",
        verdict="patch",
        flag_count=2,
        category_count=1,
        tier_1_hits=["delve"],
        tier_2_clusters=[],
        flagged_sentences=[],
    )
    assert report.verdict == "patch"


def test_rewrite_result_schema():
    from src.agents.rewriter import RewriteResult
    r = RewriteResult(
        sentence_id="test_001_s01",
        original="Delve into the nuanced landscape.",
        rewritten="Explore the complex terrain.",
        change_summary="Replaced 'delve' (tier-1 hit) and 'nuanced landscape' (tier-2 cluster).",
    )
    assert r.sentence_id == "test_001_s01"


def test_rewrite_report_schema():
    from src.agents.rewriter import RewriteReport
    report = RewriteReport(
        article_id="test_001",
        model="mistral",
        rewrites=[],
        full_rewritten_text="Clean article text.",
    )
    assert report.model == "mistral"
