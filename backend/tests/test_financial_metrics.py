import pytest

from app.services.exceptions import FinancialDataUnavailableError
from app.services.financial_metrics import compute_annual_financials, format_financial_summary


def _annual_fact(tag_values):
    return {
        "units": {
            "USD": [
                {
                    "start": start,
                    "end": end,
                    "val": val,
                    "form": "10-K",
                    "filed": filed,
                }
                for start, end, val, filed in tag_values
            ]
        }
    }


@pytest.fixture
def company_facts():
    return {
        "facts": {
            "us-gaap": {
                "RevenueFromContractWithCustomerExcludingAssessedTax": _annual_fact(
                    [
                        ("2022-01-01", "2023-01-01", 100_000_000, "2023-02-01"),
                        ("2023-01-02", "2024-01-01", 120_000_000, "2024-02-01"),
                    ]
                ),
                "NetIncomeLoss": _annual_fact(
                    [
                        ("2022-01-01", "2023-01-01", 10_000_000, "2023-02-01"),
                        ("2023-01-02", "2024-01-01", 15_000_000, "2024-02-01"),
                    ]
                ),
                "OperatingIncomeLoss": _annual_fact(
                    [
                        ("2022-01-01", "2023-01-01", 20_000_000, "2023-02-01"),
                        ("2023-01-02", "2024-01-01", 24_000_000, "2024-02-01"),
                    ]
                ),
            }
        }
    }


def test_computes_growth_and_margins(company_facts):
    periods = compute_annual_financials(company_facts)

    assert [p.fiscal_year for p in periods] == [2023, 2024]

    first, second = periods
    assert first.revenue_growth_yoy is None  # no prior period to compare
    assert second.revenue_growth_yoy == pytest.approx(0.2)
    assert second.net_income_growth_yoy == pytest.approx(0.5)
    assert second.net_margin == pytest.approx(15_000_000 / 120_000_000)
    assert second.operating_margin == pytest.approx(24_000_000 / 120_000_000)


def test_deduplicates_restated_values_using_most_recently_filed():
    facts = {
        "facts": {
            "us-gaap": {
                "Revenues": {
                    "units": {
                        "USD": [
                            {
                                "start": "2022-01-01",
                                "end": "2023-01-01",
                                "val": 90_000_000,
                                "form": "10-K",
                                "filed": "2023-02-01",
                            },
                            {
                                # Restated in a later filing - should win.
                                "start": "2022-01-01",
                                "end": "2023-01-01",
                                "val": 95_000_000,
                                "form": "10-K",
                                "filed": "2024-02-01",
                            },
                        ]
                    }
                },
                "NetIncomeLoss": {"units": {"USD": []}},
            }
        }
    }

    periods = compute_annual_financials(facts)

    assert periods[0].revenue == 95_000_000


def test_merges_periods_across_tags_when_filer_switches_tag():
    # NVIDIA-style history: older years under one tag, recent years under another.
    facts = {
        "facts": {
            "us-gaap": {
                "RevenueFromContractWithCustomerExcludingAssessedTax": _annual_fact(
                    [
                        ("2021-01-01", "2022-01-01", 100_000_000, "2022-02-01"),
                        ("2022-01-02", "2023-01-01", 110_000_000, "2023-02-01"),
                    ]
                ),
                "Revenues": _annual_fact(
                    [
                        # Overlapping year: the higher-priority tag above should win.
                        ("2022-01-02", "2023-01-01", 999_000_000, "2023-02-01"),
                        ("2023-01-02", "2024-01-01", 150_000_000, "2024-02-01"),
                    ]
                ),
                "NetIncomeLoss": {"units": {"USD": []}},
            }
        }
    }

    periods = compute_annual_financials(facts)

    assert [p.revenue for p in periods] == [100_000_000, 110_000_000, 150_000_000]
    assert periods[-1].revenue_growth_yoy == pytest.approx(round(40_000_000 / 110_000_000, 4))


def test_raises_when_no_usable_facts():
    with pytest.raises(FinancialDataUnavailableError):
        compute_annual_financials({"facts": {"us-gaap": {}}})


def test_format_financial_summary_includes_key_figures(company_facts):
    periods = compute_annual_financials(company_facts)

    summary = format_financial_summary(periods)

    assert "FY2024" in summary
    assert "Revenue=$120,000,000" in summary
    assert "RevenueGrowthYoY=20.0%" in summary
