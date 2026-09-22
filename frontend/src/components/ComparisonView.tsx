import type { FilingComparison, RiskDelta } from "../api/types";
import { BulletListSection } from "./BulletListSection";
import { Card } from "./Card";
import { Section } from "./Section";
import { SeverityBadge } from "./SeverityBadge";

function RiskDeltaCard({ risk, accentClass }: { risk: RiskDelta; accentClass: string }) {
  return (
    <Card className={`space-y-2 border-l-2 ${accentClass}`}>
      <div className="flex items-start justify-between gap-3">
        <h3 className="font-semibold text-text-primary">{risk.title}</h3>
        {risk.severity && <SeverityBadge severity={risk.severity} />}
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

function RiskDeltaGroup({
  title,
  risks,
  emptyMessage,
  accentClass,
}: {
  title: string;
  risks: RiskDelta[];
  emptyMessage: string;
  accentClass: string;
}) {
  return (
    <Section title={title}>
      {risks.length === 0 ? (
        <BulletListSection items={[]} emptyMessage={emptyMessage} />
      ) : (
        <div className="grid gap-4 md:grid-cols-2">
          {risks.map((risk, i) => (
            <RiskDeltaCard key={i} risk={risk} accentClass={accentClass} />
          ))}
        </div>
      )}
    </Section>
  );
}

export function ComparisonView({ comparison }: { comparison: FilingComparison }) {
  return (
    <div className="space-y-10">
      <Section title="Comparison Summary">
        <Card>
          <p className="text-sm leading-relaxed text-text-secondary">{comparison.summary}</p>
        </Card>
      </Section>

      <RiskDeltaGroup
        title="New Risks"
        risks={comparison.new_risks}
        emptyMessage="No new risks were introduced."
        accentClass="border-l-severity-high/50"
      />

      <RiskDeltaGroup
        title="Escalated Risks"
        risks={comparison.escalated_risks}
        emptyMessage="No risks became more severe."
        accentClass="border-l-severity-medium/50"
      />

      <RiskDeltaGroup
        title="Removed Risks"
        risks={comparison.removed_risks}
        emptyMessage="No risks were removed."
        accentClass="border-l-positive/50"
      />

      <Section title="Management Priority Changes">
        <BulletListSection
          items={comparison.management_priority_changes}
          emptyMessage="No notable changes in management priorities."
        />
      </Section>

      <Section title="Growth Strategy Changes">
        <BulletListSection
          items={comparison.growth_strategy_changes}
          emptyMessage="No notable changes in growth strategy."
        />
      </Section>

      <Section title="Significant Financial Changes">
        <BulletListSection
          items={comparison.financial_changes}
          emptyMessage="No significant financial changes were identified."
        />
      </Section>
    </div>
  );
}
