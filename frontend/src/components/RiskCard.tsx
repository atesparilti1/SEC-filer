import type { RiskItem } from "../api/types";
import { Card } from "./Card";
import { SeverityBadge } from "./SeverityBadge";

export function RiskCard({ risk }: { risk: RiskItem }) {
  return (
    <Card className="space-y-3">
      <div className="flex items-start justify-between gap-3">
        <h3 className="font-semibold text-text-primary">{risk.title}</h3>
        <SeverityBadge severity={risk.severity} />
      </div>
      <p className="text-sm text-text-secondary">{risk.description}</p>
      {risk.evidence && (
        <p className="border-l-2 border-border-strong pl-3 text-xs text-text-muted italic">
          “{risk.evidence}”
        </p>
      )}
    </Card>
  );
}
