"""One-off developer script: snapshots real API responses for the static online demo.

The GitHub Pages build of the frontend has no backend. For each demo ticker this
calls the real FastAPI app in-process (live SEC EDGAR data, cached demo analyses,
no AI call) and saves the JSON responses under frontend/public/demo-api/, which
the frontend reads when built with VITE_STATIC_DEMO=1.

Usage (from backend/, with the venv active):
    python scripts/export_static_demo.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402

DEMO_DATA_DIR = Path(__file__).resolve().parent.parent / "app" / "demo_data"
OUT_DIR = Path(__file__).resolve().parents[2] / "frontend" / "public" / "demo-api"


def write(rel: str, payload: dict) -> None:
    path = OUT_DIR / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, separators=(",", ":")), encoding="utf-8")


def main() -> None:
    fixtures = [json.loads(p.read_text(encoding="utf-8")) for p in sorted(DEMO_DATA_DIR.glob("*.json"))]
    with TestClient(app) as client:
        for fx in fixtures:
            ticker = fx["ticker"]
            print(f"[{ticker}] snapshotting...")

            def get(path: str) -> dict:
                r = client.get(path)
                r.raise_for_status()
                return r.json()

            write(f"company/{ticker}.json", get(f"/api/company/{ticker}"))

            # Only the pre-analyzed filing is offered online; others need the AI model.
            filings = get(f"/api/company/{ticker}/filings")
            filings["filings"] = [f for f in filings["filings"] if f["accession_number"] == fx["accession_number"]]
            write(f"filings/{ticker}.json", filings)

            write(f"financials/{ticker}.json", get(f"/api/financials/{ticker}"))

            r = client.post(
                "/api/analyze",
                json={"ticker": ticker, "accession_number": fx["accession_number"], "filing_type": fx["filing_type"]},
            )
            r.raise_for_status()
            write(f"analysis/{ticker}-{fx['accession_number']}.json", r.json())

    print(f"Wrote demo snapshots to {OUT_DIR}")


if __name__ == "__main__":
    main()
