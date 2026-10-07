"use client";

import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import type { ModelInsight } from "@/lib/api";
import { featureLabel } from "@/lib/features";

type Metric = "coefficient" | "permutation_importance";

export function ImportanceChart({
  insights,
  metric,
  digits,
}: {
  insights: ModelInsight[];
  metric: Metric;
  digits: number;
}) {
  const data = [...insights]
    .sort((a, b) => Math.abs(b[metric]) - Math.abs(a[metric]))
    .map((i) => ({
      feature: featureLabel(i.feature),
      value: Number(i[metric].toFixed(digits)),
    }));

  return (
    <ResponsiveContainer width="100%" height={300}>
      <BarChart data={data} layout="vertical" margin={{ left: 24 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" horizontal={false} />
        <XAxis
          type="number"
          tick={{ fill: "var(--muted)", fontSize: 12 }}
          axisLine={{ stroke: "var(--border)" }}
          tickLine={false}
        />
        <YAxis
          type="category"
          dataKey="feature"
          width={120}
          tick={{ fill: "var(--muted)", fontSize: 12 }}
          axisLine={{ stroke: "var(--border)" }}
          tickLine={false}
        />
        <Tooltip
          cursor={{ fill: "var(--surface)" }}
          contentStyle={{
            background: "var(--background)",
            border: "1px solid var(--border)",
            borderRadius: 8,
            fontSize: 12,
          }}
        />
        <Bar dataKey="value" radius={[0, 4, 4, 0]} isAnimationActive={false}>
          {data.map((d) => (
            <Cell
              key={d.feature}
              fill={d.value >= 0 ? "var(--foreground)" : "var(--gray-400)"}
            />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}
