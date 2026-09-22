import { Card } from "./Card";
import { EmptyState } from "./EmptyState";

interface BulletListSectionProps {
  items: string[];
  emptyMessage: string;
  tone?: "neutral" | "positive" | "negative";
}

const MARKER_COLOR = {
  neutral: "text-accent",
  positive: "text-positive",
  negative: "text-negative",
};

export function BulletListSection({ items, emptyMessage, tone = "neutral" }: BulletListSectionProps) {
  if (items.length === 0) return <EmptyState message={emptyMessage} />;

  return (
    <Card>
      <ul className="space-y-3">
        {items.map((item, i) => (
          <li key={i} className="flex gap-3 text-sm text-text-secondary">
            <span className={`mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-current ${MARKER_COLOR[tone]}`} />
            <span className="text-text-primary">{item}</span>
          </li>
        ))}
      </ul>
    </Card>
  );
}
