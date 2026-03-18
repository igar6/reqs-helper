"""
Tests for the CTO Requirements Agent.

These are unit tests that mock the OpenRouter API — no real API key needed.
Run: pytest tests/
"""

from unittest.mock import MagicMock, patch
import pytest

from claude_util.cto_agent import CTOAgent, AgentConfig, create_agent, DEFAULT_MODEL


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def config():
    return AgentConfig(api_key="test-key-123", model=DEFAULT_MODEL)


@pytest.fixture
def agent(config):
    return CTOAgent(config)


def _mock_completion(content: str, tokens: int = 100):
    """Build a mock OpenAI ChatCompletion response."""
    choice = MagicMock()
    choice.message.content = content
    resp = MagicMock()
    resp.choices = [choice]
    resp.usage.total_tokens = tokens
    return resp


# ---------------------------------------------------------------------------
# create_agent()
# ---------------------------------------------------------------------------

def test_create_agent_raises_without_key(monkeypatch):
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    with pytest.raises(EnvironmentError, match="No API key"):
        create_agent()


def test_create_agent_reads_env_key(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "env-key")
    agent = create_agent()
    assert agent.config.api_key == "env-key"


def test_create_agent_explicit_key():
    agent = create_agent(api_key="explicit-key")
    assert agent.config.api_key == "explicit-key"


def test_create_agent_model_override(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "k")
    agent = create_agent(model="google/gemini-2.0-flash-exp:free")
    assert agent.config.model == "google/gemini-2.0-flash-exp:free"


# ---------------------------------------------------------------------------
# CTOAgent.analyze()
# ---------------------------------------------------------------------------

@patch("claude_util.cto_agent.CTOAgent._call")
def test_analyze_empty_requirements_raises(mock_call, agent):
    with pytest.raises(ValueError, match="empty"):
        agent.analyze("   ")


@patch("claude_util.cto_agent.CTOAgent._call")
def test_analyze_short_requirements_uses_clarification(mock_call, agent):
    mock_call.return_value = ("clarification needed", 50)
    result = agent.analyze("build app")
    assert result.mode == "clarification"
    assert len(result.warnings) > 0


@patch("claude_util.cto_agent.CTOAgent._call")
def test_analyze_full_requirements_assessment(mock_call, agent):
    # First call is assessment (returns 'analysis'), second is full output
    mock_call.side_effect = [
        ("analysis", 10),
        ("## EXECUTIVE SUMMARY\nThis is a solid initiative.", 500),
    ]
    requirements = " ".join(["word"] * 30)  # 30 words — above threshold
    result = agent.analyze(requirements)
    assert result.mode == "analysis"
    assert "EXECUTIVE SUMMARY" in result.content


@patch("claude_util.cto_agent.CTOAgent._call")
def test_analyze_triggers_clarification_when_model_says_so(mock_call, agent):
    mock_call.side_effect = [
        ("clarification", 10),
        ("## CRITICAL MISSING PIECES\n1. Scope unclear.", 200),
    ]
    requirements = " ".join(["word"] * 30)
    result = agent.analyze(requirements)
    assert result.mode == "clarification"


@patch("claude_util.cto_agent.CTOAgent._call")
def test_analyze_returns_model_used(mock_call, agent):
    mock_call.side_effect = [("analysis", 5), ("content", 100)]
    result = agent.analyze(" ".join(["word"] * 30))
    assert result.model_used == DEFAULT_MODEL


@patch("claude_util.cto_agent.CTOAgent._call")
def test_analyze_tokens_tracked(mock_call, agent):
    mock_call.side_effect = [("analysis", 5), ("output", 999)]
    result = agent.analyze(" ".join(["word"] * 30))
    assert result.tokens_used == 999


# ---------------------------------------------------------------------------
# CTOAgent.analyze_stream()
# ---------------------------------------------------------------------------

@patch("claude_util.cto_agent.CTOAgent._call")
@patch("claude_util.cto_agent.CTOAgent._call_stream")
def test_analyze_stream_yields_chunks(mock_stream, mock_call, agent):
    mock_call.return_value = ("analysis", 5)
    mock_stream.return_value = iter(["chunk1", " chunk2", " chunk3"])
    requirements = " ".join(["word"] * 30)
    chunks = list(agent.analyze_stream(requirements))
    combined = "".join(chunks)
    assert "chunk1" in combined
    assert "chunk3" in combined


@patch("claude_util.cto_agent.CTOAgent._call_stream")
def test_analyze_stream_short_req_skips_assessment(mock_stream, agent):
    mock_stream.return_value = iter(["clarification output"])
    chunks = list(agent.analyze_stream("too short"))
    combined = "".join(chunks)
    assert "clarification" in combined.lower()
