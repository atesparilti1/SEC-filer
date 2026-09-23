"""Computes financial metrics from SEC XBRL company-facts data.

All arithmetic (growth rates, margins) happens here in plain Python — the AI
model never calculates or is trusted with numeric financial data.
"""

from __future__ import annotations

from datetime import date
from typing import Any

from app.schemas import FinancialPeriod
from app.services.exceptions import FinancialDataUnavailableError

# Each metric may be reported under different XBRL tags depending on the
# filer/year; we try each candidate in order and use the first with data.
METRIC_TAGS: dict[str, list[str]] = {
    "revenue": [
        "RevenueFromContractWithCustomerExcludingAssessedTax",
        "Revenues",
        "SalesRevenueNet",
        "RevenueFromContractWithCustomerIncludingAssessedTax",
    ],
    "net_income": ["NetIncomeLoss", "ProfitLoss"],
    "operating_income": ["OperatingIncomeLoss"],
    "total_assets": ["Assets"],
    "total_liabilities": ["Liabilities"],
    "cash_and_equivalents": [
        "CashAndCashEquivalentsAtCarryingValue",
        "CashAndCashEquivalentsAtCarryingValueIncludingDiscontinuedOperations",
        "CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents",
    ],
    "operating_cash_flow": ["NetCashProvidedByUsedInOperatingActivities"],
}

DURATION_METRICS = {"revenue", "net_income", "operating_income", "operating_cash_flow"}
INSTANT_METRICS = {"total_assets", "total_liabilities", "cash_and_equivalents"}

MIN_ANNUAL_DAYS = 340
MAX_ANNUAL_DAYS = 385


def _annual_points_for_tag(usgaap: dict[str, Any], tag: str, is_duration: bool) -> dict[str, dict[str, Any]]:
    """Returns the best (latest-filed) 10-K data point for each period end date."""
    concept = usgaap.get(tag)
    if not concept:
        return {}

    units = concept.get("units", {}).get("USD", [])
    points: dict[str, dict[str, Any]] = {}

    for item in units:
        if item.get("form") != "10-K":
            continue

        if is_duration:
            start = item.get("start")
            end = item.get("end")
            if not start or not end:
                continue
            days = (date.fromisoformat(end) - date.fromisoformat(start)).days
            if not (MIN_ANNUAL_DAYS <= days <= MAX_ANNUAL_DAYS):
                continue
        else:
            end = item.get("end")
            if not end:
                continue

        existing = points.get(end)
        if existing is None or item.get("filed", "") > existing.get("filed", ""):
            points[end] = item

    return points


def compute_annual_financials(company_facts: dict[str, Any], years: int = 6) -> list[FinancialPeriod]:
    """Builds a chronological list of annual FinancialPeriod records.

    Raises FinancialDataUnavailableError if the filer has no usable
    us-gaap facts at all (e.g. foreign private issuers filing under IFRS).
    """
    usgaap = company_facts.get("facts", {}).get("us-gaap")
    if not usgaap:
        raise FinancialDataUnavailableError("No us-gaap XBRL facts available for this company")

    # Filers switch tags over time (NVIDIA reported revenue under
    # RevenueFromContractWithCustomerExcludingAssessedTax until FY2022, then
    # under Revenues), so merge candidates per period: each period end takes
    # the highest-priority tag that reports it.
    metric_points: dict[str, dict[str, dict[str, Any]]] = {}
    for metric, tags in METRIC_TAGS.items():
        is_duration = metric in DURATION_METRICS
        merged: dict[str, dict[str, Any]] = {}
        for tag in tags:
            for end, point in _annual_points_for_tag(usgaap, tag, is_duration).items():
                merged.setdefault(end, point)
        if merged:
            metric_points[metric] = merged

    if "revenue" not in metric_points and "net_income" not in metric_points:
        raise FinancialDataUnavailableError(
            "Revenue and net income XBRL facts are unavailable for this company"
        )

    all_end_dates: set[str] = set()
    for points in metric_points.values():
        all_end_dates.update(points.keys())
    sorted_ends = sorted(all_end_dates)[-years:]

    periods: list[FinancialPeriod] = []
    for end in sorted_ends:
        values: dict[str, float | None] = {}
        for metric in METRIC_TAGS:
            point = metric_points.get(metric, {}).get(end)
            values[metric] = float(point["val"]) if point else None

        end_date = date.fromisoformat(end)
        periods.append(
            FinancialPeriod(
                fiscal_year=end_date.year,
                fiscal_period="FY",
                end_date=end,
                revenue=values["revenue"],
                net_income=values["net_income"],
                operating_income=values["operating_income"],
                total_assets=values["total_assets"],
                total_liabilities=values["total_liabilities"],
                cash_and_equivalents=values["cash_and_equivalents"],
                operating_cash_flow=values["operating_cash_flow"],
            )
        )

    _apply_derived_metrics(periods)
    return periods


def _apply_derived_metrics(periods: list[FinancialPeriod]) -> None:
    """Fills in YoY growth and margin fields in place, in chronological order."""
    for i, period in enumerate(periods):
        if period.revenue and period.net_income is not None:
            period.net_margin = round(period.net_income / period.revenue, 4)
        if period.revenue and period.operating_income is not None:
            period.operating_margin = round(period.operating_income / period.revenue, 4)

        if i == 0:
            continue
        prior = periods[i - 1]

        if prior.revenue and period.revenue is not None:
            period.revenue_growth_yoy = round((period.revenue - prior.revenue) / abs(prior.revenue), 4)
        if prior.net_income and period.net_income is not None:
            period.net_income_growth_yoy = round(
                (period.net_income - prior.net_income) / abs(prior.net_income), 4
            )


def format_financial_summary(periods: list[FinancialPeriod]) -> str:
    """Renders computed metrics as plain text for inclusion in the AI prompt."""
    if not periods:
        return ""

    lines = []
    for p in periods:
        parts = [f"FY{p.fiscal_year} (ended {p.end_date}):"]
        if p.revenue is not None:
            parts.append(f"Revenue=${p.revenue:,.0f}")
        if p.revenue_growth_yoy is not None:
            parts.append(f"RevenueGrowthYoY={p.revenue_growth_yoy:.1%}")
        if p.net_income is not None:
            parts.append(f"NetIncome=${p.net_income:,.0f}")
        if p.net_margin is not None:
            parts.append(f"NetMargin={p.net_margin:.1%}")
        if p.operating_margin is not None:
            parts.append(f"OperatingMargin={p.operating_margin:.1%}")
        lines.append(" ".join(parts))
    return "\n".join(lines)
