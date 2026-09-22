import type { FinancialInsightItem } from "../api/types";
import { Card } from "./Card";

export function FinancialInsightCard({ insight }: { insight: FinancialInsightItem }) {
  return (
    <Card className="space-y-2">
      <p className="text-xs font-semibold tracking-wide text-accent uppercase">{insight.metric}</p>
      <p className="text-sm text-text-primary">{insight.observation}</p>
      <p className="text-sm text-text-secondary">{insight.interpretation}</p>
    </Card>
  );
}
