from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class AnalyzedFiling(Base):
    """A cached AI analysis of a single SEC filing.

    Uniquely identified by (ticker, accession_number, filing_type) so the same
    filing is never sent to the AI model twice.
    """

    __tablename__ = "analyzed_filings"
    __table_args__ = (
        UniqueConstraint("ticker", "accession_number", "filing_type", name="uq_filing_identity"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    ticker: Mapped[str] = mapped_column(String(16), index=True)
    company_name: Mapped[str] = mapped_column(String(255))
    cik: Mapped[str] = mapped_column(String(16), index=True)

    accession_number: Mapped[str] = mapped_column(String(32), index=True)
    filing_type: Mapped[str] = mapped_column(String(16))
    filing_date: Mapped[str] = mapped_column(String(16))
    report_date: Mapped[str] = mapped_column(String(16), default="")
    primary_document: Mapped[str] = mapped_column(String(255), default="")

    analysis_json: Mapped[str] = mapped_column(Text)

    # True for filings pre-seeded from app/demo_data/ at startup, so the app
    # is explorable without any AI provider configured.
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
