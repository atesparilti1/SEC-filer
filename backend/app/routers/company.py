from fastapi import APIRouter

from app.schemas import CompanyFilingsResponse, CompanyInfo, FilingSummary
from app.services import edgar_client

router = APIRouter(prefix="/api/company", tags=["company"])


@router.get("/{ticker}", response_model=CompanyInfo)
def get_company(ticker: str) -> CompanyInfo:
    resolved = edgar_client.resolve_ticker(ticker)
    return CompanyInfo(ticker=ticker.upper(), cik=resolved["cik"], company_name=resolved["title"])


@router.get("/{ticker}/filings", response_model=CompanyFilingsResponse)
def get_company_filings(ticker: str) -> CompanyFilingsResponse:
    resolved = edgar_client.resolve_ticker(ticker)
    cik = resolved["cik"]
    filings = edgar_client.list_filings(cik, limit=20)

    summaries = [
        FilingSummary(
            accession_number=f["accession_number"],
            filing_type=f["filing_type"],
            filing_date=f["filing_date"],
            report_date=f["report_date"],
            primary_document=f["primary_document"],
            primary_doc_url=edgar_client.build_filing_document_url(
                cik, f["accession_number"], f["primary_document"]
            ),
        )
        for f in filings
    ]

    return CompanyFilingsResponse(
        company=CompanyInfo(ticker=ticker.upper(), cik=cik, company_name=resolved["title"]),
        filings=summaries,
    )
