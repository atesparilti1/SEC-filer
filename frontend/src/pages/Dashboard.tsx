import { useState } from "react";
import { api, ApiError } from "../api/client";
import type { AnalysisRecord, CompanyFilingsResponse } from "../api/types";
import { BulletListSection } from "../components/BulletListSection";
import { Card } from "../components/Card";
import { CompanyOverview } from "../components/CompanyOverview";
import { ErrorBanner } from "../components/ErrorBanner";
import { FilingSelector } from "../components/FilingSelector";
import { FinancialInsightCard } from "../components/FinancialInsightCard";
import { LoadingSpinner } from "../components/LoadingSpinner";
import { MetricCard } from "../components/MetricCard";
import { OpportunityCard } from "../components/OpportunityCard";
import { RiskCard } from "../components/RiskCard";
import { SearchBar } from "../components/SearchBar";
import { Section } from "../components/Section";
import { FinancialBarChart } from "../components/charts/FinancialBarChart";
import { formatCurrency, formatPercent } from "../utils/format";

type Stage = "idle" | "loading-filings" | "filings-ready" | "loading-analysis" | "analyzed";

export function Dashboard() {
  const [stage, setStage] = useState<Stage>("idle");
  const [filingsData, setFilingsData] = useState<CompanyFilingsResponse | null>(null);
  const [selectedAccession, setSelectedAccession] = useState<string | null>(null);
  const [analysis, setAnalysis] = useState<AnalysisRecord | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function handleSearch(ticker: string) {
    setError(null);
    setAnalysis(null);
    setSelectedAccession(null);
    setStage("loading-filings");
    try {
      const data = await api.getFilings(ticker);
      setFilingsData(data);
      setStage("filings-ready");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Something went wrong loading filings.");
      setStage("idle");
    }
  }

  async function handleAnalyze() {
    if (!filingsData || !selectedAccession) return;
    const filing = filingsData.filings.find((f) => f.accession_number === selectedAccession);
    setError(null);
    setStage("loading-analysis");
    try {
      const result = await api.analyze(
        filingsData.company.ticker,
        selectedAccession,
        filing?.filing_type,
      );
      setAnalysis(result);
      setStage("analyzed");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Something went wrong analyzing this filing.");
      setStage("filings-ready");
    }
  }

  const latestPeriod = analysis?.financials?.periods.at(-1) ?? null;

  return (
    <div className="mx-auto max-w-6xl space-y-10 px-6 py-8">
      <p className="text-sm text-text-secondary">
        <span className="font-medium text-text-primary">AAPL, NVDA, AMD, MSFT, and META</span> ship with
        pre-generated demo analyses — pick one below for an instant result. Any other filing runs live
        through the configured AI provider (a free local model via Ollama by default).
      </p>

      <Card>
        <SearchBar onSearch={handleSearch} loading={stage === "loading-filings"} />
      </Card>

      {error && <ErrorBanner message={error} />}

      {stage === "loading-filings" && <LoadingSpinner label="Looking up filings on SEC EDGAR" />}

      {filingsData && (stage === "filings-ready" || stage === "loading-analysis") && (
        <Section
          title={`${filingsData.company.company_name} (${filingsData.company.ticker})`}
          subtitle="Select a 10-K or 10-Q filing to analyze"
        >
          <FilingSelector
            filings={filingsData.filings}
            selected={selectedAccession}
            onSelect={setSelectedAccession}
          />
          <button
            onClick={handleAnalyze}
            disabled={!selectedAccession || stage === "loading-analysis"}
            className="rounded-lg bg-accent px-5 py-2.5 text-sm font-semibold text-canvas transition hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {stage === "loading-analysis" ? "Analyzing filing…" : "Analyze Filing"}
          </button>
        </Section>
      )}

      {stage === "loading-analysis" && (
        <LoadingSpinner label="Reading the filing and generating AI analysis — this can take up to a minute" />
      )}

      {analysis && stage === "analyzed" && (
        <div className="space-y-10">
          <CompanyOverview record={analysis} />

          <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
            <MetricCard label="Revenue" value={formatCurrency(latestPeriod?.revenue)} />
            <MetricCard label="Net Income" value={formatCurrency(latestPeriod?.net_income)} />
            <MetricCard
              label="Revenue Growth"
              value={formatPercent(latestPeriod?.revenue_growth_yoy)}
              deltaTone={
                (latestPeriod?.revenue_growth_yoy ?? 0) >= 0 ? "positive" : "negative"
              }
            />
            <MetricCard label="Net Margin" value={formatPercent(latestPeriod?.net_margin)} />
          </div>

          <Section title="Executive Summary">
            <Card>
              <p className="text-sm leading-relaxed text-text-secondary">
                {analysis.analysis.executive_summary}
              </p>
            </Card>
          </Section>

          <Section title="Key Risks">
            {analysis.analysis.key_risks.length === 0 ? (
              <BulletListSection items={[]} emptyMessage="No material risks were identified." />
            ) : (
              <div className="grid gap-4 md:grid-cols-2">
                {analysis.analysis.key_risks.map((risk, i) => (
                  <RiskCard key={i} risk={risk} />
                ))}
              </div>
            )}
          </Section>

          <Section title="Growth Opportunities">
            {analysis.analysis.growth_opportunities.length === 0 ? (
              <BulletListSection items={[]} emptyMessage="No growth opportunities were identified." />
            ) : (
              <div className="grid gap-4 md:grid-cols-2">
                {analysis.analysis.growth_opportunities.map((opp, i) => (
                  <OpportunityCard key={i} opportunity={opp} />
                ))}
              </div>
            )}
          </Section>

          <Section title="Financial Insights">
            {analysis.analysis.financial_insights.length === 0 ? (
              <BulletListSection items={[]} emptyMessage="No financial insights were identified." />
            ) : (
              <div className="grid gap-4 md:grid-cols-2">
                {analysis.analysis.financial_insights.map((insight, i) => (
                  <FinancialInsightCard key={i} insight={insight} />
                ))}
              </div>
            )}
          </Section>

          <Section title="Management Priorities">
            <BulletListSection
              items={analysis.analysis.management_priorities}
              emptyMessage="No management priorities were identified."
            />
          </Section>

          <Section title="Red Flags">
            <BulletListSection
              items={analysis.analysis.red_flags}
              emptyMessage="No red flags were identified."
              tone="negative"
            />
          </Section>

          <Section title="Positive Signals">
            <BulletListSection
              items={analysis.analysis.positive_signals}
              emptyMessage="No positive signals were identified."
              tone="positive"
            />
          </Section>

          {analysis.financials && analysis.financials.periods.length > 0 && (
            <Section title="Financial Performance">
              <div className="grid gap-4 md:grid-cols-2">
                <FinancialBarChart
                  title="Revenue"
                  periods={analysis.financials.periods}
                  dataKey="revenue"
                  color="var(--color-accent)"
                />
                <FinancialBarChart
                  title="Net Income"
                  periods={analysis.financials.periods}
                  dataKey="net_income"
                  color="var(--color-positive)"
                />
              </div>
            </Section>
          )}
        </div>
      )}
    </div>
  );
}
