"""Caching layer so the same filing is never re-analyzed by the AI model twice."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import AnalyzedFiling
from app.schemas import FilingAnalysis


def get_cached_analysis(
    db: Session, ticker: str, accession_number: str, filing_type: str
) -> AnalyzedFiling | None:
    stmt = select(AnalyzedFiling).where(
        AnalyzedFiling.ticker == ticker.upper(),
        AnalyzedFiling.accession_number == accession_number,
        AnalyzedFiling.filing_type == filing_type,
    )
    return db.execute(stmt).scalar_one_or_none()


def get_by_id(db: Session, analysis_id: int) -> AnalyzedFiling | None:
    return db.get(AnalyzedFiling, analysis_id)


def save_analysis(
    db: Session,
    *,
    ticker: str,
    company_name: str,
    cik: str,
    accession_number: str,
    filing_type: str,
    filing_date: str,
    report_date: str,
    primary_document: str,
    analysis: FilingAnalysis,
    is_demo: bool = False,
) -> AnalyzedFiling:
    record = AnalyzedFiling(
        ticker=ticker.upper(),
        company_name=company_name,
        cik=cik,
        accession_number=accession_number,
        filing_type=filing_type,
        filing_date=filing_date,
        report_date=report_date,
        primary_document=primary_document,
        analysis_json=analysis.model_dump_json(),
        is_demo=is_demo,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record
