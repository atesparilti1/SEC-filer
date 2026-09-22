import type { FilingSummary } from "../api/types";
import { formatDate } from "../utils/format";

interface FilingSelectorProps {
  filings: FilingSummary[];
  selected: string | null;
  onSelect: (accessionNumber: string) => void;
}

export function FilingSelector({ filings, selected, onSelect }: FilingSelectorProps) {
  return (
    <div className="overflow-hidden rounded-xl border border-border">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-border bg-surface-raised text-left text-xs tracking-wide text-text-secondary uppercase">
            <th className="px-4 py-3 font-medium">Type</th>
            <th className="px-4 py-3 font-medium">Filed</th>
            <th className="px-4 py-3 font-medium">Period</th>
            <th className="px-4 py-3 font-medium">Accession Number</th>
            <th className="px-4 py-3" />
          </tr>
        </thead>
        <tbody>
          {filings.map((filing) => {
            const isSelected = filing.accession_number === selected;
            return (
              <tr
                key={filing.accession_number}
                onClick={() => onSelect(filing.accession_number)}
                className={`cursor-pointer border-b border-border last:border-0 transition ${
                  isSelected ? "bg-accent-soft" : "hover:bg-surface-raised"
                }`}
              >
                <td className="px-4 py-3 font-semibold text-text-primary">{filing.filing_type}</td>
                <td className="px-4 py-3 text-text-secondary">{formatDate(filing.filing_date)}</td>
                <td className="px-4 py-3 text-text-secondary">{formatDate(filing.report_date)}</td>
                <td className="font-mono-tabular px-4 py-3 text-xs text-text-muted">
                  {filing.accession_number}
                </td>
                <td className="px-4 py-3 text-right">
                  {isSelected && <span className="text-xs font-medium text-accent">Selected</span>}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
