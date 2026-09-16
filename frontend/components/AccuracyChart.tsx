"use client";

import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import type { BacktestMetric } from "@/lib/api";

export function AccuracyChart({ metrics }: { metrics: BacktestMetric[] }) {
  const data = metrics.map((m) => ({
    season: String(m.test_season),
    "Model accuracy": Number((m.accuracy * 100).toFixed(1)),
    "Always-home baseline": Number((m.baseline_accuracy * 100).toFixed(1)),
  }));

  return (
    <ResponsiveContainer width="100%" height={320}>
      <BarChart data={data} barGap={6}>
        <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" vertical={false} />
        <XAxis
          dataKey="season"
          tick={{ fill: "var(--muted)", fontSize: 12 }}
          axisLine={{ stroke: "var(--border)" }}
          tickLine={false}
        />
        <YAxis
          unit="%"
          domain={[0, 100]}
          tick={{ fill: "var(--muted)", fontSize: 12 }}
          axisLine={{ stroke: "var(--border)" }}
          tickLine={false}
        />
        <Tooltip
          contentStyle={{
            background: "var(--background)",
            border: "1px solid var(--border)",
            borderRadius: 8,
            fontSize: 12,
          }}
        />
        <Legend wrapperStyle={{ fontSize: 12, color: "var(--muted)" }} />
        <Bar dataKey="Model accuracy" fill="var(--foreground)" radius={[4, 4, 0, 0]} />
        <Bar dataKey="Always-home baseline" fill="var(--gray-300)" radius={[4, 4, 0, 0]} />
      </BarChart>
    </ResponsiveContainer>
  );
}
