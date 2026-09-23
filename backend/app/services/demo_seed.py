"""Seeds pre-generated demo analyses so the app is explorable with zero AI setup.

Fixture JSON files live in app/demo_data/*.json (generated once via
scripts/generate_demo_data.py using the local AI pipeline against real SEC
filings) and are upserted into the cache table at startup, marked
`is_demo=True`. This is idempotent: filings already in the DB are skipped.
"""

from __future__ import annotations

import json
from pathlib import Path

from sqlalchemy.orm import Session

from app.schemas import FilingAnalysis
from app.services import cache

DEMO_DATA_DIR = Path(__file__).resolve().parent.parent / "demo_data"


def seed_demo_data(db: Session) -> int:
    if not DEMO_DATA_DIR.exists():
        return 0

    seeded = 0
    for fixture_path in sorted(DEMO_DATA_DIR.glob("*.json")):
        payload = json.loads(fixture_path.read_text(encoding="utf-8"))

        existing = cache.get_cached_analysis(
            db, payload["ticker"], payload["accession_number"], payload["filing_type"]
        )
        if existing is not None:
            # A regenerated fixture replaces its stale demo row. Analyses the
            # user ran live (is_demo=False) are never touched.
            fresh = FilingAnalysis.model_validate(payload["analysis"]).model_dump_json()
            if existing.is_demo and existing.analysis_json != fresh:
                existing.analysis_json = fresh
                db.commit()
                seeded += 1
            continue

        cache.save_analysis(
            db,
            ticker=payload["ticker"],
            company_name=payload["company_name"],
            cik=payload["cik"],
            accession_number=payload["accession_number"],
            filing_type=payload["filing_type"],
            filing_date=payload["filing_date"],
            report_date=payload.get("report_date", ""),
            primary_document=payload.get("primary_document", ""),
            analysis=FilingAnalysis.model_validate(payload["analysis"]),
            is_demo=True,
        )
        seeded += 1

    return seeded
