"""Thin, well-behaved client around the public SEC EDGAR endpoints.

SEC's fair-access policy requires every request to carry a descriptive
User-Agent header (see https://www.sec.gov/os/webmaster-faq#developers).
All requests in this module go through `_client()` so that header is never
forgotten.
"""

from __future__ import annotations

import time
from functools import lru_cache
from typing import Any

import httpx

from app.config import get_settings
from app.services.exceptions import SECUnavailableError, TickerNotFoundError

TICKERS_URL = "https://www.sec.gov/files/company_tickers.json"
SUBMISSIONS_URL = "https://data.sec.gov/submissions/CIK{cik}.json"
COMPANYFACTS_URL = "https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json"
ARCHIVES_BASE = "https://www.sec.gov/Archives/edgar/data"

FILING_TYPES_OF_INTEREST = {"10-K", "10-Q"}

_last_request_at = 0.0
_MIN_REQUEST_INTERVAL = 0.11  # stay comfortably under SEC's 10 req/sec limit


def _client() -> httpx.Client:
    settings = get_settings()
    headers = {
        "User-Agent": settings.sec_user_agent,
        "Accept-Encoding": "gzip, deflate",
    }
    return httpx.Client(headers=headers, timeout=15.0)


def _throttled_get(client: httpx.Client, url: str) -> httpx.Response:
    global _last_request_at
    elapsed = time.monotonic() - _last_request_at
    if elapsed < _MIN_REQUEST_INTERVAL:
        time.sleep(_MIN_REQUEST_INTERVAL - elapsed)
    try:
        response = client.get(url)
    except httpx.RequestError as exc:
        raise SECUnavailableError(f"Could not reach SEC EDGAR: {exc}") from exc
    finally:
        _last_request_at = time.monotonic()
    return response


@lru_cache(maxsize=1)
def _ticker_to_cik_map() -> dict[str, dict[str, Any]]:
    """Downloads and caches SEC's full ticker -> CIK/name lookup table."""
    with _client() as client:
        response = _throttled_get(client, TICKERS_URL)
    if response.status_code != 200:
        raise SECUnavailableError(
            f"SEC EDGAR ticker lookup returned status {response.status_code}"
        )
    raw = response.json()
    return {
        entry["ticker"].upper(): {
            "cik": str(entry["cik_str"]).zfill(10),
            "title": entry["title"],
        }
        for entry in raw.values()
    }


def resolve_ticker(ticker: str) -> dict[str, str]:
    """Returns {"cik": "0000320193", "title": "Apple Inc."} for a ticker."""
    mapping = _ticker_to_cik_map()
    entry = mapping.get(ticker.upper())
    if entry is None:
        raise TickerNotFoundError(f"Ticker '{ticker}' was not found in SEC EDGAR records")
    return entry


def get_company_submissions(cik: str) -> dict[str, Any]:
    """Fetches the full submissions payload (company facts + recent filings)."""
    with _client() as client:
        response = _throttled_get(client, SUBMISSIONS_URL.format(cik=cik))
    if response.status_code == 404:
        raise TickerNotFoundError(f"No SEC submissions found for CIK {cik}")
    if response.status_code != 200:
        raise SECUnavailableError(
            f"SEC EDGAR submissions endpoint returned status {response.status_code}"
        )
    return response.json()


def list_filings(cik: str, filing_types: set[str] | None = None, limit: int = 20) -> list[dict[str, Any]]:
    """Returns recent 10-K / 10-Q filings for a company, newest first."""
    filing_types = filing_types or FILING_TYPES_OF_INTEREST
    submissions = get_company_submissions(cik)
    recent = submissions.get("filings", {}).get("recent", {})

    forms = recent.get("form", [])
    accession_numbers = recent.get("accessionNumber", [])
    filing_dates = recent.get("filingDate", [])
    report_dates = recent.get("reportDate", [])
    primary_documents = recent.get("primaryDocument", [])

    filings: list[dict[str, Any]] = []
    for i, form in enumerate(forms):
        if form not in filing_types:
            continue
        filings.append(
            {
                "accession_number": accession_numbers[i],
                "filing_type": form,
                "filing_date": filing_dates[i],
                "report_date": report_dates[i] if i < len(report_dates) else "",
                "primary_document": primary_documents[i] if i < len(primary_documents) else "",
            }
        )
        if len(filings) >= limit:
            break
    return filings


def build_filing_document_url(cik: str, accession_number: str, primary_document: str) -> str:
    accession_no_dashes = accession_number.replace("-", "")
    cik_no_leading_zeros = str(int(cik))
    return f"{ARCHIVES_BASE}/{cik_no_leading_zeros}/{accession_no_dashes}/{primary_document}"


def fetch_filing_document(cik: str, accession_number: str, primary_document: str) -> str:
    """Downloads the raw HTML/text of a filing's primary document."""
    url = build_filing_document_url(cik, accession_number, primary_document)
    with _client() as client:
        response = _throttled_get(client, url)
    if response.status_code != 200:
        raise SECUnavailableError(f"Failed to download filing document (status {response.status_code})")
    return response.text


def get_company_facts(cik: str) -> dict[str, Any]:
    """Fetches the XBRL company-facts payload used for financial metrics."""
    with _client() as client:
        response = _throttled_get(client, COMPANYFACTS_URL.format(cik=cik))
    if response.status_code == 404:
        raise SECUnavailableError(f"No XBRL company facts available for CIK {cik}")
    if response.status_code != 200:
        raise SECUnavailableError(
            f"SEC EDGAR company facts endpoint returned status {response.status_code}"
        )
    return response.json()
