from src.agents.auditor import AuditorAgent


def test_preprocess_assigns_stable_sentence_ids():
    agent = AuditorAgent(model="mistral")
    text = "First sentence. Second sentence. Third sentence."
    sentences, paragraphs = agent._preprocess(text, "art_001")
    assert "art_001_s00" in sentences
    assert "art_001_s01" in sentences
    assert "art_001_s02" in sentences
    assert sentences["art_001_s00"] == "First sentence."


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
    assert paragraphs[0] == ["art_001_s00"]


def test_preprocess_ids_are_globally_sequential_across_paragraphs():
    agent = AuditorAgent(model="mistral")
    text = "First.\n\nSecond. Third."
    sentences, paragraphs = agent._preprocess(text, "art_001")
    # Para 1: s00; Para 2: s01, s02 — IDs do not reset per paragraph
    assert "art_001_s00" in paragraphs[0]
    assert "art_001_s01" in paragraphs[1]
    assert "art_001_s02" in paragraphs[1]
