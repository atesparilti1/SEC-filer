import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.schemas import FilingAnalysis
from app.services import cache


@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


def _sample_analysis() -> FilingAnalysis:
    return FilingAnalysis(executive_summary="Solid quarter.")


def test_save_and_retrieve_cached_analysis(db_session):
    cache.save_analysis(
        db_session,
        ticker="aapl",
        company_name="Apple Inc.",
        cik="0000320193",
        accession_number="0000320193-25-000079",
        filing_type="10-K",
        filing_date="2025-10-31",
        report_date="2025-09-27",
        primary_document="aapl.htm",
        analysis=_sample_analysis(),
    )

    found = cache.get_cached_analysis(db_session, "AAPL", "0000320193-25-000079", "10-K")

    assert found is not None
    assert found.company_name == "Apple Inc."
    assert FilingAnalysis.model_validate_json(found.analysis_json).executive_summary == "Solid quarter."


def test_cache_miss_returns_none(db_session):
    found = cache.get_cached_analysis(db_session, "AAPL", "does-not-exist", "10-K")

    assert found is None


def test_get_by_id_roundtrip(db_session):
    saved = cache.save_analysis(
        db_session,
        ticker="MSFT",
        company_name="Microsoft Corp",
        cik="0000789019",
        accession_number="0000789019-25-000001",
        filing_type="10-K",
        filing_date="2025-07-30",
        report_date="2025-06-30",
        primary_document="msft.htm",
        analysis=_sample_analysis(),
    )

    found = cache.get_by_id(db_session, saved.id)

    assert found is not None
    assert found.ticker == "MSFT"
