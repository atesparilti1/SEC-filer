import type { Severity } from "../api/types";

const STYLES: Record<Severity, string> = {
  High: "text-severity-high bg-severity-high-soft border-severity-high/40",
  Medium: "text-severity-medium bg-severity-medium-soft border-severity-medium/40",
  Low: "text-severity-low bg-severity-low-soft border-severity-low/40",
};

export function SeverityBadge({ severity }: { severity: Severity }) {
  return (
    <span
      className={`inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold tracking-wide uppercase ${STYLES[severity]}`}
    >
      {severity}
    </span>
  );
}
