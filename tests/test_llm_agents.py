from unittest.mock import patch
from src.agents.auditor import SubAgentFinding, SubAgentReport


def test_llm_lexical_agent_returns_sub_agent_report():
    from src.detectors.llm_lexical import LLMLexicalAgent
    agent = LLMLexicalAgent(model="mistral")
    mock_findings = [
        SubAgentFinding(
            sentence_id="art_001_s000",
            text="The developers, engineers, practitioners all agreed.",
            patterns_found=["synonym rotation"],
            severity="medium",
            suggested_fix="Repeat 'developers' consistently.",
        )
    ]
    with patch.object(agent, "_call_llm", return_value=mock_findings):
        result = agent.run({"art_001_s000": "The developers, engineers, practitioners all agreed."})
    assert isinstance(result, SubAgentReport)
    assert result.category == "lexical"
    assert len(result.findings) == 1
    assert result.findings[0].patterns_found == ["synonym rotation"]


def test_llm_lexical_agent_returns_empty_for_clean_text():
    from src.detectors.llm_lexical import LLMLexicalAgent
    agent = LLMLexicalAgent(model="mistral")
    with patch.object(agent, "_call_llm", return_value=[]):
        result = agent.run({"art_001_s000": "The team shipped a new feature."})
    assert result.category == "lexical"
    assert result.findings == []


def test_llm_structural_agent_returns_sub_agent_report():
    from src.detectors.llm_structural import LLMStructuralAgent
    agent = LLMStructuralAgent(model="mistral")
    mock_findings = [
        SubAgentFinding(
            sentence_id="art_001_s005",
            text="In conclusion, we have explored speed, reliability, and scalability.",
            patterns_found=["restated conclusion", "three-part list default"],
            severity="high",
            suggested_fix="End with a specific insight instead of a summary.",
        )
    ]
    with patch.object(agent, "_call_llm", return_value=mock_findings):
        result = agent.run({"art_001_s005": "In conclusion, we have explored speed, reliability, and scalability."})
    assert isinstance(result, SubAgentReport)
    assert result.category == "structural"
    assert len(result.findings) == 1


def test_llm_structural_agent_empty_for_clean_text():
    from src.detectors.llm_structural import LLMStructuralAgent
    agent = LLMStructuralAgent(model="mistral")
    with patch.object(agent, "_call_llm", return_value=[]):
        result = agent.run({"art_001_s000": "The deployment went smoothly."})
    assert result.category == "structural"
    assert result.findings == []


def test_llm_tonal_agent_returns_sub_agent_report():
    from src.detectors.llm_tonal import LLMTonalAgent
    agent = LLMTonalAgent(model="mistral")
    mock_findings = [
        SubAgentFinding(
            sentence_id="art_001_s000",
            text="Great question! It could be argued that performance matters.",
            patterns_found=["sycophantic opener", "excessive hedging"],
            severity="high",
            suggested_fix="Remove 'Great question!' and state the claim directly.",
        )
    ]
    with patch.object(agent, "_call_llm", return_value=mock_findings):
        result = agent.run({"art_001_s000": "Great question! It could be argued that performance matters."})
    assert isinstance(result, SubAgentReport)
    assert result.category == "tonal"
    assert len(result.findings) == 1


def test_llm_tonal_agent_empty_for_clean_text():
    from src.detectors.llm_tonal import LLMTonalAgent
    agent = LLMTonalAgent(model="mistral")
    with patch.object(agent, "_call_llm", return_value=[]):
        result = agent.run({"art_001_s000": "The cache hit rate dropped 12% after the deploy."})
    assert result.category == "tonal"
    assert result.findings == []


def test_llm_rhythmic_agent_returns_sub_agent_report():
    from src.detectors.llm_rhythmic import LLMRhythmicAgent
    agent = LLMRhythmicAgent(model="mistral")
    mock_findings = [
        SubAgentFinding(
            sentence_id="art_001_s002",
            text="It is important to note that the system handles this case.",
            patterns_found=["mechanical padding"],
            severity="low",
            suggested_fix="Cut 'It is important to note that' — just state it.",
        )
    ]
    with patch.object(agent, "_call_llm", return_value=mock_findings):
        result = agent.run({"art_001_s002": "It is important to note that the system handles this case."})
    assert isinstance(result, SubAgentReport)
    assert result.category == "rhythmic"
    assert len(result.findings) == 1


def test_llm_rhythmic_agent_empty_for_clean_text():
    from src.detectors.llm_rhythmic import LLMRhythmicAgent
    agent = LLMRhythmicAgent(model="mistral")
    with patch.object(agent, "_call_llm", return_value=[]):
        result = agent.run({"art_001_s000": "The build failed. Nobody knew why. It was three AM."})
    assert result.category == "rhythmic"
    assert result.findings == []
