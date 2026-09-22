from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import CompareRequest, CompareResponse
from app.services import ai_analysis, analyze_pipeline
from app.services.financial_metrics import format_financial_summary

router = APIRouter(prefix="/api", tags=["compare"])


@router.post("/compare", response_model=CompareResponse)
def compare(request: CompareRequest, db: Session = Depends(get_db)) -> CompareResponse:
    filing_a = analyze_pipeline.analyze_filing(db, request.ticker_a, request.accession_number_a, None)
    filing_b = analyze_pipeline.analyze_filing(db, request.ticker_b, request.accession_number_b, None)

    financial_summary = ""
    if filing_b.financials:
        financial_summary = format_financial_summary(filing_b.financials.periods)

    comparison = ai_analysis.compare_filings(
        company_name=filing_a.company_name,
        label_a=f"{filing_a.filing_type} filed {filing_a.filing_date}",
        analysis_a=filing_a.analysis,
        label_b=f"{filing_b.filing_type} filed {filing_b.filing_date}",
        analysis_b=filing_b.analysis,
        financial_summary=financial_summary,
    )

    return CompareResponse(filing_a=filing_a, filing_b=filing_b, comparison=comparison)
