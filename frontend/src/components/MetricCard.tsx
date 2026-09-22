import { Card } from "./Card";

interface MetricCardProps {
  label: string;
  value: string;
  delta?: string | null;
  deltaTone?: "positive" | "negative" | "neutral";
}

export function MetricCard({ label, value, delta, deltaTone = "neutral" }: MetricCardProps) {
  const deltaColor =
    deltaTone === "positive"
      ? "text-positive"
      : deltaTone === "negative"
        ? "text-negative"
        : "text-text-secondary";

  return (
    <Card>
      <p className="text-xs font-medium tracking-wide text-text-secondary uppercase">{label}</p>
      <p className="mt-2 font-mono-tabular text-2xl font-semibold text-text-primary">{value}</p>
      {delta && <p className={`mt-1 text-sm font-medium ${deltaColor}`}>{delta}</p>}
    </Card>
  );
}
