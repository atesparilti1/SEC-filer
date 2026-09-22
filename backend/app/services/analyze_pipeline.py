"""Orchestrates a full filing analysis: resolve -> fetch -> parse -> AI -> cache.

This is the one place that ties together edgar_client, filing_parser,
financial_metrics, ai_analysis and cache so the API routers stay thin.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.schemas import AnalysisRecord, FilingAnalysis, FinancialsResponse
from app.services import ai_analysis, cache, edgar_client, filing_parser, financial_metrics
from app.services.exceptions import FilingNotFoundError, FinancialDataUnavailableError


def _find_filing_metadata(cik: str, ticker: str, accession_number: str, filing_type: str | None) -> dict:
    filings = edgar_client.list_filings(cik, limit=200)
    for f in filings:
        if f["accession_number"] == accession_number:
            return f
    raise FilingNotFoundError(
        f"Filing {accession_number} was not found among recent 10-K/10-Q filings for {ticker}"
    )


def get_financials(ticker: str) -> FinancialsResponse:
    company = edgar_client.resolve_ticker(ticker)
    facts = edgar_client.get_company_facts(company["cik"])
    periods = financial_metrics.compute_annual_financials(facts)
    return FinancialsResponse(
        ticker=ticker.upper(),
        company_name=company["title"],
        cik=company["cik"],
        periods=periods,
    )


def analyze_filing(db: Session, ticker: str, accession_number: str, filing_type: str | None) -> AnalysisRecord:
    company = edgar_client.resolve_ticker(ticker)
    cik = company["cik"]

    cached = cache.get_cached_analysis(db, ticker, accession_number, filing_type or "")
    financials = _safe_get_financials(ticker)

    if cached and (not filing_type or cached.filing_type == filing_type):
        return _record_from_db(cached, financials, cache_hit=True)

    metadata = _find_filing_metadata(cik, ticker, accession_number, filing_type)
    resolved_filing_type = metadata["filing_type"]

    if not cached:
        cached = cache.get_cached_analysis(db, ticker, accession_number, resolved_filing_type)
        if cached:
            return _record_from_db(cached, financials, cache_hit=True)

    html = edgar_client.fetch_filing_document(cik, accession_number, metadata["primary_document"])
    sections = filing_parser.extract_sections(html, resolved_filing_type)
    filing_text = filing_parser.build_analysis_input(sections)

    financial_summary = financial_metrics.format_financial_summary(financials.periods) if financials else ""

    analysis = ai_analysis.analyze_filing(
        company_name=company["title"],
        ticker=ticker.upper(),
        filing_type=resolved_filing_type,
        filing_date=metadata["filing_date"],
        filing_text=filing_text,
        financial_summary=financial_summary,
    )

    record = cache.save_analysis(
        db,
        ticker=ticker,
        company_name=company["title"],
        cik=cik,
        accession_number=accession_number,
        filing_type=resolved_filing_type,
        filing_date=metadata["filing_date"],
        report_date=metadata.get("report_date", ""),
        primary_document=metadata.get("primary_document", ""),
        analysis=analysis,
    )
    return _record_from_db(record, financials, cache_hit=False)


def get_analysis_by_id(db: Session, analysis_id: int) -> AnalysisRecord | None:
    record = cache.get_by_id(db, analysis_id)
    if record is None:
        return None
    financials = _safe_get_financials(record.ticker)
    return _record_from_db(record, financials, cache_hit=True)


def _safe_get_financials(ticker: str) -> FinancialsResponse | None:
    try:
        return get_financials(ticker)
    except FinancialDataUnavailableError:
        return None


def _record_from_db(db_record, financials: FinancialsResponse | None, cache_hit: bool) -> AnalysisRecord:
    return AnalysisRecord(
        id=db_record.id,
        ticker=db_record.ticker,
        company_name=db_record.company_name,
        cik=db_record.cik,
        accession_number=db_record.accession_number,
        filing_type=db_record.filing_type,
        filing_date=db_record.filing_date,
        report_date=db_record.report_date,
        analysis=FilingAnalysis.model_validate_json(db_record.analysis_json),
        financials=financials,
        cached=cache_hit,
        is_demo=db_record.is_demo,
    )
