from config.settings import settings
from src.detectors.lexical import PythonLexicalDetector


def test_tier1_hit_flags_sentence():
    detector = PythonLexicalDetector()
    sentences = {"art_001_s000": "We should delve into this topic."}
    paragraphs = [["art_001_s000"]]
    report = detector.run(sentences, paragraphs)
    assert len(report.sentence_hits) == 1
    assert "delve" in report.sentence_hits[0].matched_words
    assert report.sentence_hits[0].tier == 1
    assert "delve" in report.lexical_summary.tier_1_hits


def test_tier1_clean_sentence_no_hit():
    detector = PythonLexicalDetector()
    sentences = {"art_001_s000": "This is a clean sentence with no AI words."}
    paragraphs = [["art_001_s000"]]
    report = detector.run(sentences, paragraphs)
    assert len(report.sentence_hits) == 0
    assert len(report.lexical_summary.tier_1_hits) == 0


def test_tier2_cluster_flags_when_two_words_in_paragraph():
    # "navigate" and "nuanced" are both in TIER_2
    detector = PythonLexicalDetector()
    sentences = {
        "art_001_s000": "We need to navigate this challenge.",
        "art_001_s001": "The situation is nuanced and complex.",
    }
    paragraphs = [["art_001_s000", "art_001_s001"]]
    report = detector.run(sentences, paragraphs)
    assert len(report.lexical_summary.tier_2_clusters) == 1
    cluster_words = report.lexical_summary.tier_2_clusters[0]
    assert "navigate" in cluster_words
    assert "nuanced" in cluster_words


def test_tier2_no_cluster_for_single_word_in_paragraph():
    detector = PythonLexicalDetector()
    sentences = {"art_001_s000": "We need to navigate this challenge."}
    paragraphs = [["art_001_s000"]]
    report = detector.run(sentences, paragraphs)
    assert len(report.lexical_summary.tier_2_clusters) == 0


def test_tier2_words_in_separate_paragraphs_do_not_cluster():
    detector = PythonLexicalDetector()
    sentences = {
        "art_001_s000": "We need to navigate this challenge.",
        "art_001_s001": "The situation is nuanced.",
    }
    # Words are in different paragraphs — must NOT cluster
    paragraphs = [["art_001_s000"], ["art_001_s001"]]
    report = detector.run(sentences, paragraphs)
    assert len(report.lexical_summary.tier_2_clusters) == 0


def test_tier3_density_is_computed():
    # "furthermore" and "moreover" are TIER_3 words
    detector = PythonLexicalDetector()
    sentences = {
        "art_001_s000": "Furthermore this is true.",
        "art_001_s001": "Moreover we can confirm this.",
    }
    paragraphs = [["art_001_s000"], ["art_001_s001"]]
    report = detector.run(sentences, paragraphs)
    assert report.lexical_summary.tier_3_density > 0


def test_tier3_density_zero_for_clean_text():
    detector = PythonLexicalDetector()
    sentences = {
        "art_001_s000": "The implementation is straightforward.",
        "art_001_s001": "The code is well-structured and easy to follow.",
    }
    paragraphs = [["art_001_s000", "art_001_s001"]]
    report = detector.run(sentences, paragraphs)
    assert report.lexical_summary.tier_3_density == 0.0
