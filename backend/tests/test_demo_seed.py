import json

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.services import cache, demo_seed


@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


FIXTURE = {
    "ticker": "DEMO",
    "company_name": "Demo Corp",
    "cik": "0000000001",
    "accession_number": "0000000001-25-000001",
    "filing_type": "10-K",
    "filing_date": "2025-01-01",
    "report_date": "2024-12-31",
    "primary_document": "demo.htm",
    "analysis": {
        "executive_summary": "A demo filing.",
        "key_risks": [],
        "growth_opportunities": [],
        "financial_insights": [],
        "management_priorities": [],
        "red_flags": [],
        "positive_signals": [],
    },
}


def test_seed_demo_data_loads_fixtures(db_session, tmp_path, monkeypatch):
    fixture_path = tmp_path / "DEMO_10-K.json"
    fixture_path.write_text(json.dumps(FIXTURE), encoding="utf-8")
    monkeypatch.setattr(demo_seed, "DEMO_DATA_DIR", tmp_path)

    seeded = demo_seed.seed_demo_data(db_session)

    assert seeded == 1
    record = cache.get_cached_analysis(db_session, "DEMO", "0000000001-25-000001", "10-K")
    assert record is not None
    assert record.is_demo is True
    assert record.company_name == "Demo Corp"


def test_seed_demo_data_is_idempotent(db_session, tmp_path, monkeypatch):
    fixture_path = tmp_path / "DEMO_10-K.json"
    fixture_path.write_text(json.dumps(FIXTURE), encoding="utf-8")
    monkeypatch.setattr(demo_seed, "DEMO_DATA_DIR", tmp_path)

    first = demo_seed.seed_demo_data(db_session)
    second = demo_seed.seed_demo_data(db_session)

    assert first == 1
    assert second == 0


def test_seed_demo_data_refreshes_regenerated_fixture(db_session, tmp_path, monkeypatch):
    fixture_path = tmp_path / "DEMO_10-K.json"
    fixture_path.write_text(json.dumps(FIXTURE), encoding="utf-8")
    monkeypatch.setattr(demo_seed, "DEMO_DATA_DIR", tmp_path)
    demo_seed.seed_demo_data(db_session)

    updated = json.loads(json.dumps(FIXTURE))
    updated["analysis"]["executive_summary"] = "A regenerated demo filing."
    fixture_path.write_text(json.dumps(updated), encoding="utf-8")

    assert demo_seed.seed_demo_data(db_session) == 1
    record = cache.get_cached_analysis(db_session, "DEMO", "0000000001-25-000001", "10-K")
    assert "A regenerated demo filing." in record.analysis_json


def test_seed_demo_data_never_overwrites_live_analysis(db_session, tmp_path, monkeypatch):
    from app.schemas import FilingAnalysis

    live = json.loads(json.dumps(FIXTURE["analysis"]))
    live["executive_summary"] = "Analyzed live by the user."
    cache.save_analysis(
        db_session,
        ticker="DEMO",
        company_name="Demo Corp",
        cik="0000000001",
        accession_number="0000000001-25-000001",
        filing_type="10-K",
        filing_date="2025-01-01",
        report_date="2024-12-31",
        primary_document="demo.htm",
        analysis=FilingAnalysis.model_validate(live),
        is_demo=False,
    )
    fixture_path = tmp_path / "DEMO_10-K.json"
    fixture_path.write_text(json.dumps(FIXTURE), encoding="utf-8")
    monkeypatch.setattr(demo_seed, "DEMO_DATA_DIR", tmp_path)

    assert demo_seed.seed_demo_data(db_session) == 0
    record = cache.get_cached_analysis(db_session, "DEMO", "0000000001-25-000001", "10-K")
    assert "Analyzed live by the user." in record.analysis_json


def test_seed_demo_data_missing_dir_returns_zero(db_session, tmp_path, monkeypatch):
    monkeypatch.setattr(demo_seed, "DEMO_DATA_DIR", tmp_path / "does-not-exist")

    assert demo_seed.seed_demo_data(db_session) == 0
