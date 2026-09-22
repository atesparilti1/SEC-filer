"""Generates structured, filing-grounded analysis using an LLM.

Two interchangeable providers are supported, selected via `AI_PROVIDER`:
- "ollama" (default): a local model served by Ollama — free, runs entirely
  on the machine running the backend, no API key required.
- "openai": OpenAI's hosted API — higher quality, but costs money per call.

Either way, the model is instructed to use ONLY the filing text it is given,
to keep factual statements separate from interpretation, and to never invent
financial figures (those are computed separately in financial_metrics.py).
Output is constrained to a strict JSON schema so the response always matches
`FilingAnalysis` / `FilingComparison`, regardless of provider.
"""

from __future__ import annotations

import json

import httpx
from openai import APIError, OpenAI

from app.config import get_settings
from app.schemas import FilingAnalysis, FilingComparison
from app.services.exceptions import AIAnalysisError

OLLAMA_TIMEOUT_SECONDS = 300.0

# Ollama defaults to a 4096-token context window, which truncates the filing
# excerpt this app sends (up to ~3 x 12,000 chars, i.e. several thousand
# tokens). Explicitly request a larger window so the model actually sees the
# whole excerpt instead of silently losing the end of it.
OLLAMA_CONTEXT_TOKENS = 16384

SYSTEM_PROMPT = """You are a meticulous equity research analyst. You analyze SEC \
10-K/10-Q filing excerpts and produce structured, well-reasoned analysis.

Rules you must follow strictly:
- Base every statement ONLY on the filing text provided to you. Do not use \
outside knowledge about the company's financials, recent news, or stock price.
- Never invent, estimate, or restate numeric financial metrics (revenue, \
margins, growth rates). Those are computed separately by the application.
- Clearly separate factual statements (what the filing literally says) from \
your own interpretation. Use the "evidence" fields to point to what the \
filing says, and keep "interpretation"/"observation" fields for your analysis.
- Be concise, specific, and avoid generic boilerplate risk language.
- The executive_summary must be a non-empty 2-4 sentence paragraph. Write it
  last, after you have worked out the risks, opportunities, and insights
  below, so it reflects your full analysis rather than a generic preview.
- Return ONLY the structured JSON specified by the schema."""

# Property order below matches generation order for locally-hosted models
# using grammar-constrained decoding (e.g. Ollama): putting executive_summary
# last means the model has already "worked through" risks/opportunities/
# insights by the time it writes the summary, which noticeably improves
# summary quality/non-emptiness compared to writing it first.
ANALYSIS_JSON_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "key_risks": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "title": {"type": "string"},
                    "description": {"type": "string"},
                    "severity": {"type": "string", "enum": ["High", "Medium", "Low"]},
                    "evidence": {"type": "string"},
                },
                "required": ["title", "description", "severity", "evidence"],
            },
        },
        "growth_opportunities": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "title": {"type": "string"},
                    "description": {"type": "string"},
                    "evidence": {"type": "string"},
                },
                "required": ["title", "description", "evidence"],
            },
        },
        "financial_insights": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "metric": {"type": "string"},
                    "observation": {"type": "string"},
                    "interpretation": {"type": "string"},
                },
                "required": ["metric", "observation", "interpretation"],
            },
        },
        "management_priorities": {"type": "array", "items": {"type": "string"}},
        "red_flags": {"type": "array", "items": {"type": "string"}},
        "positive_signals": {"type": "array", "items": {"type": "string"}},
        "executive_summary": {"type": "string"},
    },
    "required": [
        "key_risks",
        "growth_opportunities",
        "financial_insights",
        "management_priorities",
        "red_flags",
        "positive_signals",
        "executive_summary",
    ],
}


def _risk_delta_schema() -> dict:
    return {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "title": {"type": "string"},
            "description": {"type": "string"},
            "severity": {"type": ["string", "null"], "enum": ["High", "Medium", "Low", None]},
            "evidence": {"type": "string"},
        },
        "required": ["title", "description", "severity", "evidence"],
    }


COMPARISON_JSON_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "new_risks": {"type": "array", "items": _risk_delta_schema()},
        "removed_risks": {"type": "array", "items": _risk_delta_schema()},
        "escalated_risks": {"type": "array", "items": _risk_delta_schema()},
        "management_priority_changes": {"type": "array", "items": {"type": "string"}},
        "growth_strategy_changes": {"type": "array", "items": {"type": "string"}},
        "financial_changes": {"type": "array", "items": {"type": "string"}},
        "summary": {"type": "string"},
    },
    "required": [
        "new_risks",
        "removed_risks",
        "escalated_risks",
        "management_priority_changes",
        "growth_strategy_changes",
        "financial_changes",
        "summary",
    ],
}

COMPARISON_SYSTEM_PROMPT = """You are a meticulous equity research analyst comparing two \
SEC filings from the same company at different points in time. You are given each \
filing's previously-generated structured analysis (risks, opportunities, priorities, etc). \
Identify what changed between the earlier filing (A) and the later filing (B). \
Base your comparison only on the two analyses provided. Return only the structured \
JSON described in the schema."""


def _build_analysis_prompt(
    company_name: str,
    ticker: str,
    filing_type: str,
    filing_date: str,
    filing_text: str,
    financial_summary: str,
) -> str:
    return f"""Company: {company_name} ({ticker})
Filing type: {filing_type}
Filing date: {filing_date}

Computed financial context (already calculated in Python — do not recompute \
or restate these numbers, just use them for interpretation if relevant):
{financial_summary or "No financial data available."}

Filing excerpt (Business, Risk Factors, and MD&A sections):
{filing_text}

Analyze this filing and return the structured JSON described in the schema."""


def _build_comparison_prompt(
    company_name: str,
    label_a: str,
    analysis_a: FilingAnalysis,
    label_b: str,
    analysis_b: FilingAnalysis,
    financial_summary: str,
) -> str:
    return f"""Company: {company_name}

Filing A ({label_a}) analysis:
{analysis_a.model_dump_json(indent=2)}

Filing B ({label_b}) analysis:
{analysis_b.model_dump_json(indent=2)}

Financial context (computed, not AI-generated):
{financial_summary or "No financial data available."}

Compare Filing A to Filing B and return the structured JSON described in the schema."""


def _run_structured_completion(
    *, system_prompt: str, user_prompt: str, schema_name: str, json_schema: dict
) -> dict:
    """Dispatches to the configured AI provider and returns the parsed JSON payload."""
    settings = get_settings()
    if settings.ai_provider == "openai":
        return _call_openai(system_prompt, user_prompt, schema_name, json_schema)
    return _call_ollama(system_prompt, user_prompt, json_schema)


def _call_openai(system_prompt: str, user_prompt: str, schema_name: str, json_schema: dict) -> dict:
    settings = get_settings()
    if not settings.openai_api_key:
        raise AIAnalysisError(
            "AI_PROVIDER is set to 'openai' but OPENAI_API_KEY is not configured on the server"
        )

    client = OpenAI(api_key=settings.openai_api_key)
    try:
        response = client.chat.completions.create(
            model=settings.openai_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            response_format={
                "type": "json_schema",
                "json_schema": {"name": schema_name, "strict": True, "schema": json_schema},
            },
            temperature=0.2,
        )
    except APIError as exc:
        raise AIAnalysisError(f"OpenAI API error: {exc}") from exc

    content = response.choices[0].message.content
    if not content:
        raise AIAnalysisError("OpenAI returned an empty response")

    try:
        return json.loads(content)
    except json.JSONDecodeError as exc:
        raise AIAnalysisError(f"OpenAI response was not valid JSON: {exc}") from exc


def _call_ollama(system_prompt: str, user_prompt: str, json_schema: dict) -> dict:
    settings = get_settings()

    try:
        response = httpx.post(
            f"{settings.ollama_base_url}/api/chat",
            json={
                "model": settings.ollama_model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                "format": json_schema,
                "stream": False,
                "options": {"temperature": 0.2, "num_ctx": OLLAMA_CONTEXT_TOKENS},
            },
            timeout=OLLAMA_TIMEOUT_SECONDS,
        )
    except httpx.ConnectError as exc:
        raise AIAnalysisError(
            f"Could not reach the local Ollama server at {settings.ollama_base_url}. "
            "Is Ollama installed and running? Try: ollama serve"
        ) from exc
    except httpx.TimeoutException as exc:
        raise AIAnalysisError(
            "The local AI model took too long to respond. It may still be loading — try again."
        ) from exc

    if response.status_code == 404:
        raise AIAnalysisError(
            f"Local model '{settings.ollama_model}' is not installed. "
            f"Run: ollama pull {settings.ollama_model}"
        )
    if response.status_code != 200:
        raise AIAnalysisError(f"Ollama returned status {response.status_code}: {response.text[:300]}")

    content = response.json().get("message", {}).get("content")
    if not content:
        raise AIAnalysisError("The local AI model returned an empty response")

    try:
        return json.loads(content)
    except json.JSONDecodeError as exc:
        raise AIAnalysisError(f"Local model response was not valid JSON: {exc}") from exc


def analyze_filing(
    company_name: str,
    ticker: str,
    filing_type: str,
    filing_date: str,
    filing_text: str,
    financial_summary: str = "",
) -> FilingAnalysis:
    if not filing_text.strip():
        raise AIAnalysisError("No filing text was available to analyze")

    payload = _run_structured_completion(
        system_prompt=SYSTEM_PROMPT,
        user_prompt=_build_analysis_prompt(
            company_name, ticker, filing_type, filing_date, filing_text, financial_summary
        ),
        schema_name="filing_analysis",
        json_schema=ANALYSIS_JSON_SCHEMA,
    )

    try:
        return FilingAnalysis.model_validate(payload)
    except ValueError as exc:
        raise AIAnalysisError(f"AI response did not match the expected schema: {exc}") from exc


def compare_filings(
    company_name: str,
    label_a: str,
    analysis_a: FilingAnalysis,
    label_b: str,
    analysis_b: FilingAnalysis,
    financial_summary: str = "",
) -> FilingComparison:
    payload = _run_structured_completion(
        system_prompt=COMPARISON_SYSTEM_PROMPT,
        user_prompt=_build_comparison_prompt(
            company_name, label_a, analysis_a, label_b, analysis_b, financial_summary
        ),
        schema_name="filing_comparison",
        json_schema=COMPARISON_JSON_SCHEMA,
    )

    try:
        return FilingComparison.model_validate(payload)
    except ValueError as exc:
        raise AIAnalysisError(f"AI response did not match the expected schema: {exc}") from exc
