import { Card } from "@/components/ui/Card";
import type { ModelInsight } from "@/lib/api";
import {
  CAVEATS,
  GLOSSARY,
  buildTakeaways,
} from "@/lib/insights-narrative";

export function AiInsights({ insights }: { insights: ModelInsight[] }) {
  const takeaways = buildTakeaways(insights);

  return (
    <section className="mb-10" aria-labelledby="ai-insights-heading">
      <div className="mb-4 flex flex-wrap items-baseline justify-between gap-2">
        <h2 id="ai-insights-heading" className="text-lg font-semibold tracking-tight">
          AI Insights
        </h2>
        <span className="text-xs text-muted">
          Explanations written by Claude. Takeaways are computed from this
          model&apos;s numbers and update when it is retrained.
        </span>
      </div>

      <div className="grid gap-4 md:grid-cols-3">
        {takeaways.map((t, i) => (
          <Card key={t.title}>
            <div className="text-xs font-mono text-muted">0{i + 1}</div>
            <h3 className="mt-2 text-sm font-medium leading-snug">{t.title}</h3>
            <p className="mt-2 text-sm text-muted leading-relaxed">{t.body}</p>
          </Card>
        ))}
      </div>

      <div className="mt-4 grid gap-4 lg:grid-cols-2">
        <Card>
          <h3 className="text-sm font-medium">How to read this page</h3>
          <dl className="mt-4 space-y-4">
            {GLOSSARY.map((g) => (
              <div key={g.term}>
                <dt className="text-sm font-medium">{g.term}</dt>
                <dd className="mt-1 text-sm text-muted leading-relaxed">
                  {g.definition}
                </dd>
              </div>
            ))}
          </dl>
        </Card>
        <Card>
          <h3 className="text-sm font-medium">What this does not tell you</h3>
          <ul className="mt-4 space-y-3 text-sm text-muted leading-relaxed list-disc pl-5">
            {CAVEATS.map((c) => (
              <li key={c}>{c}</li>
            ))}
          </ul>
        </Card>
      </div>
    </section>
  );
}
