import httpx
import pytest
import respx

from app.services import edgar_client
from app.services.exceptions import SECUnavailableError, TickerNotFoundError

TICKERS_PAYLOAD = {
    "0": {"cik_str": 320193, "ticker": "AAPL", "title": "Apple Inc."},
    "1": {"cik_str": 1045810, "ticker": "NVDA", "title": "NVIDIA CORP"},
}


@respx.mock
def test_resolve_ticker_returns_padded_cik():
    respx.get(edgar_client.TICKERS_URL).mock(
        return_value=httpx.Response(200, json=TICKERS_PAYLOAD)
    )

    result = edgar_client.resolve_ticker("aapl")

    assert result == {"cik": "0000320193", "title": "Apple Inc."}


@respx.mock
def test_resolve_ticker_unknown_raises():
    respx.get(edgar_client.TICKERS_URL).mock(
        return_value=httpx.Response(200, json=TICKERS_PAYLOAD)
    )

    with pytest.raises(TickerNotFoundError):
        edgar_client.resolve_ticker("ZZZZZZ")


@respx.mock
def test_ticker_lookup_service_unavailable():
    respx.get(edgar_client.TICKERS_URL).mock(return_value=httpx.Response(503))

    with pytest.raises(SECUnavailableError):
        edgar_client.resolve_ticker("AAPL")


SUBMISSIONS_PAYLOAD = {
    "filings": {
        "recent": {
            "form": ["10-K", "8-K", "10-Q", "10-Q"],
            "accessionNumber": ["0001-K", "0002-8K", "0003-Q", "0004-Q"],
            "filingDate": ["2025-10-31", "2025-09-01", "2025-08-01", "2025-05-01"],
            "reportDate": ["2025-09-27", "", "2025-06-28", "2025-03-29"],
            "primaryDocument": ["a.htm", "b.htm", "c.htm", "d.htm"],
        }
    }
}


@respx.mock
def test_list_filings_filters_to_10k_10q_only():
    respx.get(edgar_client.SUBMISSIONS_URL.format(cik="0000320193")).mock(
        return_value=httpx.Response(200, json=SUBMISSIONS_PAYLOAD)
    )

    filings = edgar_client.list_filings("0000320193")

    forms = [f["filing_type"] for f in filings]
    assert forms == ["10-K", "10-Q", "10-Q"]
    assert "8-K" not in forms


@respx.mock
def test_list_filings_respects_limit():
    respx.get(edgar_client.SUBMISSIONS_URL.format(cik="0000320193")).mock(
        return_value=httpx.Response(200, json=SUBMISSIONS_PAYLOAD)
    )

    filings = edgar_client.list_filings("0000320193", limit=1)

    assert len(filings) == 1
    assert filings[0]["accession_number"] == "0001-K"


def test_build_filing_document_url_strips_dashes_and_leading_zeros():
    url = edgar_client.build_filing_document_url("0000320193", "0000320193-25-000079", "aapl.htm")

    assert url == (
        "https://www.sec.gov/Archives/edgar/data/320193/000032019325000079/aapl.htm"
    )
