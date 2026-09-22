from typing import Literal

from pydantic import BaseModel, Field

Severity = Literal["High", "Medium", "Low"]


# ---------------------------------------------------------------------------
# Company / filings
# ---------------------------------------------------------------------------


class CompanyInfo(BaseModel):
    ticker: str
    cik: str
    company_name: str
    sic_description: str = ""


class FilingSummary(BaseModel):
    accession_number: str
    filing_type: str
    filing_date: str
    report_date: str = ""
    primary_document: str = ""
    primary_doc_url: str = ""


class CompanyFilingsResponse(BaseModel):
    company: CompanyInfo
    filings: list[FilingSummary]


# ---------------------------------------------------------------------------
# Financial metrics (computed in Python from SEC XBRL data, never by the AI)
# ---------------------------------------------------------------------------


class FinancialPeriod(BaseModel):
    fiscal_year: int
    fiscal_period: str
    end_date: str
    revenue: float | None = None
    net_income: float | None = None
    operating_income: float | None = None
    total_assets: float | None = None
    total_liabilities: float | None = None
    cash_and_equivalents: float | None = None
    operating_cash_flow: float | None = None
    revenue_growth_yoy: float | None = None
    net_income_growth_yoy: float | None = None
    operating_margin: float | None = None
    net_margin: float | None = None


class FinancialsResponse(BaseModel):
    ticker: str
    company_name: str
    cik: str
    periods: list[FinancialPeriod]


# ---------------------------------------------------------------------------
# AI analysis schema (strict — see app/services/ai_analysis.py for the prompt
# that enforces this shape)
# ---------------------------------------------------------------------------


class RiskItem(BaseModel):
    title: str
    description: str
    severity: Severity
    evidence: str


class OpportunityItem(BaseModel):
    title: str
    description: str
    evidence: str


class FinancialInsightItem(BaseModel):
    metric: str
    observation: str
    interpretation: str


class FilingAnalysis(BaseModel):
    executive_summary: str
    key_risks: list[RiskItem] = Field(default_factory=list)
    growth_opportunities: list[OpportunityItem] = Field(default_factory=list)
    financial_insights: list[FinancialInsightItem] = Field(default_factory=list)
    management_priorities: list[str] = Field(default_factory=list)
    red_flags: list[str] = Field(default_factory=list)
    positive_signals: list[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# API request / response envelopes
# ---------------------------------------------------------------------------


class AnalyzeRequest(BaseModel):
    ticker: str
    accession_number: str
    filing_type: str | None = None


class AnalysisRecord(BaseModel):
    id: int
    ticker: str
    company_name: str
    cik: str
    accession_number: str
    filing_type: str
    filing_date: str
    report_date: str = ""
    analysis: FilingAnalysis
    financials: FinancialsResponse | None = None
    cached: bool = False
    is_demo: bool = False

    model_config = {"from_attributes": True}


class CompareRequest(BaseModel):
    ticker_a: str
    accession_number_a: str
    ticker_b: str
    accession_number_b: str


class RiskDelta(BaseModel):
    title: str
    description: str
    severity: Severity | None = None
    evidence: str = ""


class FilingComparison(BaseModel):
    new_risks: list[RiskDelta] = Field(default_factory=list)
    removed_risks: list[RiskDelta] = Field(default_factory=list)
    escalated_risks: list[RiskDelta] = Field(default_factory=list)
    management_priority_changes: list[str] = Field(default_factory=list)
    growth_strategy_changes: list[str] = Field(default_factory=list)
    financial_changes: list[str] = Field(default_factory=list)
    summary: str = ""


class CompareResponse(BaseModel):
    filing_a: AnalysisRecord
    filing_b: AnalysisRecord
    comparison: FilingComparison


class ErrorResponse(BaseModel):
    detail: str
