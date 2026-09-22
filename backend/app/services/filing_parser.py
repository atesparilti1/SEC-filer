"""Extracts and cleans the sections of a 10-K / 10-Q that matter for AI analysis.

SEC filings are large (500KB-2MB of HTML) and mostly boilerplate/legal
formatting, so we never send the whole document to the AI model. Instead we:

1. Strip HTML down to plain text.
2. Locate the real "Item N." section headers (as opposed to the identical
   ones listed in the table of contents) using a gap heuristic: a table of
   contents lists items back-to-back with almost no text between them, while
   a real section heading is followed by a substantial body of text.
3. Slice out just the sections we care about (Business, Risk Factors, MD&A).
4. Truncate each section to a character budget to keep token usage bounded.
"""

from __future__ import annotations

import re
import warnings
from dataclasses import dataclass

from bs4 import BeautifulSoup, XMLParsedAsHTMLWarning

from app.services.exceptions import FilingParsingError

warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)

# Minimum characters that must follow a heading before the next heading for
# it to be considered a real section (rather than a table-of-contents entry).
MIN_SECTION_GAP = 500

# Which XBRL-style "Item N" key maps to which logical section, per form type.
SECTION_KEYS_BY_FORM = {
    "10-K": {"business": "1", "risk_factors": "1A", "mdna": "7"},
    "10-Q": {"risk_factors": "1A", "mdna": "2"},
}

# Character budget per section sent to the AI model (keeps token usage sane).
MAX_SECTION_CHARS = 12_000

HEADER_PATTERN = re.compile(
    r"\bItem\s+(\d{1,2}[A-C]?)\.\s*([A-Z][A-Za-z ,&\-']{2,70})",
    re.IGNORECASE,
)


@dataclass
class HeaderMatch:
    key: str
    start: int
    label: str


def _clean_html_to_text(html: str) -> str:
    soup = BeautifulSoup(html, "lxml")
    text = soup.get_text("\n")
    text = text.replace("\xa0", " ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{2,}", "\n", text)
    return text


def _find_real_headers(text: str) -> list[HeaderMatch]:
    raw_matches = [
        HeaderMatch(key=m.group(1).upper(), start=m.start(), label=m.group(2).strip())
        for m in HEADER_PATTERN.finditer(text)
    ]
    if not raw_matches:
        return []

    real: list[HeaderMatch] = []
    for i, match in enumerate(raw_matches):
        next_start = raw_matches[i + 1].start if i + 1 < len(raw_matches) else len(text)
        if (next_start - match.start) >= MIN_SECTION_GAP:
            real.append(match)
    return real


def _slice_sections(text: str, headers: list[HeaderMatch], keys: dict[str, str]) -> dict[str, str]:
    # Last occurrence of each key wins: real TOC-like duplicates were already
    # filtered out, so a remaining duplicate is almost always the actual
    # heading appearing later than a short, filtered-out earlier reference.
    last_by_key: dict[str, HeaderMatch] = {}
    for h in headers:
        last_by_key[h.key] = h

    ordered = sorted(last_by_key.values(), key=lambda h: h.start)
    positions = [h.start for h in ordered]

    sections: dict[str, str] = {}
    for section_name, item_key in keys.items():
        header = last_by_key.get(item_key)
        if header is None:
            continue
        idx = positions.index(header.start)
        end = positions[idx + 1] if idx + 1 < len(positions) else len(text)
        body = text[header.start:end].strip()
        sections[section_name] = body[:MAX_SECTION_CHARS]

    return sections


def extract_sections(html: str, filing_type: str) -> dict[str, str]:
    """Returns a dict of {business, risk_factors, mdna} -> cleaned text.

    Missing sections are simply omitted rather than raising, so callers can
    still analyze whatever was found.
    """
    keys = SECTION_KEYS_BY_FORM.get(filing_type.upper())
    if keys is None:
        raise FilingParsingError(f"Unsupported filing type for section extraction: {filing_type}")

    try:
        text = _clean_html_to_text(html)
    except Exception as exc:  # noqa: BLE001 - surfaced as a domain error
        raise FilingParsingError(f"Failed to parse filing HTML: {exc}") from exc

    headers = _find_real_headers(text)
    if not headers:
        raise FilingParsingError("Could not locate any 'Item N.' section headers in the filing")

    sections = _slice_sections(text, headers, keys)
    if not sections:
        raise FilingParsingError("Filing was parsed but none of the expected sections were found")

    return sections


def build_analysis_input(sections: dict[str, str]) -> str:
    """Formats extracted sections into a single labeled block for the AI prompt."""
    titles = {
        "business": "ITEM 1 - BUSINESS",
        "risk_factors": "ITEM 1A - RISK FACTORS",
        "mdna": "MANAGEMENT'S DISCUSSION AND ANALYSIS",
    }
    parts = []
    for key, title in titles.items():
        if key in sections and sections[key]:
            parts.append(f"=== {title} ===\n{sections[key]}")
    return "\n\n".join(parts)
