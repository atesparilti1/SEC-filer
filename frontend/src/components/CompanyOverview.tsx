import type { AnalysisRecord } from "../api/types";
import { formatDate } from "../utils/format";
import { Card } from "./Card";

export function CompanyOverview({ record }: { record: AnalysisRecord }) {
  const fields = [
    { label: "Ticker", value: record.ticker },
    { label: "Company", value: record.company_name },
    { label: "CIK", value: record.cik },
    { label: "Filing Type", value: record.filing_type },
    { label: "Filing Date", value: formatDate(record.filing_date) },
  ];

  return (
    <Card>
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div className="flex flex-wrap gap-x-8 gap-y-3">
          {fields.map((f) => (
            <div key={f.label}>
              <p className="text-xs tracking-wide text-text-muted uppercase">{f.label}</p>
              <p className="mt-0.5 font-medium text-text-primary">{f.value}</p>
            </div>
          ))}
        </div>
        {record.is_demo ? (
          <span className="rounded-full border border-accent/40 bg-accent-soft px-3 py-1 text-xs font-medium text-accent">
            Demo data — pre-generated
          </span>
        ) : (
          record.cached && (
            <span className="rounded-full border border-border-strong px-3 py-1 text-xs text-text-muted">
              Cached analysis
            </span>
          )
        )}
      </div>
    </Card>
  );
}
