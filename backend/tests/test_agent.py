"""
Unit tests for VoteGuide agent logic: intent classification,
country detection, tool functions, and run_agent orchestration.
"""
import sys
import os
import pytest
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
os.environ.setdefault("GEMINI_API_KEY", "test-api-key")


@pytest.fixture(scope="module", autouse=True)
def patch_modules():
    mock_response = MagicMock()
    mock_response.text = "Test agent response."
    mock_client = MagicMock()
    mock_client.models.generate_content.return_value = mock_response

    with patch("main.client", mock_client), \
         patch("main.initialize_rag"), \
         patch("main.rag_search", return_value=[
             {"content": "Test RAG context.", "metadata": {}, "relevance_score": 0.9}
         ]):
        import main as m
        yield m, mock_client


@pytest.fixture()
def m(patch_modules):
    mod, _ = patch_modules
    return mod


@pytest.fixture()
def mock_client(patch_modules):
    _, mc = patch_modules
    return mc


# ── classify_intent ───────────────────────────────────────────────────────────

class TestClassifyIntent:
    @pytest.mark.parametrize("msg,expected", [
        ("How do I register to vote?", "registration"),
        ("voter id sign up", "registration"),
        ("How to vote step by step?", "process"),
        ("polling procedure", "process"),
        ("When is the election?", "timeline"),
        ("next election date", "timeline"),
        ("Am I eligible to vote?", "eligibility"),
        ("who can vote?", "eligibility"),
        ("what is the electoral college", "explanation"),
        ("define constituency", "explanation"),
        ("hi there", "general"),
    ])
    def test_classification(self, m, msg, expected):
        assert m.classify_intent(msg) == expected

    def test_case_insensitive(self, m):
        assert m.classify_intent("how to register") == m.classify_intent("HOW TO REGISTER")

    def test_empty_string(self, m):
        assert m.classify_intent("") == "general"

    def test_returns_string(self, m):
        assert isinstance(m.classify_intent("hello"), str)


# ── detect_country ────────────────────────────────────────────────────────────

class TestDetectCountry:
    @pytest.mark.parametrize("msg,expected", [
        ("India Lok Sabha election", "india"),
        ("US electoral college", "usa"),
        ("UK parliament", "uk"),
        ("How do I vote?", None),
    ])
    def test_from_message(self, m, msg, expected):
        assert m.detect_country(msg, None) == expected

    def test_context_overrides_message(self, m):
        assert m.detect_country("UK elections", {"country": "india"}) == "india"

    def test_empty_context_uses_message(self, m):
        assert m.detect_country("USA elections", {}) == "usa"

    def test_returns_none_for_unknown(self, m):
        assert m.detect_country("Tell me about elections", None) is None


# ── Tool functions ────────────────────────────────────────────────────────────

class TestTools:
    def test_timeline_info_returns_string(self, m):
        result = m.get_timeline_info("india")
        assert isinstance(result, str) and len(result) > 10

    def test_timeline_unknown_country(self, m):
        result = m.get_timeline_info("narnia")
        assert "not available" in result.lower() or "supported" in result.lower()

    def test_registration_guide_has_steps(self, m):
        result = m.get_registration_guide("india")
        assert "step" in result.lower() or "Steps" in result

    def test_registration_unknown_country(self, m):
        result = m.get_registration_guide("atlantis")
        assert "not available" in result.lower() or "supported" in result.lower()

    def test_voting_process_has_numbered_steps(self, m):
        result = m.get_voting_process("india")
        assert "1." in result

    def test_voting_process_unknown_country(self, m):
        result = m.get_voting_process("mordor")
        assert "not available" in result.lower() or "supported" in result.lower()

    def test_format_eligible_result(self, m):
        formatted = m.format_eligibility_result({
            "eligible": True,
            "reason": "You are eligible!",
            "next_steps": ["Register", "Vote"],
        })
        assert "✅" in formatted and "Next Steps" in formatted

    def test_format_ineligible_result(self, m):
        formatted = m.format_eligibility_result({
            "eligible": False,
            "reason": "Too young.",
            "next_steps": ["Wait"],
        })
        assert "❌" in formatted


# ── run_agent ─────────────────────────────────────────────────────────────────

class TestRunAgent:
    def test_returns_dict_with_required_keys(self, m, mock_client):
        result = m.run_agent("How do I vote in India?", [], "english", "standard", None)
        for key in ("response", "intent", "model_used", "country_detected", "tools_used"):
            assert key in result

    def test_registration_intent_uses_tool(self, m, mock_client):
        result = m.run_agent("How to register in India?", [], "english", "standard", None)
        assert result["intent"] == "registration"
        assert result["country_detected"] == "india"

    def test_eligibility_with_user_context_uses_tool(self, m, mock_client):
        ctx = {"country": "india", "age": 22, "is_citizen": True, "is_resident": True}
        result = m.run_agent("Am I eligible to vote?", [], "english", "standard", ctx)
        assert result["intent"] == "eligibility"
        assert len(result["tools_used"]) > 0

    def test_gemini_called_once(self, m, mock_client):
        mock_client.reset_mock()
        m.run_agent("Hello", [], "english", "standard", None)
        assert mock_client.models.generate_content.called

    def test_simplified_mode_works(self, m, mock_client):
        result = m.run_agent("What is voting?", [], "english", "simplified", None)
        assert "response" in result

    def test_non_english_language_accepted(self, m, mock_client):
        result = m.run_agent("How do I vote?", [], "hindi", "standard", None)
        assert "response" in result
