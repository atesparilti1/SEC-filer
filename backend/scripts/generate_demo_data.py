"""One-off developer script: generates the bundled demo fixtures in app/demo_data/.

Runs the real analysis pipeline (live SEC EDGAR + the configured AI provider)
for a fixed set of well-known tickers and writes the result as JSON. These
fixtures are committed to the repo and seeded into the cache at startup (see
app/services/demo_seed.py) so the app is explorable with zero AI setup.

Usage (from backend/, with the venv active):
    python scripts/generate_demo_data.py [TICKER ...]

With no arguments, regenerates all demo tickers.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.services import ai_analysis, edgar_client, filing_parser, financial_metrics  # noqa: E402

DEMO_DATA_DIR = Path(__file__).resolve().parent.parent / "app" / "demo_data"
DEMO_TICKERS = ["AAPL", "NVDA", "AMD", "MSFT", "META"]


def generate_one(ticker: str) -> None:
    print(f"[{ticker}] resolving ticker...")
    company = edgar_client.resolve_ticker(ticker)
    cik = company["cik"]

    print(f"[{ticker}] listing filings...")
    filings = edgar_client.list_filings(cik, filing_types={"10-K"}, limit=1)
    if not filings:
        print(f"[{ticker}] no 10-K found, skipping")
        return
    filing = filings[0]

    print(f"[{ticker}] fetching {filing['accession_number']}...")
    html = edgar_client.fetch_filing_document(cik, filing["accession_number"], filing["primary_document"])

    print(f"[{ticker}] extracting sections...")
    sections = filing_parser.extract_sections(html, filing["filing_type"])
    filing_text = filing_parser.build_analysis_input(sections)

    print(f"[{ticker}] computing financials...")
    try:
        facts = edgar_client.get_company_facts(cik)
        periods = financial_metrics.compute_annual_financials(facts)
        financial_summary = financial_metrics.format_financial_summary(periods)
    except Exception as exc:  # noqa: BLE001
        print(f"[{ticker}] financials unavailable: {exc}")
        financial_summary = ""

    print(f"[{ticker}] running AI analysis (this can take a while on a local model)...")
    analysis = ai_analysis.analyze_filing(
        company_name=company["title"],
        ticker=ticker.upper(),
        filing_type=filing["filing_type"],
        filing_date=filing["filing_date"],
        filing_text=filing_text,
        financial_summary=financial_summary,
    )

    fixture = {
        "ticker": ticker.upper(),
        "company_name": company["title"],
        "cik": cik,
        "accession_number": filing["accession_number"],
        "filing_type": filing["filing_type"],
        "filing_date": filing["filing_date"],
        "report_date": filing.get("report_date", ""),
        "primary_document": filing.get("primary_document", ""),
        "analysis": json.loads(analysis.model_dump_json()),
    }

    DEMO_DATA_DIR.mkdir(parents=True, exist_ok=True)
    out_path = DEMO_DATA_DIR / f"{ticker.upper()}_{filing['filing_type']}.json"
    out_path.write_text(json.dumps(fixture, indent=2), encoding="utf-8")
    print(f"[{ticker}] wrote {out_path}")


def main() -> None:
    tickers = sys.argv[1:] or DEMO_TICKERS
    for ticker in tickers:
        try:
            generate_one(ticker)
        except Exception as exc:  # noqa: BLE001
            print(f"[{ticker}] FAILED: {exc}")


if __name__ == "__main__":
    main()
