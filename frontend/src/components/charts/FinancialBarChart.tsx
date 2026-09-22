import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { FinancialPeriod } from "../../api/types";
import { formatCurrency } from "../../utils/format";
import { Card } from "../Card";

interface FinancialBarChartProps {
  title: string;
  periods: FinancialPeriod[];
  dataKey: "revenue" | "net_income";
  color: string;
}

interface TooltipPayload {
  payload: { fiscal_year: number; value: number | null };
}

function ChartTooltip({ active, payload }: { active?: boolean; payload?: TooltipPayload[] }) {
  if (!active || !payload?.length) return null;
  const point = payload[0].payload;
  return (
    <div className="rounded-lg border border-border-strong bg-surface-raised px-3 py-2 text-xs shadow-lg">
      <p className="font-medium text-text-secondary">FY{point.fiscal_year}</p>
      <p className="font-mono-tabular mt-0.5 text-sm font-semibold text-text-primary">
        {formatCurrency(point.value)}
      </p>
    </div>
  );
}

export function FinancialBarChart({ title, periods, dataKey, color }: FinancialBarChartProps) {
  const data = periods.map((p) => ({
    fiscal_year: p.fiscal_year,
    value: p[dataKey],
  }));

  return (
    <Card>
      <p className="mb-4 text-xs font-semibold tracking-wide text-text-secondary uppercase">
        {title}
      </p>
      <ResponsiveContainer width="100%" height={240}>
        <BarChart data={data} margin={{ top: 4, right: 8, left: 8, bottom: 0 }}>
          <CartesianGrid stroke="var(--color-border)" vertical={false} />
          <XAxis
            dataKey="fiscal_year"
            tickFormatter={(v) => `FY${v}`}
            tick={{ fill: "var(--color-text-muted)", fontSize: 12 }}
            axisLine={{ stroke: "var(--color-border)" }}
            tickLine={false}
          />
          <YAxis
            tickFormatter={(v) => formatCurrency(v)}
            tick={{ fill: "var(--color-text-muted)", fontSize: 12 }}
            axisLine={false}
            tickLine={false}
            width={64}
          />
          <Tooltip content={<ChartTooltip />} cursor={{ fill: "var(--color-border)" }} />
          <Bar dataKey="value" fill={color} radius={[4, 4, 0, 0]} maxBarSize={48} />
        </BarChart>
      </ResponsiveContainer>
    </Card>
  );
}
