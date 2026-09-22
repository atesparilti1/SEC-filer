import pytest

from app.services.exceptions import FilingParsingError
from app.services.filing_parser import build_analysis_input, extract_sections


def _padded(text: str, min_len: int = 600) -> str:
    """Pads short section bodies past the TOC-detection gap threshold."""
    filler = " Lorem ipsum dolor sit amet consectetur adipiscing elit." * 20
    return (text + filler)[:max(len(text), min_len)]


def make_10k_html() -> str:
    toc = "<p>Item 1. Business Item 1A. Risk Factors Item 7. Management's Discussion</p>"
    business = "<p>Item 1. Business</p><p>" + _padded("We design and sell widgets globally.") + "</p>"
    risk_factors = "<p>Item 1A. Risk Factors</p><p>" + _padded(
        "Our business faces competitive risk and supply chain risk."
    ) + "</p>"
    mdna = "<p>Item 7. Management's Discussion and Analysis</p><p>" + _padded(
        "Revenue increased due to strong demand in our core markets."
    ) + "</p>"
    closing = "<p>Item 7A. Quantitative Disclosures</p><p>" + _padded("Market risk discussion.") + "</p>"

    return f"<html><body>{toc}{business}{risk_factors}{mdna}{closing}</body></html>"


def test_extract_sections_skips_table_of_contents():
    html = make_10k_html()

    sections = extract_sections(html, "10-K")

    assert "business" in sections
    assert "risk_factors" in sections
    assert "mdna" in sections
    assert "widgets" in sections["business"]
    assert "competitive risk" in sections["risk_factors"]
    assert "Revenue increased" in sections["mdna"]


def test_extract_sections_raises_when_no_headers_found():
    with pytest.raises(FilingParsingError):
        extract_sections("<html><body><p>Nothing relevant here.</p></body></html>", "10-K")


def test_extract_sections_rejects_unsupported_filing_type():
    with pytest.raises(FilingParsingError):
        extract_sections(make_10k_html(), "8-K")


def test_build_analysis_input_labels_each_section():
    sections = {"business": "biz text", "risk_factors": "risk text", "mdna": "mdna text"}

    result = build_analysis_input(sections)

    assert "ITEM 1 - BUSINESS" in result
    assert "ITEM 1A - RISK FACTORS" in result
    assert "MANAGEMENT'S DISCUSSION AND ANALYSIS" in result
    assert "biz text" in result
