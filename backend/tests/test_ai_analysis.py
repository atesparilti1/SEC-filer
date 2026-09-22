import json
from types import SimpleNamespace

import httpx
import pytest
import respx

from app.config import get_settings
from app.services import ai_analysis
from app.services.exceptions import AIAnalysisError

VALID_ANALYSIS_PAYLOAD = {
    "executive_summary": "Solid quarter with steady growth.",
    "key_risks": [
        {
            "title": "Supply chain concentration",
            "description": "Heavy reliance on a small number of suppliers.",
            "severity": "Medium",
            "evidence": "The Company depends on a limited number of suppliers.",
        }
    ],
    "growth_opportunities": [],
    "financial_insights": [],
    "management_priorities": [],
    "red_flags": [],
    "positive_signals": [],
}


@pytest.fixture(autouse=True)
def _clear_settings_cache():
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.fixture
def ollama_settings(monkeypatch):
    monkeypatch.setenv("AI_PROVIDER", "ollama")
    monkeypatch.setenv("OLLAMA_BASE_URL", "http://localhost:11434")
    monkeypatch.setenv("OLLAMA_MODEL", "llama3.1:8b")
    get_settings.cache_clear()


@respx.mock
def test_analyze_filing_via_ollama_success(ollama_settings):
    respx.post("http://localhost:11434/api/chat").mock(
        return_value=httpx.Response(
            200, json={"message": {"role": "assistant", "content": json.dumps(VALID_ANALYSIS_PAYLOAD)}}
        )
    )

    result = ai_analysis.analyze_filing(
        company_name="Test Corp",
        ticker="TEST",
        filing_type="10-K",
        filing_date="2025-01-01",
        filing_text="Item 1. Business... some real filing text here.",
    )

    assert result.executive_summary == "Solid quarter with steady growth."
    assert result.key_risks[0].severity == "Medium"


@respx.mock
def test_analyze_filing_ollama_connection_refused_raises_clear_error(ollama_settings):
    respx.post("http://localhost:11434/api/chat").mock(side_effect=httpx.ConnectError("refused"))

    with pytest.raises(AIAnalysisError, match="Is Ollama installed and running"):
        ai_analysis.analyze_filing(
            company_name="Test Corp",
            ticker="TEST",
            filing_type="10-K",
            filing_date="2025-01-01",
            filing_text="some filing text",
        )


@respx.mock
def test_analyze_filing_ollama_model_not_found(ollama_settings):
    respx.post("http://localhost:11434/api/chat").mock(return_value=httpx.Response(404))

    with pytest.raises(AIAnalysisError, match="ollama pull"):
        ai_analysis.analyze_filing(
            company_name="Test Corp",
            ticker="TEST",
            filing_type="10-K",
            filing_date="2025-01-01",
            filing_text="some filing text",
        )


@respx.mock
def test_analyze_filing_ollama_invalid_json_raises(ollama_settings):
    respx.post("http://localhost:11434/api/chat").mock(
        return_value=httpx.Response(200, json={"message": {"content": "not valid json"}})
    )

    with pytest.raises(AIAnalysisError):
        ai_analysis.analyze_filing(
            company_name="Test Corp",
            ticker="TEST",
            filing_type="10-K",
            filing_date="2025-01-01",
            filing_text="some filing text",
        )


def test_analyze_filing_rejects_empty_text(ollama_settings):
    with pytest.raises(AIAnalysisError, match="No filing text"):
        ai_analysis.analyze_filing(
            company_name="Test Corp",
            ticker="TEST",
            filing_type="10-K",
            filing_date="2025-01-01",
            filing_text="   ",
        )


def test_analyze_filing_via_openai_success(monkeypatch):
    monkeypatch.setenv("AI_PROVIDER", "openai")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-fake-key")
    get_settings.cache_clear()

    fake_response = SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content=json.dumps(VALID_ANALYSIS_PAYLOAD)))]
    )

    class FakeCompletions:
        def create(self, **kwargs):
            return fake_response

    class FakeChat:
        completions = FakeCompletions()

    class FakeOpenAIClient:
        def __init__(self, api_key):
            self.chat = FakeChat()

    monkeypatch.setattr(ai_analysis, "OpenAI", FakeOpenAIClient)

    result = ai_analysis.analyze_filing(
        company_name="Test Corp",
        ticker="TEST",
        filing_type="10-K",
        filing_date="2025-01-01",
        filing_text="some filing text",
    )

    assert result.executive_summary == "Solid quarter with steady growth."


def test_analyze_filing_openai_missing_key_raises(monkeypatch):
    monkeypatch.setenv("AI_PROVIDER", "openai")
    monkeypatch.setenv("OPENAI_API_KEY", "")
    get_settings.cache_clear()

    with pytest.raises(AIAnalysisError, match="OPENAI_API_KEY"):
        ai_analysis.analyze_filing(
            company_name="Test Corp",
            ticker="TEST",
            filing_type="10-K",
            filing_date="2025-01-01",
            filing_text="some filing text",
        )
