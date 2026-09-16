import { AccuracyChart } from "@/components/AccuracyChart";
import { Card } from "@/components/ui/Card";
import { DataTable } from "@/components/ui/DataTable";
import { PageHeader } from "@/components/ui/PageHeader";
import { StatTile } from "@/components/ui/StatTile";
import { getBacktestMetrics, getModelInfo } from "@/lib/api";

export const dynamic = "force-dynamic";

export default async function ModelPerformancePage() {
  const [metrics, modelInfo] = await Promise.all([
    getBacktestMetrics(),
    getModelInfo(),
  ]);

  const overallAccuracy =
    metrics.reduce((sum, m) => sum + m.accuracy * m.games, 0) /
    metrics.reduce((sum, m) => sum + m.games, 0);

  const overallBaseline =
    metrics.reduce((sum, m) => sum + m.baseline_accuracy * m.games, 0) /
    metrics.reduce((sum, m) => sum + m.games, 0);

  const totalGames = metrics.reduce((sum, m) => sum + m.games, 0);

  return (
    <div className="mx-auto max-w-6xl px-6 py-12">
      <PageHeader
        eyebrow="Walk-forward backtest"
        title="Model Performance"
        description="Out-of-sample accuracy from a season-by-season walk-forward backtest: each season is predicted using only data available before it, never data from that season or later."
      />

      <div className="grid grid-cols-2 gap-4 sm:grid-cols-4 mb-10">
        <StatTile
          label="Overall accuracy"
          value={`${(overallAccuracy * 100).toFixed(1)}%`}
          sublabel={`vs. ${(overallBaseline * 100).toFixed(1)}% baseline`}
        />
        <StatTile
          label="Games backtested"
          value={totalGames.toLocaleString()}
          sublabel={`${metrics.length} seasons`}
        />
        <StatTile
          label="Model version"
          value={modelInfo.model_version}
          sublabel={new Date(modelInfo.training_date).toLocaleDateString()}
        />
        <StatTile
          label="Features"
          value={String(modelInfo.feature_cols.length)}
          sublabel="rolling-5 EPA diffs"
        />
      </div>

      <Card className="mb-10">
        <h2 className="text-sm font-medium mb-4">
          Accuracy vs. always-predict-home baseline, by season
        </h2>
        <AccuracyChart metrics={metrics} />
      </Card>

      <div className="mb-4">
        <h2 className="text-sm font-medium">Backtest metrics by season</h2>
      </div>

      <DataTable
        rowKey={(row) => row.test_season}
        rows={metrics}
        columns={[
          { header: "Season", render: (r) => r.test_season },
          { header: "Games", render: (r) => r.games, align: "right" },
          {
            header: "Accuracy",
            render: (r) => `${(r.accuracy * 100).toFixed(1)}%`,
            align: "right",
          },
          {
            header: "Baseline",
            render: (r) => `${(r.baseline_accuracy * 100).toFixed(1)}%`,
            align: "right",
          },
          {
            header: "Log loss",
            render: (r) => r.log_loss.toFixed(3),
            align: "right",
          },
          { header: "Brier", render: (r) => r.brier.toFixed(3), align: "right" },
          {
            header: "ROC AUC",
            render: (r) => r.roc_auc.toFixed(3),
            align: "right",
          },
        ]}
      />

      <div className="mt-8 flex flex-wrap gap-2">
        {modelInfo.feature_cols.map((f) => (
          <span
            key={f}
            className="rounded-full border border-border px-3 py-1 text-xs font-mono text-muted"
          >
            {f}
          </span>
        ))}
      </div>
    </div>
  );
}
