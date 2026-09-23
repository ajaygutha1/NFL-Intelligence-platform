import Link from "next/link";

import { Card } from "@/components/ui/Card";

const FEATURES = [
  {
    href: "/model-performance",
    title: "Model Performance",
    description:
      "Walk-forward backtest accuracy, log loss, Brier score, and ROC AUC by season.",
    enabled: true,
  },
  {
    href: "/predictions",
    title: "Weekly predictions",
    description: "Live win probabilities for the upcoming week's matchups.",
    enabled: false,
  },
  {
    href: "/history",
    title: "Prediction History",
    description: "Every backtested game, filterable by season and confidence.",
    enabled: false,
  },
  {
    href: "/insights",
    title: "Model Insights",
    description: "Feature coefficients and permutation importance.",
    enabled: false,
  },
];

export default function Home() {
  return (
    <div className="mx-auto max-w-6xl px-6 py-16">
      <div className="max-w-2xl">
        <div className="text-xs font-medium uppercase tracking-widest text-muted mb-4">
          NFL win probability model
        </div>
        <h1 className="text-4xl sm:text-5xl font-semibold tracking-tight leading-[1.1]">
          A leak-free NFL prediction pipeline, end to end.
        </h1>
        <p className="mt-5 text-base text-muted leading-relaxed">
          Play-by-play EPA features, walk-forward validated logistic regression,
          and a live prediction platform &mdash; built from raw NFL data to a
          served API and this dashboard.
        </p>
      </div>

      <div className="mt-14 grid gap-4 sm:grid-cols-2">
        {FEATURES.map((feature) =>
          feature.enabled ? (
            <Link key={feature.href} href={feature.href}>
              <Card className="h-full transition-colors hover:border-foreground">
                <h2 className="text-base font-medium">{feature.title}</h2>
                <p className="mt-2 text-sm text-muted">{feature.description}</p>
              </Card>
            </Link>
          ) : (
            <Card key={feature.href} className="h-full opacity-50">
              <div className="flex items-center justify-between">
                <h2 className="text-base font-medium">{feature.title}</h2>
                <span className="text-[10px] uppercase tracking-widest text-muted border border-border rounded-full px-2 py-0.5">
                  Coming soon
                </span>
              </div>
              <p className="mt-2 text-sm text-muted">{feature.description}</p>
            </Card>
          ),
        )}
      </div>
    </div>
  );
}
