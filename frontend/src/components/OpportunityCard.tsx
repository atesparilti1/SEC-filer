import type { OpportunityItem } from "../api/types";
import { Card } from "./Card";

export function OpportunityCard({ opportunity }: { opportunity: OpportunityItem }) {
  return (
    <Card className="space-y-3 border-l-2 border-l-positive/50">
      <h3 className="font-semibold text-text-primary">{opportunity.title}</h3>
      <p className="text-sm text-text-secondary">{opportunity.description}</p>
      {opportunity.evidence && (
        <p className="border-l-2 border-border-strong pl-3 text-xs text-text-muted italic">
          “{opportunity.evidence}”
        </p>
      )}
    </Card>
  );
}
