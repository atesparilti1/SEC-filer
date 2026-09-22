export type Severity = "High" | "Medium" | "Low";

export interface CompanyInfo {
  ticker: string;
  cik: string;
  company_name: string;
  sic_description: string;
}

export interface FilingSummary {
  accession_number: string;
  filing_type: string;
  filing_date: string;
  report_date: string;
  primary_document: string;
  primary_doc_url: string;
}

export interface CompanyFilingsResponse {
  company: CompanyInfo;
  filings: FilingSummary[];
}

export interface FinancialPeriod {
  fiscal_year: number;
  fiscal_period: string;
  end_date: string;
  revenue: number | null;
  net_income: number | null;
  operating_income: number | null;
  total_assets: number | null;
  total_liabilities: number | null;
  cash_and_equivalents: number | null;
  operating_cash_flow: number | null;
  revenue_growth_yoy: number | null;
  net_income_growth_yoy: number | null;
  operating_margin: number | null;
  net_margin: number | null;
}

export interface FinancialsResponse {
  ticker: string;
  company_name: string;
  cik: string;
  periods: FinancialPeriod[];
}

export interface RiskItem {
  title: string;
  description: string;
  severity: Severity;
  evidence: string;
}

export interface OpportunityItem {
  title: string;
  description: string;
  evidence: string;
}

export interface FinancialInsightItem {
  metric: string;
  observation: string;
  interpretation: string;
}

export interface FilingAnalysis {
  executive_summary: string;
  key_risks: RiskItem[];
  growth_opportunities: OpportunityItem[];
  financial_insights: FinancialInsightItem[];
  management_priorities: string[];
  red_flags: string[];
  positive_signals: string[];
}

export interface AnalysisRecord {
  id: number;
  ticker: string;
  company_name: string;
  cik: string;
  accession_number: string;
  filing_type: string;
  filing_date: string;
  report_date: string;
  analysis: FilingAnalysis;
  financials: FinancialsResponse | null;
  cached: boolean;
  is_demo: boolean;
}

export interface RiskDelta {
  title: string;
  description: string;
  severity: Severity | null;
  evidence: string;
}

export interface FilingComparison {
  new_risks: RiskDelta[];
  removed_risks: RiskDelta[];
  escalated_risks: RiskDelta[];
  management_priority_changes: string[];
  growth_strategy_changes: string[];
  financial_changes: string[];
  summary: string;
}

export interface CompareResponse {
  filing_a: AnalysisRecord;
  filing_b: AnalysisRecord;
  comparison: FilingComparison;
}
